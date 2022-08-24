# test all deamon functionality

def test_get_jobs(server):
    assert server.get_pending_jobs() == 1
    assert server.get_running_jobs() == 1

def test_priority_queue(server):
    _, job1 =  server.aquire_job()
    _, job2 =  server.aquire_job()
    assert job1["priority"] > job2["priority"] 

def test_update_job_status(server):
    server.update_job_status(id, dict)
    assert server.queue.get_dict()[id] == dict

# def test_update_worker_status(server):
#     server.update_worker_status(pid, {"status": "running"})
#     assert server.workers[pid]["status"] == "runnning"

def test_submit_job(server):
    server.submit_job(job)

def test_check_alive(server):
    job1
    job2
    assert server.check_alive(job1.id)
    assert not server.check_alive(job2.id)
    

# ------------------ CLIENT FUNCTIONALITY -------------------
def test_sbatch(server):
    # submit testjob
    # test if job is queued and set to pending
    # test if commandline kwargs all work
    pass

def test_squeue(server):
    # submit testjob1
    # submit testjob2
    # test if commandline kwargs all work
    pass

def test_scancel(server):
    # submit testjob
    # test if job is running
    # test if job is killed
    pass

def test_sinfo(server):
    # test if commandline kwargs all work
    pass

def register_worker(server):
    # create worker and register it (does not require start)
    pass

def kill_worker(server):
    # create worker, run it
    # kill it, check if all jobs also killed
    pass
