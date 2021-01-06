#!/usr/bin/env python3

from json import load, loads, dump, dumps, JSONEncoder, JSONDecodeError
from numpy import integer, floating, ndarray
from os import sep, path as os_path
from Scripts.Utility.path import create_dir

BASE_PATH = f"{os_path.dirname(os_path.realpath(''))}{sep}SportPredictions{sep}Products{sep}"


class NpEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, integer):
            return int(obj)
        elif isinstance(obj, floating):
            return float(obj)
        elif isinstance(obj, ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def encode_data(data):
    temp = dumps(data, cls=NpEncoder)
    return loads(temp)


def save(data, name: str = None, path: str = None):
    name = 'NoName.json' if name is None else name
    path = BASE_PATH if path is None else f'{BASE_PATH}{path}{sep}'
    create_dir(path)
    # File output
    with open(path + name, 'w') as outfile:
        dump(data, outfile, indent=4, ensure_ascii=True, cls=NpEncoder)
        print(f'File was save with the the name: {name} , on the path: {path}')


def read(name: str):
    try:
        with open(name, encoding='utf8') as json_file:
            data = load(json_file)
        return data
    except JSONDecodeError as _:
        print(f'Error in decoding this file: {name}')
        return None


def str_to_dict(data):
    if type(data) is str:
        return loads(data)
    elif type(data) is list:
        temp = list()
        for item in data:
            temp.append(str_to_dict(item))
        return temp
