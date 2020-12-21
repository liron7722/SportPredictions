from time import time, sleep


def call_sleep(seconds=0, minutes=0, hours=0, days=0, logger=None):
    message = f"Going to sleep for {days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
    logger.info(message) if logger is not None else print(message)
    sleep((days * 24 * 60 * 60) + (hours * 60 * 60) + (minutes * 60) + seconds)


def time_measure(total_time):
    if total_time > 24 * 60 * 60:
        unit = 'days'
        total_time = total_time / 60 / 60 / 24

    elif total_time > 60 * 60:
        unit = 'hours'
        total_time = total_time / 60 / 60

    elif total_time > 60:
        unit = 'minutes'
        total_time = total_time / 60

    else:
        unit = 'seconds'

    return total_time, unit


def time_wrapper(func, logger=None):
    # Decorator that reports the execution time.
    def wrap(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()
        total_time, unit = time_measure(total_time=end - start)

        # Print | Log
        msg = f'This operation of {func.__name__} took {round(total_time, 2)} {unit}'
        if logger is not None:
            logger.debug(msg)
        else:
            print(msg)

        return result
    return wrap
