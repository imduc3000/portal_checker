// No AI API: curated replies, restricted to the configured friends' group.
export const JOKES = [
  'Bình đang tiết kiệm năng lượng để bùng nổ vào phút 89 của deadline 😎',
  'Deadline vừa vào nhóm là Bình bật chế độ: đã xem nhưng chưa sẵn sàng 😂',
  'Bình bảo “5 phút nữa làm” — nhóm đang chờ xác định múi giờ của 5 phút đó ⏰',
  'Portal có thông báo mới, còn Bình có thêm lý do để “mai tính” 😌',
  'Bình không trễ deadline, Bình chỉ thích tạo bất ngờ cho cả nhóm 🎬',
  'Nhóm cần người chốt kèo, Bình đang bận mở cuộc họp với chiếc gối 🛌',
  'Bình lên kế hoạch rất kỹ: bước 1 mở laptop, bước 2 nghỉ giải lao ☕',
  'Bình online là nhóm vui; Bình nhận làm bài là nhóm… theo dõi tiến độ 😆',
];

export function normalize(text) {
  return text.normalize('NFD').replace(/\p{M}/gu, '').replace(/đ/g, 'd')
    .replace(/Đ/g, 'D').toLowerCase().replace(/\s+/g, ' ').trim();
}

export function commandFrom(text) {
  if (typeof text !== 'string' || text.length > 500) return null;
  let command = normalize(text);
  const prefix = /^@(?:bot portal checker|bot\.icvlnhsz|bot)\s*[:,]?\s+(.+)$/;
  const match = command.match(prefix);
  if (match) command = match[1];
  else if (command.startsWith('/')) command = command.slice(1);
  else return null; // Never react to ordinary group chatter about Bình.
  if (['binh', 'choc binh'].includes(command)) return 'binh';
  if (['dung binh', 'stop binh'].includes(command)) return 'stop';
  if (['tro giup', 'help', 'ping'].includes(command)) return 'help';
  return null;
}

export function eventFrom(body, env) {
  const event = body?.result;
  const message = event?.message;
  if (body?.ok !== true || event?.event_name !== 'message.text.received') return null;
  if (!message || message.from?.is_bot === true || String(message.from?.id) === env.BOT_ID) return null;
  if (message.chat?.chat_type !== 'GROUP' || String(message.chat.id) !== env.ZALO_CHAT_ID) return null;
  if (typeof message.message_id !== 'string' || !message.message_id) return null;
  const command = commandFrom(message.text);
  return command ? { command, id: message.message_id, chatId: String(message.chat.id) } : null;
}

export async function zaloCall(env, method, payload, fetcher = fetch) {
  try {
    const response = await fetcher(`https://bot-api.zaloplatforms.com/bot${env.ZALO_BOT_TOKEN}/${method}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload), signal: AbortSignal.timeout(7000),
    });
    if (!response.ok) return false;
    return (await response.json()).ok === true;
  } catch { return false; } // Never log token-bearing URLs, request bodies or group messages.
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'GET' && url.pathname === '/health') return Response.json({ ok: true });
    if (url.pathname !== '/webhook') return new Response('Not found', { status: 404 });
    if (request.method !== 'POST') return new Response('POST required', { status: 405 });
    if (!env.WEBHOOK_SECRET || !env.ZALO_BOT_TOKEN || !env.ZALO_CHAT_ID || !env.GROUP_BOT) {
      return new Response('Not configured', { status: 503 });
    }
    if (request.headers.get('X-Bot-Api-Secret-Token') !== env.WEBHOOK_SECRET) {
      return new Response('Forbidden', { status: 403 });
    }
    let body;
    try {
      // Bound the actual stream, not just the caller-controlled Content-Length.
      const reader = request.body?.getReader();
      const buffers = [];
      let bytes = 0;
      if (!reader) return new Response('JSON required', { status: 400 });
      while (true) {
        const part = await reader.read();
        if (part.done) break;
        bytes += part.value.byteLength;
        if (bytes > 32768) { await reader.cancel(); return new Response('Too large', { status: 413 }); }
        buffers.push(part.value);
      }
      body = JSON.parse(await new Blob(buffers).text());
    } catch { return new Response('Invalid JSON', { status: 400 }); }
    const event = eventFrom(body, env);
    // Also ACK authenticated webhook verification probes and unsupported events.
    if (!event) return Response.json({ ok: true });
    try {
      const id = env.GROUP_BOT.idFromName(event.chatId);
      return await env.GROUP_BOT.get(id).fetch('https://group.internal/handle', {
        method: 'POST', body: JSON.stringify(event),
      });
    } catch { return new Response('Temporarily unavailable', { status: 503 }); }
  },
};

// SQLite-backed Durable Object: serialize requests per group and persist cooldown/dedup.
export class GroupBot {
  constructor(ctx, env) {
    this.ctx = ctx;
    this.env = env;
    this.queue = Promise.resolve();
  }

  fetch(request) {
    const work = this.queue.then(() => this.handle(request));
    this.queue = work.catch(() => {});
    return work;
  }

  async handle(request) {
    const event = await request.json();
    const state = await this.ctx.storage.get('state') || {
      seen: [], lastReply: 0, lastJoke: 0, lastIndex: -1, paused: false, day: '', count: 0,
    };
    if (state.seen.includes(event.id)) return Response.json({ ok: true });
    const now = Date.now();
    const day = new Date(now).toISOString().slice(0, 10);
    if (day !== state.day) { state.day = day; state.count = 0; }
    state.seen = [...state.seen, event.id].slice(-128);
    if (event.command === 'stop') state.paused = true;
    const cooled = now - state.lastReply >= 8000;
    const canJoke = !state.paused && now - state.lastJoke >= 30000;
    if (!cooled || state.count >= 100 || (event.command === 'binh' && !canJoke)) {
      await this.ctx.storage.put('state', state);
      return Response.json({ ok: true });
    }
    let text;
    if (event.command === 'binh') {
      // Rotate randomly without repeating the previous joke.
      const offset = 1 + Math.floor(Math.random() * (JOKES.length - 1));
      state.lastIndex = (state.lastIndex + offset) % JOKES.length;
      state.lastJoke = now;
      text = JOKES[state.lastIndex];
    } else if (event.command === 'stop') {
      text = 'Đã tắt chọc Bình trong nhóm. Muốn bật lại, chủ bot đổi cấu hình/reset trạng thái giúp nhé 🤝';
    } else {
      text = 'Có mặt bro 😎\n@Bot Portal Checker Bình → chọc nhẹ một câu + sticker\n@Bot Portal Checker dừng Bình → tắt chọc Bình\nMình nghỉ 30 giây giữa các câu chọc; tối đa 100 lượt/ngày cho nhóm.';
      if (state.paused) text += '\nHiện chế độ chọc Bình đang tắt.';
    }
    state.lastReply = now;
    state.count += 1;
    // Reserve before external sends: webhook retries never produce a joke storm.
    // If Zalo fails, this event is not retried; send a new command after cooldown.
    await this.ctx.storage.put('state', state);
    await zaloCall(this.env, 'sendChatAction', { chat_id: event.chatId, action: 'typing' });
    const sent = await zaloCall(this.env, 'sendMessage', { chat_id: event.chatId, text });
    if (sent && event.command === 'binh' && this.env.STICKER_ID) {
      await zaloCall(this.env, 'sendSticker', { chat_id: event.chatId, sticker: this.env.STICKER_ID });
    }
    return Response.json({ ok: true });
  }
}
