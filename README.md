[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![pyqueue version](https://img.shields.io/badge/version-v0.01-green.svg)](https://github.com/jnsbck/pyqueue)
[![Tests](https://github.com/jnsbck/pyqueue/workflows/Tests/badge.svg?branch=main)](https://github.com/jnsbck/pyqueue/actions)

# pyqueue

Simple slurm like Job queue written in python.

Consists of Control Daemon that collects and distributes jobs. Keeps track of workers and job status.

Supports sbatch, squeue, sinfo and (not yet) scancel.


## Install
1. Clone the repo
2. `cd pyqueue`
3. `python3 setup.py .`

To test if the installation was successful, type `pyqueue`

## Getting started
To use pyqueue, start the queue daemon with `pyqueue start daemon`. You can check if the deamon is running with `pyqueue sinfo`.

Now the daemon is ready to accept jobs, which you can submit with `sbatch`, i.e. `pyqueue sbatch Hello World!` and monitor with `pyqueue squeue`. All of the jobs that are submitted to the daemon get collected and distributed among the worker processes that the daemon manages. To spin up a worker, you can run `pyqueue start worker`. You can check the status of the worker by calling `pyqueue sinfo`. The outputs for each job are stored in `./outputs/`.

## Structure
To keep pyqueue somewhat modular, it is split into:
- `daemon.py`, queue server
- `client.py`, client
- `worker.py`, worker processes
- `jobs.py`, job specifications

Any of the 4 componenents can be extendend and worked on relatively independently of the remaining parts. Other Job types can be added as long as they inherit from `Job`.

---
---
## To Dos:
### General
#### Important
- [x] Add logging (server / CtlDaemon and workers)
- [ ] Add error handling and exceptions for jobs (also Keyboard Interrupt of server / worker)

#### Nice to have
- [ ] Add tests
    - [x] tests for all job types
    - [x] tests for daemon
    - [ ] ==NEXT== tests for worker
    - [ ] tests for client
- [ ] Add Type Hinting and Documentation and comments
- [x] Add users
- [x] Add priorities
- [ ] Add timing of jobs
- [ ] setup.py
    - [x] add setup.py
    - [ ] test setup.py in VM
- [x] License
- [ ] System config file? (log_dir, output_dir, port, daemon address)

---
### Client
#### Important
- [x] Start/stop daemon from client

#### Nice to have
- [x] make squeue nice
    - [x] add flag for state
    - [x] add flat to show finished
    - [x] add flag to show jobtype
    - [x] add flag to show user
    - [x] add flag to show me
    - [x] add flag to show id
- [x] make sinfo nice

---
### Server
#### Important
- [x] Only allow one server to run at a time!
- [x] make sbatch work nicely
- [-] make scancel work
- [x] Send and receive jobs as pickle, rather than dict

#### Nice to have
- [ ] Keep jobs in file so when Server is killed, they can potentially be resumed
- [ ] Make client functions accept kwargs
- [ ] Register the workers automatically (up to max number of workers, as specified in kwargs)
- [ ] Remove finished jobs from queue (all or if they are too old)
- [ ] Change to different protocol i.e. HTTP? (one that does not need pickling of objects)
- [ ] Look into server option `register_instance(instance, allow_dotted_names=False)` that could expose class variables and allow to change them without the dictionary hussle of updating them


---
### Worker
#### Important
- [ ] Worker is somewhat of a mess that needs fixing
- [x] Add Worker I/O (output/error logs)
- [x] add process logs with <pid>.err and <pid>.out
- [x] Add Worker

#### Nice to have
- [ ] Add multiprocessing.Pool worker option for running Callables
- [ ] Add CallableJob where job.run is just running a python function
- [ ] Add shutdown function at the end (orderly shutdown)
- [ ] Add option to rerun failed jobs (x times, at the end, requeue them...)

---
### Jobs
#### Important

#### Nice to have
- [ ] DockerJob