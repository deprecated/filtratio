import sys

def this_func_name(down=1):
    """Return name of current function

    See Albert Vonpupp's answer to this SO question:  http://stackoverflow.com/questions/251464/how-to-get-the-function-name-as-string-in-python

    We modify his solution to go down one (or optionally more) levels
    in the stack, so we get the name of the calling function rather
    than this one

    """
    return sys._getframe(down).f_code.co_name
