import requests
from Scripts.Utility.time import call_sleep
from Scripts.Utility.exceptions import PageNotLoaded


def connect(url, return_text: bool = True, return_json: bool = False, re_try: int = 5):
    r = requests.get(url)
    if r.status_code != 200:
        call_sleep(seconds=5)
        if re_try > 0:
            return connect(url, return_text, return_json, re_try=re_try - 1)
        raise PageNotLoaded(r.url, r.status_code)
    if return_text:
        return r.text
    if return_json:
        return r.json()


def post(url, data=None, return_text: bool = True, return_json: bool = False, re_try: int = 5):
    r = requests.post(url, data=data)
    if r.status_code != 200:
        call_sleep(seconds=5)
        if re_try > 0:
            return connect(url, return_text, return_json, re_try=re_try - 1)
        raise PageNotLoaded(r.url, r.status_code)
    if return_text:
        return r.text
    if return_json:
        return r.json()
