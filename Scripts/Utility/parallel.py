from concurrent.futures import as_completed
from concurrent.futures import process, thread


def run_job(func):
    with process.ProcessPoolExecutor() as executor:
        executor.submit(func)


def do__as_completed(iterable, func):
    for item in as_completed(iterable):
        func(item.result())


def print_as_completed(iterable):
    for item in as_completed(iterable):
        print(item.result())
