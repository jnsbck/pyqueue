# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

import threading
import time
import xmlrpc.client

import pytest

from pyqueue import worker
from pyqueue.daemon import CtlDaemon, StoppableServerThread
from pyqueue.utils import try_pickle, try_unpickle
from pyqueue.worker import Worker
from tests.utils import DummyJob


def test_submit_update_and_get_jobs(server=None, client=None):
    daemon = CtlDaemon() if server is None else server.instance
    client = daemon if client is None else client

    job1 = DummyJob(priority=0, status="pending")
    job2 = DummyJob(priority=1, status="pending")
    job3 = DummyJob(priority=2, status="pending")
    client.submit_job(try_pickle(job1))
    client.submit_job(try_pickle(job2))
    client.submit_job(try_pickle(job3))

    # test update job status
    client.update_job_status(job3.id, {"status": "running"})
    assert (
        daemon.queue.get_dict()[job3.id].status == "running"
    ), "job status could not be updated"
    # test get_running_jobs and get_pending_jobs
    assert (
        daemon.get_num_pending_jobs() == 2
    ), "number of pending jobs does not match the expected number"
    assert daemon.get_running_ids() == [
        job3.id
    ], "the ID of the running job is not the correct"

    # test if jobs come back in correct order
    job1 = try_unpickle(client.acquire_job())
    job2 = try_unpickle(client.acquire_job())

    # should throw IndexError since list of pending jobs is empty
    try:
        client.acquire_job()
    except IndexError:
        pass
    except xmlrpc.client.Fault as exception:
        if "IndexError" in exception.faultString:
            pass
        else:
            raise exception

    assert (
        job1.status == "submitted"
    ), f"Job status should equal submitted, instead is {job1.status}"
    assert (
        job2.status == "submitted"
    ), f"Job status should equal submitted, instead is {job2.status}"
    assert job1.priority > job2.priority, "Jobs were fetched in the wrong order"


def test_submit_job(server=None, client=None):
    daemon = CtlDaemon() if server is None else server.instance
    client = daemon if client is None else client

    job = DummyJob(priority=0, status="pending")
    client.submit_job(try_pickle(job))

    assert (
        job in daemon.queue
    ), "Either no or not the same job that was submitted was queued."


def test_update_worker_status(server=None, client=None):
    worker = Worker()
    daemon = CtlDaemon() if server is None else server.instance
    client = daemon if client is None else client

    worker.register_with_queue_server(client)
    assert len(daemon.workers) > 0, "No worker was registered."
    pid = list(daemon.workers.keys())[0]

    client.update_worker_status(pid, {"status": "running"})
    status = daemon.workers[pid]["status"]
    assert status == "running", f"job status should be running, instead it is {status}"


@pytest.mark.parametrize(
    "test",
    [test_update_worker_status, test_submit_update_and_get_jobs, test_submit_job],
)
def test_server_client_interaction(test):
    def test_with_server_and_client(test):
        thread = StoppableServerThread(port=8001)
        server = thread.server
        thread.start()

        client = xmlrpc.client.ServerProxy("http://localhost:8001", allow_none=True)

        # ensures that the server is closed before the exception is raised!
        try:
            test(server, client)
            thread.stop()
        except Exception as exception:
            thread.stop()
            raise exception

    test_with_server_and_client(test)
    time.sleep(
        0.5
    )  # for some reason without this OSError: [Errno 98] (Address already in use) is raised
