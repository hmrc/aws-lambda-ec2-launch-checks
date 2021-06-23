"""
This type stub file was generated by pyright.
"""

import logging
from boto3.session import Session
from boto3.compat import _warn_deprecated_python

__author__ = ...
__version__ = ...
DEFAULT_SESSION = ...
def setup_default_session(**kwargs): # -> None:
    """
    Set up a default session, passing through any parameters to the session
    constructor. There is no need to call this unless you wish to pass custom
    parameters, because a default session will be created for you.
    """
    ...

def set_stream_logger(name=..., level=..., format_string=...): # -> None:
    """
    Add a stream handler for the given name and level to the logging module.
    By default, this logs all boto3 messages to ``stdout``.

        >>> import boto3
        >>> boto3.set_stream_logger('boto3.resources', logging.INFO)

    For debugging purposes a good choice is to set the stream logger to ``''``
    which is equivalent to saying "log everything".

    .. WARNING::
       Be aware that when logging anything from ``'botocore'`` the full wire
       trace will appear in your logs. If your payloads contain sensitive data
       this should not be used in production.

    :type name: string
    :param name: Log name
    :type level: int
    :param level: Logging level, e.g. ``logging.INFO``
    :type format_string: str
    :param format_string: Log message format
    """
    ...

def client(*args, **kwargs): # -> _:
    """
    Create a low-level service client by name using the default session.

    See :py:meth:`boto3.session.Session.client`.
    """
    ...

def resource(*args, **kwargs): # -> _:
    """
    Create a resource service client by name using the default session.

    See :py:meth:`boto3.session.Session.resource`.
    """
    ...

class NullHandler(logging.Handler):
    def emit(self, record): # -> None:
        ...
    


