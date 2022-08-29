# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

import codecs
import datetime
import logging
import pickle
import time
from collections.abc import Iterable

from pyqueue.jobs import Job


def get_logger(name, log_level=logging.INFO, console_level=logging.WARNING):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    formatter = logging.basicConfig(
        format="%(levelname)s|%(name)s: %(asctime)s - %(message)s",
        filename="pyqueue.log",
        datefmt="%d.%m.%Y, %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def wait_until(somepredicate, timeout=5, period=0.25, *args, **kwargs):
    mustend = time.time() + timeout
    while time.time() < mustend:
        if somepredicate(*args, **kwargs):
            return True
        time.sleep(period)
    return False


def is_up(server):
    try:
        server.sinfo()
        return True
    except ConnectionRefusedError:
        return False


def fix_datetime(xmlrpc_datetime):
    return datetime.datetime.strptime(str(xmlrpc_datetime), "%Y%m%dT%H:%M:%S")


def pickle_obj(obj):
    return "pickled_" + codecs.encode(pickle.dumps(obj), "base64").decode()


def unpickle_obj(pickled_obj):
    return pickle.loads(
        codecs.decode(pickled_obj[len("pickled_") :].encode(), "base64")
    )


def try_pickle(arg):
    if any(isinstance(arg, cl) for cl in [Job]):
        return pickle_obj(arg)
    else:
        return arg


def try_unpickle(arg):
    if isinstance(arg, str) and "pickled_" in arg:
        return unpickle_obj(arg)
    else:
        return arg


# def check_unpickle(func, *args, **kwargs):

#     def wrapped_func_unpickle(*args, **kwargs):
# args = list(args)
#         for i, arg in enumerate(args):
#             args[i] = try_unpickle(arg)
# args = tuple(args)


#         for kwarg, arg in kwargs.items():
#             kwargs[kwarg] = try_unpickle(arg)

#         out = func(*args, **kwargs)

#         if isinstance(out, Iterable):
# out = list(out)
#             for i, o in enumerate(out):
#                 out[i] = try_unpickle(out)
# out = tuple(out)
#         else:
#             out = try_unpickle(out)
#         return out

#     return wrapped_func_unpickle


def check_pickle(func, *args, **kwargs):
    def wrapped_func_pickle(*args, **kwargs):
        args = list(args)
        for i, arg in enumerate(args):
            args[i] = try_pickle(arg)
        args = tuple(args)

        for kwarg, arg in kwargs.items():
            kwargs[kwarg] = try_pickle(arg)

        out = func(*args, **kwargs)
        if isinstance(out, Iterable):
            out = list(out)
            for i, o in enumerate(out):
                out[i] = try_pickle(out)
            out = tuple(out)
        else:
            out = try_pickle(out)
        return out

    return wrapped_func_pickle
