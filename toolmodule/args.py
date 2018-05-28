import argparse

def args(*args,**kwargs):
    def _decorator(func):
        func.__dict__.setdefault('args',[]).insert(0,(args,kwargs))
        return func
    return _decorator
