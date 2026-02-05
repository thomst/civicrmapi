"""
Exceptions raised by civicrmapi.

There are three main levels where errors can occur when performing an api call:

- The api cannot be reached.
- Invalid api credentials are used.
- The api call is invalid due to malformed parameters.
- The api call cannot be processed by CiviCRM..

Exceptions raised by the first level are subprocess or requests related. We
leave them alone. If we got valid Responses but do not get valid json formatted
result data we raise InvalidResponse. This for sure can have many different
reasons.

For all api related exceptions (level 2, 3 and 4) we use the InvalidApiCall
class. (We try hard to distinguish them from not api related ones... which is
not always easy.)
"""

import subprocess


class InvalidApiCall(Exception):
    """
    Raised for invalid api calls of any kind:

    - Access denial because of invalid credentials.
    - Malformed api calls.
    - Invalid parameters.
    - All kind of errors due to CiviCRM's buisness logic and database integrity.
    """
    def __init__(self, value):
        if isinstance(value, dict):
            value = value.get('error_message', str(value))
        elif isinstance(value, subprocess.CalledProcessError):
            value = value.stderr
        super().__init__(value)


class InvalidResponse(Exception):
    """
    Raised for valid responses with for - which reason ever - invalid response
    data. For example a subprocess call which succeeds but do not return valid
    json data. This may happen if the command does not reach the api at all, but
    do not exit with a proper return code.

    :params value: Either requests or subprocess response or a data dict
    :type value: dict or requests.Response or subprocess.CompletedProcess
    """
    def __init__(self, value):
        super().__init__(repr(value))
