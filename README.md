Simple slurm like Job queue written in python.

Consists of Control Daemon that collects and distributes jobs. Keeps track of worker and job status.

Supports sbatch, squeue, scancel, sinfo


### General
#### Important
- [ ] ==NEXT== Add logging (server / CtlDaemon and workers)
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
- [x] License
- [ ] System config file?

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
- [ ] ==NEXT== make sbatch work nicely
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
- [ ] ==NEXT== Add Worker I/O (output/error logs)
- [x] add process logs with <pid>.err and <pid>.out
- [x] Add Worker

#### Nice to have
- [ ] Add multiprocessing.Pool worker option for running Callables
- [ ] Add CallableJob where job.run is just running a python function
- [ ] Add shutdown function at the end (orderly shutdown)
- [ ] Add option to rerun failed jobs (x times, at the end, requeue them...)


### Jobs
#### Important

#### Nice to have
- [ ] DockerJob



Workflow Idea

<!-- 
# ssh cin-hn
# python3 daemon.py &
# exit

# ssh gber3
# python3 client.py register_worker
# python3 client.py sbatch job1.sh
# python3 client.py sbatch job2.sh
# python3 client.py sbatch job3.sh
# exit

# ssh ber1
# python3 client.py register_worker
# python3 client.py sbatch job1.sh
# exit
 -->