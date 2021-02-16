from Scripts.API.prediction_site_helper import Helper
from Scripts.Utility.time import call_sleep


def run():
    helper = Helper()
    while True:
        helper.load()
        call_sleep(hours=1)


if __name__ == '__main__':
    run()
