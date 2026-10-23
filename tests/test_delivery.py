import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import delivery
import news_checker


def item(key='new', summary='summary'):
    return dict(id=key, title='Title', summary=summary, date='2026-10-23', link='https://example.com')


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'state.json'
        self.override = patch.object(delivery, 'STATE', self.path)
        self.override.start()
        self.addCleanup(self.override.stop)
        self.addCleanup(self.temp.cleanup)
        self.channels = dict(telegram=('tg', '1'), zalo=('za', '2'))

    def test_legacy_migration_does_not_replay_old_news(self):
        self.path.write_text(json.dumps({'seen_ids': ['old']}))
        state = delivery.load_state()
        calls = []
        delivery.deliver([item('old')], state, self.channels,
                         sender=lambda *a: calls.append(a) or True)
        self.assertEqual(calls, [])

    def test_zalo_failure_does_not_resend_successful_telegram(self):
        state = delivery.load_state()
        calls = []
        def sender(name, config, text):
            calls.append(name)
            return name != 'zalo'
        self.assertEqual(delivery.deliver([item()], state, self.channels, sender=sender), ['zalo'])
        self.assertEqual(state['deliveries']['telegram']['sent_ids'], ['new'])
        self.assertEqual(state['deliveries']['zalo']['sent_ids'], [])
        calls.clear()
        state = delivery.load_state()
        delivery.deliver([item()], state, self.channels, sender=lambda name, *a: calls.append(name) or True)
        self.assertEqual(calls, ['zalo'])

    def test_telegram_failure_still_attempts_zalo(self):
        state = delivery.load_state()
        delivery.deliver([item()], state, self.channels, sender=lambda name, *a: name == 'zalo')
        self.assertEqual(state['deliveries']['zalo']['sent_ids'], ['new'])
        self.assertEqual(state['deliveries']['telegram']['sent_ids'], [])

    def test_partial_long_message_resumes_without_repeating_confirmed_chunks(self):
        state = delivery.load_state()
        calls = []
        def sender(name, config, text):
            calls.append(text)
            return len(calls) != 2
        message = item(summary='😀' * 2500)
        delivery.deliver([message], state, {'zalo': ('za', '2')}, sender=sender)
        self.assertEqual(state['deliveries']['zalo']['partial']['new']['next'], 1)
        resumed = []
        delivery.deliver([message], delivery.load_state(), {'zalo': ('za', '2')},
                         sender=lambda name, config, text: resumed.append(text) or True)
        self.assertEqual(resumed[0], calls[1])
        for text in calls + resumed:
            self.assertLessEqual(len(text.encode('utf-16-le')) // 2, 2000)

    def test_more_than_50_items_do_not_repeat(self):
        messages = [item(str(i)) for i in range(65)]
        delivery.deliver(messages, delivery.load_state(), self.channels, sender=lambda *a: True)
        calls = []
        delivery.deliver(messages, delivery.load_state(), self.channels, sender=lambda *a: calls.append(a) or True)
        self.assertEqual(calls, [])

    def test_corrupted_state_is_not_reset(self):
        self.path.write_text('{bad')
        with self.assertRaises(ValueError):
            delivery.load_state()
        self.assertEqual(self.path.read_text(), '{bad')

    def test_http_200_api_rejection_is_failure(self):
        with patch.object(delivery.requests, 'post') as post:
            post.return_value.json.return_value = {'ok': False}
            self.assertFalse(delivery.send('zalo', ('secret', 'group'), 'hello'))

    def test_send_errors_do_not_log_token(self):
        output = io.StringIO()
        with patch.object(delivery.requests, 'post', side_effect=delivery.requests.RequestException('secret-token')):
            with contextlib.redirect_stdout(output):
                self.assertFalse(delivery.send('zalo', ('secret-token', 'group'), 'hello'))
        self.assertNotIn('secret-token', output.getvalue())

    def test_missing_optional_zalo_keeps_telegram(self):
        env = dict(TELEGRAM_BOT_TOKEN='tg', TELEGRAM_CHAT_ID='1')
        with patch.dict(os.environ, env, clear=True), patch.object(delivery, 'load_dotenv'):
            with patch.object(delivery, 'deliver', return_value=[]) as mock:
                self.assertEqual(delivery.run(lambda: []), 0)
                self.assertEqual(set(mock.call_args.args[2]), {'telegram'})

    def test_portal_failure_returns_error_without_altering_state(self):
        self.path.write_text('{"seen_ids": ["old"]}')
        env = dict(TELEGRAM_BOT_TOKEN='tg', TELEGRAM_CHAT_ID='1')
        with patch.dict(os.environ, env, clear=True), patch.object(delivery, 'load_dotenv'):
            def fail():
                raise RuntimeError('login failed')
            self.assertEqual(delivery.run(fail), 1)
        self.assertEqual(json.loads(self.path.read_text()), {'seen_ids': ['old']})

    def test_fetch_does_not_write_delivery_state(self):
        with patch.object(news_checker, 'load_dotenv'), patch.object(news_checker.requests, 'Session') as session:
            client = session.return_value
            client.post.return_value.json.return_value = {'url': 'https://example.com/session'}
            client.get.return_value.json.return_value = [dict(id=123, tieuDe='Title', tomTatNoiDung='Summary', link='https://example.com', ngayDang='today')]
            result = news_checker.check_for_update()
            self.assertEqual(result[0]['id'], '123')
            self.assertFalse(self.path.exists())


if __name__ == '__main__':
    unittest.main()
