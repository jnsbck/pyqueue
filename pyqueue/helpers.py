# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck


def dt2dict(dt):
    d = {"days": dt.days}
    d["hours"], rem = divmod(dt.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return d


def timedelta2dict(f, *args, **kwargs):
    def wrapped_f(*args, **kwargs):
        out = f(*args, **kwargs)

        if out is None or out == float("nan"):
            out = float("nan")
            d = {"days": out, "hours": out, "minutes": out, "seconds": out}
        elif abs(out) == float("inf"):
            d = {"days": out, "hours": out, "minutes": out, "seconds": out}
        else:
            d = dt2dict(out)
        return d

    return wrapped_f


def timedeltastr(dict):
    return "{}-{:02d}:{:02d}:{:02d}".format(
        dict["days"], dict["hours"], dict["minutes"], dict["seconds"]
    )
