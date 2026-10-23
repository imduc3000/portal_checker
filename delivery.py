"""Independent delivery ledgers; only IDs/hashes are persisted, never message bodies."""
import hashlib
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

STATE = Path('seen_notifications.json')


def load_state():
    # Refuse to silently reset damaged state, which would resend historical news.
    data = json.loads(STATE.read_text()) if STATE.exists() else {'seen_ids': []}
    if not isinstance(data, dict) or not isinstance(data.get('seen_ids', []), list):
        raise ValueError('Invalid state')
    deliveries = data.setdefault('deliveries', {})
    for name in ('telegram', 'zalo'):
        ledger = deliveries.setdefault(name, {
            'sent_ids': list(data.get('seen_ids', [])), 'partial': {},
        })
        if not isinstance(ledger.get('sent_ids'), list) or not isinstance(ledger.get('partial'), dict):
            raise ValueError('Invalid delivery ledger')
    data['version'] = 2
    return data


def save_state(data):
    temporary = STATE.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(STATE)


def split_text(text, limit):
    parts, current, size = [], [], 0
    for char in text:
        width = 2 if ord(char) > 0xFFFF else 1
        if size + width > limit:
            parts.append(''.join(current))
            current, size = [], 0
        current.append(char)
        size += width
    if current:
        parts.append(''.join(current))
    return parts


def send(name, config, text):
    token, chat_id = config
    host = 'https://api.telegram.org' if name == 'telegram' else 'https://bot-api.zaloplatforms.com'
    try:
        response = requests.post(f'{host}/bot{token}/sendMessage',
                                 json={'chat_id': chat_id, 'text': text}, timeout=20)
        response.raise_for_status()
        if response.json().get('ok') is not True:
            return False
        return True
    except (requests.RequestException, ValueError, AttributeError):
        # Never print request exceptions: their URLs can contain bot tokens.
        return False


def deliver(items, state, channels, sender=send, persist=save_state):
    failures = []
    for name, config in channels.items():
        ledger = state['deliveries'][name]
        sent = set(str(key) for key in ledger['sent_ids'])
        count = 0
        for item in items:
            key = str(item['id'])
            if key in sent:
                continue
            text = (f"🔔 Thông báo Portal TDTU\n\n📌 {item['title']}\n"
                    f"📅 {item['date']}\n\n{item['summary']}\n\n🔗 {item['link']}")
            parts = split_text(text, 2000 if name == 'zalo' else 4000)
            digest = hashlib.sha256(text.encode()).hexdigest()
            progress = ledger['partial'].get(key, {})
            start = progress.get('next', 0) if progress.get('digest') == digest else 0
            if type(start) is not int or not 0 <= start <= len(parts):
                raise ValueError('Invalid partial progress')
            failed = False
            for index in range(start, len(parts)):
                if not sender(name, config, parts[index]):
                    failed = True
                    break
                ledger['partial'][key] = {'digest': digest, 'next': index + 1}
                persist(state)
            if failed:
                failures.append(name)
                print(f'{name}: failed; pending messages will be retried next run')
                break  # Avoid repeatedly hitting a quota-limited API in this run.
            ledger['sent_ids'].append(key)
            ledger['partial'].pop(key, None)
            sent.add(key)
            persist(state)
            count += 1
        print(f'{name}: {count} announcements delivered')
    return failures


def run(fetch):
    load_dotenv()
    channels, missing = {}, []
    for name in ('telegram', 'zalo'):
        token = os.getenv(name.upper() + '_BOT_TOKEN', '').strip()
        chat = os.getenv(name.upper() + '_CHAT_ID', '').strip()
        if token and chat:
            channels[name] = (token, chat)
        elif token or chat or name == 'telegram':
            missing.append(name)
    if missing:
        print('Incomplete channel settings: ' + ', '.join(missing))
    try:
        if not channels:
            raise ValueError('No configured channels')
        state = load_state()
        items = fetch() or []
        save_state(state)
        failures = deliver(items, state, channels)
        return int(bool(failures or missing))
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, AttributeError):
        print('Checker failed: check configuration, Portal response and state file; no state reset performed.')
        return 1
