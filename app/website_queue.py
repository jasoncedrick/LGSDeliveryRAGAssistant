"""Bounded, in-memory delivery queue; never changes the research pipeline."""
from collections import OrderedDict
import logging
import secrets
import threading
import time


class QueueFull(Exception):
    pass


class AnswerQueue:
    def __init__(self, answer, capacity=11, retention=600, wait_limit=300, clock=time.monotonic):
        self.answer = answer
        self.capacity = capacity  # One running request plus up to ten waiting.
        self.retention = retention
        self.wait_limit = wait_limit
        self.clock = clock
        self.lock = threading.Lock()
        self.jobs = OrderedDict()
        self.worker = None

    def _prune(self):
        now = self.clock()
        for ticket, job in list(self.jobs.items()):
            if job['state'] == 'queued' and now - job['created'] >= self.wait_limit:
                job.clear()
                job.update(state='failed', finished=now,
                           detail='The waiting time limit was reached. Please submit your question again.')
            if job['state'] in ('completed', 'failed') and now - job['finished'] >= self.retention:
                del self.jobs[ticket]
        # Bound retained response memory even during heavy use.
        terminal = [key for key, job in self.jobs.items() if job['state'] in ('completed', 'failed')]
        for key in terminal[:-100]:
            del self.jobs[key]

    def submit(self, question, language):
        with self.lock:
            self._prune()
            if sum(j['state'] in ('queued', 'running') for j in self.jobs.values()) >= self.capacity:
                raise QueueFull()
            ticket = secrets.token_urlsafe(32)
            self.jobs[ticket] = dict(state='queued', created=self.clock(),
                                     question=question, language=language)
            if self.worker is None:
                self.worker = threading.Thread(target=self._run, name='citizen-answer-queue', daemon=True)
                self.worker.start()
            return ticket

    def status(self, ticket):
        with self.lock:
            self._prune()
            job = self.jobs.get(ticket)
            if job is None:
                return None
            result = {'state': job['state']}
            if job['state'] == 'queued':
                active = [key for key, j in self.jobs.items() if j['state'] in ('queued', 'running')]
                result['ahead'] = active.index(ticket)
            elif job['state'] == 'completed':
                result['result'] = job['result']
            elif job['state'] == 'failed':
                result['detail'] = job['detail']
            return result

    def _run(self):
        while True:
            with self.lock:
                self._prune()
                job = next((j for j in self.jobs.values() if j['state'] == 'queued'), None)
                if job is None:
                    self.worker = None
                    return
                job['state'] = 'running'
                question, language = job.pop('question'), job.pop('language')
            try:
                result = self.answer(question, language)
            except Exception:
                logging.getLogger(__name__).exception('Queued citizen request failed')
                with self.lock:
                    job.update(state='failed', finished=self.clock(),
                               detail='The assistant could not complete this question. Please try again.')
            else:
                with self.lock:
                    job.update(state='completed', finished=self.clock(), result=result)
