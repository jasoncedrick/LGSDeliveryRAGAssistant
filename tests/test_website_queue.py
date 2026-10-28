"""Synthetic concurrency checks; no real questions, model or evaluation calls."""
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
from app.website import Runtime, create_app
from app.website_language import REQUESTED_LANGUAGE
from app.website_queue import AnswerQueue


def finished(queue, ticket):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        status = queue.status(ticket)
        if status and status['state'] in ('completed', 'failed'):
            return status
        time.sleep(.005)
    raise AssertionError('Synthetic queue did not finish')


class QueueTests(unittest.TestCase):
    def client(self, answer):
        runtime = Runtime()
        runtime.pipeline = SimpleNamespace(handle_query=answer)
        runtime.health = Mock(return_value={'status': 'ready', 'message': 'Ready'})
        app = create_app(runtime, start_runtime=False)
        return TestClient(app), app.state.answer_queue, runtime

    def test_multiple_visitors_fifo_language_isolation_and_result_privacy(self):
        started, release = threading.Event(), threading.Event()
        observed = []

        def answer(question):
            observed.append((question, REQUESTED_LANGUAGE.get()))
            if question == 'first':
                started.set()
                if not release.wait(5):
                    raise RuntimeError('test timed out')
            return {'status': 'ANSWERED', 'answer': question}

        client, queue, runtime = self.client(answer)
        try:
            one = client.post('/api/jobs', json={'query': 'first', 'response_language': 'taglish'})
            self.assertEqual(one.status_code, 202)
            self.assertTrue(started.wait(2))
            two = client.post('/api/jobs', json={'query': 'second', 'response_language': 'bislish'})
            three = client.post('/api/jobs', json={'query': 'third'})
            tickets = [r.json()['ticket'] for r in (one, two, three)]
            self.assertEqual(len(set(tickets)), 3)
            pending = client.post('/api/jobs/status', json={'ticket': tickets[1]})
            self.assertEqual(pending.json(), {'state': 'queued', 'ahead': 1})
            self.assertEqual(pending.headers['cache-control'], 'no-store')
            self.assertEqual(client.post('/api/jobs/status', json={'ticket': 'x' * 43}).status_code, 404)
            self.assertEqual(client.post('/api/jobs/status', json={'ticket': '../bad'}).status_code, 422)
            # Older synchronous clients cannot overlap the queued generator.
            self.assertEqual(client.post('/api/query', json={'query': 'legacy'}).status_code, 429)
            release.set()
            for ticket, question in zip(tickets, ['first', 'second', 'third']):
                self.assertEqual(finished(queue, ticket)['result']['answer'], question)
            self.assertEqual(observed, [('first', 'taglish'), ('second', 'bislish'), ('third', 'auto')])
            self.assertFalse(runtime.query_lock.locked())
        finally:
            release.set()

    def test_capacity_accepts_ten_waiting_then_recovers(self):
        started, release = threading.Event(), threading.Event()

        def answer(question):
            started.set()
            if not release.wait(5):
                raise RuntimeError('test timed out')
            return {'status': 'ANSWERED', 'answer': question}

        client, queue, _ = self.client(answer)
        try:
            first = client.post('/api/jobs', json={'query': 'first'}).json()['ticket']
            self.assertTrue(started.wait(2))
            others = [client.post('/api/jobs', json={'query': str(i)}) for i in range(10)]
            self.assertTrue(all(r.status_code == 202 for r in others))
            full = client.post('/api/jobs', json={'query': 'overflow'})
            self.assertEqual(full.status_code, 429)
            self.assertEqual(full.headers['retry-after'], '60')
            release.set()
            for ticket in [first] + [r.json()['ticket'] for r in others]:
                self.assertEqual(finished(queue, ticket)['state'], 'completed')
            accepted = client.post('/api/jobs', json={'query': 'recovered'})
            self.assertEqual(finished(queue, accepted.json()['ticket'])['result']['answer'], 'recovered')
        finally:
            release.set()

    def test_failure_does_not_stall_queue_or_leak_error(self):
        def answer(question):
            if question == 'bad':
                raise RuntimeError('private synthetic diagnostic')
            return {'status': 'CLARIFICATION_REQUIRED', 'answer': 'Which service?'}
        client, queue, _ = self.client(answer)
        with self.assertLogs('app.website_queue', level='ERROR'):
            bad = client.post('/api/jobs', json={'query': 'bad'}).json()['ticket']
            failure = finished(queue, bad)
        self.assertEqual(failure['state'], 'failed')
        self.assertNotIn('private', str(failure))
        good = client.post('/api/jobs', json={'query': 'good'}).json()['ticket']
        self.assertEqual(finished(queue, good)['result']['status'], 'CLARIFICATION_REQUIRED')

    def test_wait_expiry_and_result_retention(self):
        now = [0]
        started, release = threading.Event(), threading.Event()
        seen = []
        def answer(question, language):
            seen.append(question)
            started.set()
            release.wait(5)
            return question
        queue = AnswerQueue(answer, clock=lambda: now[0])
        try:
            first = queue.submit('first', 'auto')
            self.assertTrue(started.wait(2))
            second = queue.submit('expired', 'auto')
            now[0] = 301
            self.assertEqual(queue.status(second)['state'], 'failed')
            release.set()
            self.assertEqual(finished(queue, first)['result'], 'first')
            self.assertEqual(seen, ['first'])
            now[0] = 902
            self.assertIsNone(queue.status(first))
            self.assertIsNone(queue.status(second))
        finally:
            release.set()

    def test_invalid_or_offline_submission_never_enqueues(self):
        answer = Mock()
        client, queue, runtime = self.client(answer)
        for payload in ({'query': ' '}, {'query': 'x' * 2001}, {'query': 'test', 'response_language': 'invalid'}):
            self.assertEqual(client.post('/api/jobs', json=payload).status_code, 422)
        runtime.health.return_value = {'status': 'model_offline', 'message': 'Offline'}
        self.assertEqual(client.post('/api/jobs', json={'query': 'test'}).status_code, 503)
        self.assertEqual(len(queue.jobs), 0)
        answer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
