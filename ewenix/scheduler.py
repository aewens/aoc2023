from ewenix.monad import Just, Nil
from ewenix.util import now

from collections import defaultdict
from heapq import heappush, heappop, heapify

class Scheduler:
    def __init__(self):
        self.clear()

    def clear(self):
        self.jobid = 1
        self.queue = list()
        self.jobs = defaultdict(dict)

    def push(self, action, suspend=None, jobid=None):
        ts = now()
        if suspend is None:
            suspend = ts

        if jobid is None:
            jobid = self.jobid + 1
            self.jobid = jobid

        jobs = self.jobs[suspend]
        if jobs.get(jobid) is None:
            entry = dict()
            entry["ts"] = ts
            entry["action"] = action
            self.jobs[suspend][jobid] = entry

        heappush(self.queue, suspend)
        return jobid

    def pop(self):
        if len(self.queue) == 0:
            return Nil()

        suspend = heappop(self.queue)
        jobs = self.jobs.get(suspend)
        keys = sorted(jobs.keys())
        jobid = keys[0]
        entry = jobs.pop(jobid)
        if len(jobs) == 0:
            del self.jobs[suspend]

        entry["until"] = suspend
        entry["id"] = jobid
        return Just(entry)
