from time import sleep


def call_sleep(seconds=0, minutes=0, hours=0, days=0, logger=None):
    massage = f"Going to sleep for {days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
    if logger is not None:
        logger.info(massage)
    sleep((days * 24 * 60 * 60) + (hours * 60 * 60) + (minutes * 60) + seconds)
