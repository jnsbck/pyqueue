# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

import inspect
import os
from abc import ABC

import pytest

import pyqueue.jobs as Jobs
from tests.utils import DummyJob, is_picklable

testable_jobs = [DummyJob]
for name, obj in inspect.getmembers(Jobs):
    if inspect.isclass(obj) and obj not in [Jobs.Job, ABC]:
        testable_jobs.append(obj)


@pytest.mark.parametrize("Job", testable_jobs)
def test_if_job_is_picklable(Job):
    job = Job()
    assert is_picklable(job), f"{job.__class__} is not picklable!"


def test_bashjob_name_extraction():
    cmd2name = {
        "echo hello": "echo",
        "python3 echo.py -a hell --last_letter o": "echo.py",
        "bash echo.sh": "echo.sh",
        "./echo.sh hello": "echo.sh",
    }
    for cmd, name in cmd2name.items():
        job = Jobs.BashJob(cmd)
        assert job.name == name, "job was not named as expected. "


@pytest.mark.parametrize(
    "Job, expected_out, expected_err",
    [(DummyJob, "test print", "test warn"), (Jobs.BashJob, "no cmd provided\n", "")],
)
def test_job_run(Job, expected_out, expected_err):
    job = Job()
    output_dir = "./test_outputs/"
    os.makedirs(output_dir, exist_ok=True)
    if job._out != None:
        job._out = f"{output_dir}testjob_{job.id}.out"
        job._err = f"{output_dir}testjob_{job.id}.err"

    status, out, err = job.run()
    assert status == 0, "Job seems to fail or return 1"
    assert (
        expected_err == err
    ), f"expected error: {expected_err} != returned error {err}"

    with open(job._out, "r") as fout:
        out = fout.read()
    assert (
        expected_out == out
    ), f"output written to file was not what was expceted: expected {expected_out} != written {out}"

    with open(job._err, "r") as ferr:
        err = ferr.read()
    assert (
        err == expected_err
    ), f"error written to file was not what was expceted: expected {expected_out} != written {out}"

    # rm dir and files from testing
    os.remove(job._out)
    os.remove(job._err)
    os.rmdir(output_dir)


# @pytest.mark.parametrize("Job", testable_jobs)
# def test_check_alive(Job):
#     job = Job()
#     assert job.check_alive()
#
#     job.run()
#     assert job.check_alive()

#     job.kill()
#     assert not job.check_alive()

# @pytest.mark.parametrize("Job", testable_jobs)
# def test_job_kill(Job):
#     job = Job()
#     job.kill()
#     assert not job.check_alive(), "Job was not reliably killed."

#     job = Job()
#     job.run()
#     job.kill()
#     assert not job.check_alive(), "Job was not reliably killed."
