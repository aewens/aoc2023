from time import time

def now():
    return int(time())

def mint(value, default=None):
    try:
        return int(value)

    except:
        return default
