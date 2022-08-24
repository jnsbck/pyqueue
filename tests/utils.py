import time
from pyqueue.jobs import Job
import pytest

@pytest.mark.skip()
class DummyJob(Job):
    def __init__(self, priority=0, force_exception=False, status="pending"):
        super().__init__(priority=priority)
        self.name = "testjob"
        self.status = status


    def run(self):
        return 1, "stdout", "stderr"

    def kill(self):
        pass # for now

    def check_alive(self):
        return None # for now

@pytest.mark.skip()
def dummy_pyjob(seconds=10, force_exception=False):
    
    time.sleep(seconds)
    print("test print")
    
    if force_exception:
        raise Exception("test exception")


    return "test output"

# test bash job
# python3 testjob.py

    