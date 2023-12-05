from enum import Enum, auto
from json import loads

DONE = "%DONE%"

class BMode(Enum):
    INT  = auto()
    LIST = auto()
    DICT = auto()
    BYTE = auto()

def bdecode(data):
    if len(data) == 0:
        return

    char = data[0]
    data = data[1:]

    if char == "e":
        return data, DONE

    if char == "i":
        cache = ""
        while True:
            char = data[0]
            data = data[1:]

            if char == "e":
                return data, int(cache)

            cache = cache + char

    elif char == "l":
        final = list()
        while True:
            data, value = bdecode(data)
            if value == DONE:
                break

            final.append(value)

        return data, final

    elif char == "d":
        final = dict()
        key = None
        while True:
            data, value = bdecode(data)
            if value == DONE:
                break

            if key is None:
                key = value
                continue

            final[key] = value
            key = None

        return data, final

    else:
        size = None
        cache = char
        while True:
            char = data[0]
            data = data[1:]

            if size is None and char == ":":
                size = int(cache)
                cache = ""
                continue

            cache = cache + char
            if size is not None and len(cache) == size:
                return data, cache

    return data, DONE

def bencode(data, enc=False):
    if enc:
        data = loads(data)

    cache = ""
    if isinstance(data, dict):
        cache = cache + "d"
        for key, value in data.items():
            cache = cache + bencode(key)
            cache = cache + bencode(value)

        cache = cache + "e"
        return cache

    elif isinstance(data, list):
        cache = cache + "l"
        for value in data:
            cache = cache + bencode(value)

        cache = cache + "e"
        return cache

    elif isinstance(data, int):
        return f"i{data}e"

    else:
        size = len(data)
        return f"{size}:{data}"
