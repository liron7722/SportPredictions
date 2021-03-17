import datetime
from functools import wraps
from Scripts.Utility.logger import Logger


def track_time_spent(func_name):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start = datetime.datetime.now()
            ret = f(*args, **kwargs)
            delta = datetime.datetime.now() - start
            print(f'{func_name} took {delta.total_seconds()} seconds')
            return ret
        return wrapped
    return decorator


def log_wrapper(func_name, request=None, logger: Logger = None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ret = f(*args, **kwargs)
            if type(request) is not None:
                msg = {'requested_function': func_name,
                       'method': request.method,
                       'user_agent': str(request.user_agent),
                       'content_type': request.content_type,
                       'charset': request.charset,
                       'url': request.url,
                       'remote_address': request.remote_addr}
                logger.log(message=msg) if logger is not None else print(msg)
            return ret
        return wrapped
    return decorator
