import requests
from Scripts.Utility.Exceptions import PageNotLoaded


def connect(url, return_text: bool = True, return_json: bool = False):
    r = requests.get(url)
    if r.status_code != 200:
        raise PageNotLoaded(r.url, r.status_code)
    if return_text:
        return r.text
    if return_json:
        return r.json()
