import { test } from 'node:test';
import assert from 'node:assert/strict';
import worker, { commandFrom, eventFrom, GroupBot, zaloCall, JOKES } from './worker.mjs';

const env = { ZALO_CHAT_ID: 'group', BOT_ID: 'bot', ZALO_BOT_TOKEN: 'test-only', WEBHOOK_SECRET: 'test-secret', STICKER_ID: 'sticker' };
function payload(text = '@Bot Portal Checker Bình', id = 'm1') {
  return { ok: true, result: { event_name: 'message.text.received', message: {
    text, message_id: id, from: { id: 'friend', is_bot: false }, chat: { id: 'group', chat_type: 'GROUP' },
  } } };
}
function setup() {
  const values = new Map();
  const ctx = { storage: {
    async get(key) { return structuredClone(values.get(key)); },
    async put(key, value) { values.set(key, structuredClone(value)); },
  } };
  return { ctx, values, bot: new GroupBot(ctx, env) };
}
function req(event) { return new Request('https://internal/handle', { method: 'POST', body: JSON.stringify(event) }); }

test('only explicit bot commands match, including accents/case/aliases', () => {
  for (const text of ['@Bot Portal Checker Bình', '@bot bình', '@bot.iCVlnHsz binh', '/binh']) {
    assert.equal(commandFrom(text), 'binh');
  }
  for (const text of ['Bình ơi học bài', 'Bình', '@Bình test', '@bot Lan', null]) assert.equal(commandFrom(text), null);
  assert.equal(commandFrom('@bot dừng Bình'), 'stop');
  assert.equal(commandFrom('@bot trợ giúp'), 'help');
});

test('ignore other groups, private chats, bot senders and unsupported events', () => {
  assert.equal(eventFrom(payload(), env).command, 'binh');
  for (const modify of [
    p => p.result.message.chat.id = 'other',
    p => p.result.message.chat.chat_type = 'PRIVATE',
    p => p.result.message.from.is_bot = true,
    p => p.result.message.from.id = 'bot',
    p => p.result.event_name = 'message.sticker.received',
    p => delete p.result.message.message_id,
  ]) { const p = payload(); modify(p); assert.equal(eventFrom(p, env), null); }
});

test('webhook rejects bad secret before dispatch', async () => {
  const response = await worker.fetch(new Request('https://bot/webhook', { method: 'POST', body: JSON.stringify(payload()) }), { ...env, GROUP_BOT: {} });
  assert.equal(response.status, 403);
});

test('authenticated verification and unknown commands are acknowledged without sends', async () => {
  for (const data of [{}, payload('just chatting')]) {
    const response = await worker.fetch(new Request('https://bot/webhook', { method: 'POST', headers: { 'X-Bot-Api-Secret-Token': env.WEBHOOK_SECRET }, body: JSON.stringify(data) }), { ...env, GROUP_BOT: {} });
    assert.equal(response.status, 200);
  }
});

test('typing, curated message, then sticker; duplicate events are ignored concurrently', async () => {
  const { bot } = setup();
  const calls = [];
  const original = globalThis.fetch;
  globalThis.fetch = async (url, options) => { calls.push([url.split('/').at(-1), JSON.parse(options.body)]); return Response.json({ ok: true }); };
  try {
    const event = eventFrom(payload(), env);
    await Promise.all([bot.fetch(req(event)), bot.fetch(req(event))]);
    assert.deepEqual(calls.map(c => c[0]), ['sendChatAction', 'sendMessage', 'sendSticker']);
    assert.equal(calls[0][1].action, 'typing');
    assert.ok(JOKES.includes(calls[1][1].text));
  } finally { globalThis.fetch = original; }
});

test('persistent dedup and cooldown survive object restart', async () => {
  const { bot, ctx, values } = setup();
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => { calls++; return Response.json({ ok: true }); };
  try {
    await bot.fetch(req(eventFrom(payload(), env)));
    const restarted = new GroupBot(ctx, env);
    await restarted.fetch(req(eventFrom(payload(), env)));
    await restarted.fetch(req(eventFrom(payload('@bot Bình', 'm2'), env)));
    assert.equal(calls, 3);
    assert.deepEqual(values.get('state').seen, ['m1', 'm2']);
  } finally { globalThis.fetch = original; }
});

test('stop command permanently pauses jokes without an ordinary member restart command', async () => {
  const { bot, values } = setup();
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => { calls++; return Response.json({ ok: true }); };
  try {
    await bot.fetch(req(eventFrom(payload('@bot dừng Bình'), env)));
    const state = values.get('state'); state.lastReply = 0; values.set('state', state);
    await bot.fetch(req(eventFrom(payload('@bot Bình', 'm2'), env)));
    assert.equal(calls, 2); // Typing and stop confirmation only.
    assert.equal(values.get('state').paused, true);
  } finally { globalThis.fetch = original; }
});

test('typing failure does not block text; text failure suppresses sticker', async () => {
  const { bot } = setup();
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async url => { calls.push(url.split('/').at(-1)); return Response.json({ ok: false }); };
  try {
    await bot.fetch(req(eventFrom(payload(), env)));
    assert.deepEqual(calls, ['sendChatAction', 'sendMessage']);
  } finally { globalThis.fetch = original; }
});

test('daily budget caps sends', async () => {
  const { bot, values } = setup();
  values.set('state', { day: new Date().toISOString().slice(0, 10), count: 100, seen: [], lastReply: 0, lastJoke: 0 });
  const original = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error('should not send'); };
  try { await bot.fetch(req(eventFrom(payload(), env))); assert.equal(values.get('state').count, 100); }
  finally { globalThis.fetch = original; }
});

test('network and non-JSON errors become false without logging credentials', async () => {
  assert.equal(await zaloCall(env, 'sendMessage', {}, async () => { throw new Error('token'); }), false);
  assert.equal(await zaloCall(env, 'sendMessage', {}, async () => new Response('bad')), false);
});
