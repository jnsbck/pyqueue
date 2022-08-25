import os
import sys
import time
import warnings

import pyqueue
from pyqueue.utils import pickle_obj

Job = pyqueue.jobs.Job


class DummyJob(Job):
    def __init__(
        self,
        priority=0,
        force_exception=False,
        status="pending",
        output_dir="./test_outputs",
    ):
        super().__init__(priority=priority)
        self.name = "testjob"
        self.status = status
        self.output_dir = output_dir
        self.force_exception = force_exception
        self._out = os.path.join(output_dir, f"{self.name}_{self.id}.out")
        self._err = os.path.join(output_dir, f"{self.name}_{self.id}.err")

    def run(self):
        with open(self._out, "w") as sys.stdout:
            print("test print", end="")

        with open(self._err, "w") as sys.stderr:
            sys.stderr.write("test warn")

        if self.force_exception:
            raise Exception

        return 0, "test print", "test warn"

    def kill(self):
        pass  # for now

    def check_alive(self):
        return None  # for now


def dummy_pyjob(seconds=10, force_exception=False):

    time.sleep(seconds)
    print("test print")

    if force_exception:
        raise Exception("test exception")

    return "test output"


def is_picklable(obj):
    try:
        pickle_obj(obj)
        return True
    except Exception:
        return False
