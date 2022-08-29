# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

import argparse
import datetime
import getpass
import os
import sys
import xmlrpc.client

from pyqueue.daemon import StoppableServer
from pyqueue.utils import get_logger, is_up, wait_until
from pyqueue.worker import Worker

log = get_logger("CLIENT")


class QueueClient(object):
    def __init__(self, server):
        parser = argparse.ArgumentParser(
            description="Client to interact with the job queue server.",
            usage="""pyqueue <command> [<args>]
        
        sinfo: Show current system and queue status.
        squeue: Show submitted jobs.
        sbatch: Submit batch job.
        scancel: Cancel batch job.

        start: Start the queue daemon or a worker process
        stop: Stops the queue daemon or a worker process
        """,
        )
        parser.add_argument(
            "command",
            nargs="?",
            help="Subcommand to run. [sinfo, squeue, sbatch, scancel, start, stop]",
        )
        parser.add_argument(
            "-v",
            "--version",
            action="store_true",
            help="output version information and exit.",
        )
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if args.command is None:
            if args.version:
                print("pyqueue, v0.0.1")
                exit(0)
            else:
                print("No inputs were provided")
                parser.print_help()
                exit(1)
        elif not hasattr(self, args.command):
            print("Unrecognized command")
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        self.server = server
        self.user, self.timestamp, self.pid = self.get_client_info()
        self.deamon_thread = None

        getattr(self, args.command)()

    def get_client_info(self):
        user = getpass.getuser()
        timestamp = datetime.datetime.now()
        pid = os.getpid()
        return user, timestamp, pid

    def squeue(self):
        parser = argparse.ArgumentParser(description="Show queue status")
        parser.add_argument(
            "-m", "--me", action="store_true", help="only show my jobs in the queue"
        )
        parser.add_argument("-j", "--job", help="only show job queued filtered by ID")
        parser.add_argument(
            "-n", "--name", help="only show jobs queued filtered by name"
        )
        parser.add_argument(
            "-u", "--user", help="only show jobs queued filtered by user"
        )
        parser.add_argument(
            "-t", "--type", help="only show jobs queued filtered by type"
        )
        parser.add_argument(
            "-s", "--status", help="only show jobs queued filtered by status"
        )
        parser.add_argument(
            "-f",
            "--finished",
            action="store_true",
            default=False,
            help="also show jobs that have already finished",
        )
        # now that we're inside a subcommand, ignore the first TWO argvs
        args = parser.parse_args(sys.argv[2:])

        _, user_name, _ = self.get_client_info()

        print(self.server.squeue(user_name, args.__dict__))

    def register_worker(self):
        parser = argparse.ArgumentParser(
            description="Register a worker with the Queue server."
        )
        args = parser.parse_args(sys.argv[2:])

        self.server.register_worker()

    def sinfo(self):
        parser = argparse.ArgumentParser(
            description="Show current system and queue status."
        )
        # args = parser.parse_args(sys.argv[2:])

        # show some of the client info
        print(
            "date-time: {1}\nlogged in as user: {0}\ncurrent client pid: {2}\n".format(
                *self.get_client_info()
            )
        )
        try:
            print(self.server.sinfo())
        except ConnectionRefusedError:
            print("Queue daemon is not running.")

    def slog(self):
        parser = argparse.ArgumentParser(description="Show current system logs.")
        args = parser.parse_args(sys.argv[2:])

        print(self.server.slog())

    def sbatch(self):
        parser = argparse.ArgumentParser(description="submit job")
        parser.add_argument("input")
        parser.add_argument("-p", "--priority")
        args = parser.parse_args(sys.argv[2:])

        kwargs = {
            k: v for k, v in zip(["owner", "timestamp", "pid"], self.get_client_info())
        }

        self.server.sbatch(args.input, kwargs)

    def scancel(self):
        parser = argparse.ArgumentParser(description="cancel job")
        parser.add_argument(
            "-m", "--me", action="store_true", help="cancel my jobs in the queue"
        )
        parser.add_argument(
            "-j", "--job", help="cancel job with a given ID"
        )  # needs access protections!!!
        parser.add_argument(
            "-n", "--name", help="cancel jobs with a specifeid name"
        )  # needs access protections!!!
        parser.add_argument(
            "-u", "--user", help="cancel jobs queued by a specified user"
        )  # needs access protections!!!
        parser.add_argument(
            "-t", "--type", help="only show jobs queued filtered by type"
        )  # needs access protections!!!
        parser.add_argument(
            "-s", "--status", help="only show jobs queued filtered by status"
        )  # needs access protections!!!
        args = parser.parse_args(sys.argv[2:])

        print("DUMMY OUTPUT: Running scancel")

    def start(self):
        parser = argparse.ArgumentParser(
            description="Start a pyqueue service [daemon, worker]"
        )
        parser.add_argument(
            "service",
            nargs="?",
            choices=["daemon", "worker"],
            help="Service to start. [daemon, worker]",
        )
        # parser.add_argument(
        #     "-p",
        #     "--port",
        #     default=8000,
        #     type=int,
        #     help="specify the port the daemon is listening on",
        # )
        parser.add_argument(
            "-w",
            "--worker",
            action="store_true",
            default=False,
            help="quick start worker with flag argument",
        )
        parser.add_argument(
            "-d",
            "--daemon",
            action="store_true",
            default=False,
            help="quick start daemon with flag argument",
        )
        args = parser.parse_args(sys.argv[2:])
        if args.service is None and not (args.worker or args.daemon):
            parser.print_help()
        if "daemon" == args.service or args.daemon:
            try:
                self.server.sinfo()
            except ConnectionRefusedError:
                daemon = StoppableServer()
                pid = os.fork()
                if pid > 0:
                    if wait_until(is_up, server=self.server):
                        print(f"A pyqueue daemon is listening on localhost:{8000}.")
                    else:
                        raise ConnectionRefusedError(f"Could not connect to daemon.")
                else:
                    daemon.serve_forever()

        if "worker" == args.service or args.worker:
            if is_up(self.server):
                pid = os.fork()
                if pid > 0:
                    pass
                else:
                    worker = Worker()
                    worker.register_with_queue_server(self.server)
                    print(f"Spawning a worker process with pid: {worker.pid}")
                    worker.start()
            else:
                print("No Daemon running.")
        if (
            args.service not in ["daemon", "worker"]
            and not args.worker
            and not args.daemon
        ):
            print(
                f"{args.service} is not a valid service, select one of [daemon, worker]"
            )
        sys.exit(0)

    def stop(self):
        parser = argparse.ArgumentParser(
            description="Stop a pyqueue service [daemon, worker]"
        )
        parser.add_argument(
            "service",
            nargs="?",
            choices=["daemon", "worker"],
            help="Service to start. [daemon, worker]",
        )
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            default=False,
            help="ignore running or pending jobs",
        )
        parser.add_argument(
            "-i",
            "--id",
            type=int,
            help="process id of the worker in question.",
        )
        parser.add_argument(
            "-w",
            "--worker",
            action="store_true",
            default=False,
            help="quick stop worker with flag argument",
        )
        parser.add_argument(
            "-d",
            "--daemon",
            action="store_true",
            default=False,
            help="quick stop daemon with flag argument",
        )
        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            default=False,
            help="stop all running workers and daemons",
        )

        args = parser.parse_args(sys.argv[2:])
        if args.service is None and not (args.all or args.worker or args.daemon):
            parser.print_help()
        if "daemon" == args.service or args.daemon or args.all:
            try:
                num_pending = self.server.get_num_pending_jobs()
                num_running = self.server.get_num_running_jobs()
                if num_pending == 0 and num_running == 0:
                    try:
                        self.server.shutdown()
                    except ConnectionRefusedError:
                        pass  # Catches error caused by sigterm in shutdown
                elif args.force:
                    try:
                        self.server.shutdown()
                    except ConnectionRefusedError:
                        pass  # Catches error caused by sigterm in shutdown
                else:
                    print(
                        f"There are still {num_running} running and {num_pending} pending jobs. To stop the service use --force."
                    )

                if not wait_until(is_up, server=self.server):
                    print("The pyqueue daemon was successfully shut down.")
                else:
                    print("The pyqueue daemon could not be shut down.")
            except ConnectionRefusedError:
                print("No daemon seems to be active.")

        if "worker" == args.service or args.worker or args.all:
            # TODO: stop worker
            # TODO: check if worker is active then needs --force
            print("DUMMY OUTPUT: worker X was stopped successfully")
        if (
            args.service not in ["daemon", "worker"]
            and not args.worker
            and not args.daemon
            and not args.all
        ):
            print(
                f"{args.service} is not a valid service, select one of [daemon, worker]"
            )


def main():
    server = xmlrpc.client.ServerProxy("http://localhost:8000", allow_none=True)
    QueueClient(server)
    sys.exit(0)


if __name__ == "__main__":
    main()
