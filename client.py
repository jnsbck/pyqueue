import xmlrpc.client
import argparse
import sys

import getpass
import datetime
import os


class QueueClient(object):

    def __init__(self, server):
        parser = argparse.ArgumentParser(description='Client to interact with the job queue server.', usage='''queue-client <command> [<args>]
        
        sinfo: Show current system and queue status.
        squeue: Show submitted jobs.
        sbatch: Submit batch job.
        scancel: Cancel batch job.
        ''')
        parser.add_argument('command', nargs='?', help='Subcommand to run. [sinfo, squeue, sbatch, scancel]')
        parser.add_argument('-v', '--version', action='store_true', help='output version information and exit.')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if args.command is None:
            if args.version:
                print("v0.0.1")
                exit(1)
            else:
                print('No inputs were provided')
                parser.print_help()
                exit(1)
        elif not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        self.server = server
        self.user, self.timestamp, self.pid = self.get_client_info()

        getattr(self, args.command)()
    
    def get_client_info(self):
        user = getpass.getuser()
        timestamp = datetime.datetime.now()
        pid = os.getpid()
        return user, timestamp, pid

    def squeue(self):
        parser = argparse.ArgumentParser(
            description='Show queue status')
        parser.add_argument('-m', '--me')
        parser.add_argument('-j', '--job')
        parser.add_argument('-n', '--name')
        parser.add_argument('-u', '--user')
        # now that we're inside a subcommand, ignore the first TWO argvs
        args = parser.parse_args(sys.argv[2:])
        
        print("; ".join(["idx", "type", "id", "ppid", "pid", "status", "owner", "submitted", "time"]))
        print(self.server.squeue())

    def register_worker(self):
        parser = argparse.ArgumentParser(
            description='Register a worker with the Queue server.')
        # now that we're inside a subcommand, ignore the first TWO argvs
        args = parser.parse_args(sys.argv[2:])

        server.register_worker()        

    def sinfo(self):
        parser = argparse.ArgumentParser(
            description='Show current system and queue status.')
        args = parser.parse_args(sys.argv[2:])
        
        # show number and stats for registered workers (uptime, status, client info)
        # show length of queue
        # show some of the client info
        print("user: %s, date-time: %s, pid: %s" % self.get_client_info())
        print(server.info())
    
    def sbatch(self):
        parser = argparse.ArgumentParser(
            description='submit job')
        parser.add_argument("input")
        args = parser.parse_args(sys.argv[2:])
        
        
        kwargs = {k:v for k,v in zip(["owner", "timestamp", "pid"], self.get_client_info())}
        
        server.sbatch(args.input, kwargs)

    def scancel(self):
        parser = argparse.ArgumentParser(
            description='cancel job')
        parser.add_argument('-m', '--me')
        parser.add_argument('-j', '--job')
        parser.add_argument('-n', '--name')
        parser.add_argument('-u', '--user')
        args = parser.parse_args(sys.argv[2:])
        
        print("Running scancel")


if __name__ == '__main__':
    server = xmlrpc.client.ServerProxy("http://localhost:8000")
    QueueClient(server)