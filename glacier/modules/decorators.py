#!/usr/bin/env python
# encoding: utf-8

# import modules
from functools import wraps
import sys
# import our modules
from modules import glacierexception

def handle_errors(fn):
    """
    Decorator for exception handling.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except glacierexception.GlacierException as e:

            # We are only interested in the error message in case
            # it is a self-caused exception.
            e.write(indentation='||  ', stack=False, message=True)
            sys.exit(e.exitcode)

    return wrapper
