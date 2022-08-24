# test all deamon functionality
from pyqueue.daemon import CtlDaemon
from tests.utils import DummyJob
from pyqueue.worker import Worker

from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import os

def test_submit_update_and_get_jobs(server = None):

    daemon = CtlDaemon() if server is None else server
    job1 = DummyJob(priority=0, status="pending") 
    job2 = DummyJob(priority=1, status="pending")
    job3 = DummyJob(priority=2, status="pending")
    daemon.submit_job(job1)
    daemon.submit_job(job2)
    daemon.submit_job(job3)

    # test update job status
    daemon.update_job_status(job3.id, {"status": "running"})
    assert daemon.queue.get_dict()[job3.id].status == "running"

    # test get_running_jobs and get_pending_jobs
    assert daemon.get_num_pending_jobs() == 2
    assert daemon.get_running_ids() == [job3.id]

    # test if jobs come back in correct order
    _, job1 = daemon.acquire_job()
    _, job2 = daemon.acquire_job()
    
    # should throw IndexError since list of pending jobs is empty
    try:
        daemon.acquire_job()
    except IndexError:
        pass
    
    assert job1["status"] != "running"
    assert job2["status"] != "running"
    assert job1["priority"] > job2["priority"] 


def test_submit_job(server = None):
    daemon = CtlDaemon() if server is None else server
    job = DummyJob(priority=0, status="pending") 
    daemon.submit_job(job)
    assert job in daemon.queue


def test_update_worker_status(server = None):
    worker = Worker()
    daemon = CtlDaemon() if server is None else server
    
    worker.register_with_queue_server(daemon)
    assert len(daemon.workers) > 0
    pid = list(daemon.workers.keys())[0]
    
    daemon.update_worker_status(pid, {"status": "running"})
    assert daemon.workers[pid]["status"] == "running"


# def test_server_client_interactions():
#     daemon = SimpleXMLRPCServer(("localhost", 8001), allow_none=True, bind_and_activate=False) # problems with reusing ports
#     daemon.register_introspection_functions()
#     daemon.register_instance(CtlDaemon())

#     newpid = os.fork()
#     if newpid == 0:
#         daemon.serve_forever()
#         os._exit(0)
#     else:
#         queue_server = xmlrpc.client.ServerProxy("http://localhost:8001", allow_none=True)

#         # test_submit_update_and_get_jobs(queue_server)
#         # test_submit_job(queue_server)
#         # test_update_worker_status(queue_server)
#         daemon.server_close()
