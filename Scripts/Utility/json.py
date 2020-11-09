#!/usr/bin/env python3

import json
import numpy as np


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def save(data, name: str = None):
    if name is None:
        name = 'NoName.json'
    # File output
    with open(name, 'w') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=True, cls=NpEncoder)


def read(name: str):
    try:
        with open(name, encoding='utf8') as json_file:
            data = json.load(json_file)
        return data
    except json.JSONDecodeError as _:
        print(f'Error in decoding this file: {name}')
        return None
