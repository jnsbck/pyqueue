import time

def test_pyjob(seconds=10, force_exception=False):
    
    time.sleep(seconds)
    print("test print")
    
    if force_exception:
        raise Exception("test exception")


    return "test output"

# test bash job
# python3 testjob.py

    