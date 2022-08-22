Slurm like Job queue.


### General
- [ ] Add logging
- [X] Add users
- [X] Add priorities
- [ ] Add error handling and exceptions for jobs (Keyboard Interrupt of server / worker)

- [ ] Add tests

### Client
- [ ] make squeue nice
- [ ] make sinfo nice

### Server
- [X] Only allow one server to run at a time!
- [ ] Keep jobs in file so when Server is killed, they can potentially be resumed
- [ ] make sbatch work
- [ ] make scancel work

### Worker
- [X] Add Worker
