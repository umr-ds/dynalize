'''
Created on 08.04.2015

@author: PUM
'''
import threading

#see http://stackoverflow.com/questions/3012421/python-lazy-property-decorator
def lazyproperty(fn):
    attr_name = '_lazy_' + fn.__name__
    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop


def allow_async_execution(f):
    '''
    Allows to pass "run_async=True/False" to the function to optionally run in a different thread. Defaults to run_async=False.
    Returns the thread in case of async execution, otherwise the functions return value.
    '''
    def wrapper(*args, **kwargs):
        async=False

        if "run_async" in kwargs:
            # Found async keyword. Need to remove it and run the function in a different thread
            async = kwargs["run_async"]
            del kwargs["run_async"]

        if async:
            def worker():
                f(*args, **kwargs)

            new_thread = threading.Thread(target=worker)
            new_thread.start()
            return new_thread
        else:
            # No async keyword found, run normally
            return f(*args, **kwargs)

    return wrapper
