# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

import codecs
import datetime
import pickle
from collections.abc import Iterable
from pyqueue.jobs import Job


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
