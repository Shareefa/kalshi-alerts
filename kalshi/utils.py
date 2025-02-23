
from collections import defaultdict
import random
from typing import Any, Iterable


def analyze_json_type(json_data: Iterable[dict[str, Any]]):
    obj = defaultdict(dict)
    for item in json_data:
        for key, value in item.items():
            t = type(value).__name__
            if t not in obj[key]:
                obj[key][t] = 1
            else:
                obj[key][t] += 1
    for key, value in obj.items():
        print(f'{key}:')
        for t, items in value.items():
            print(f'\t{t}: {items}')


