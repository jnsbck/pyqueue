import datetime

def timedelta2dict(f,*args, **kwargs):
    def wrapped_f(*args, **kwargs):
        out = f(*args, **kwargs)
    
        if out is None or out == float("nan"):
            out = float("nan")
            d = {"days": out, "hours": out, "minutes": out, "seconds": out}
        elif abs(out) == float("inf"):
            d = {"days": out, "hours": out, "minutes": out, "seconds": out}
        else:
            d = {"days": out.days}
            d["hours"], rem = divmod(out.seconds, 3600)
            d["minutes"], d["seconds"] = divmod(rem, 60)
            return d
    return wrapped_f

def datetime2str(t):
    return t.strftime("%H:%M:%S, %d.%m.%Y")

def fix_datetime(xmlrpc_datetime):
    return datetime.datetime.strptime(str(xmlrpc_datetime), '%Y%m%dT%H:%M:%S')