"""
Exceptions raised by civicrmapi.

There are three main levels where errors can occur when performing an api call:

- The api cannot be reached.
- Invalid api credentials are used.
- Missing permissions.
- The api call is invalid due to malformed parameters.
- The api call cannot be processed by CiviCRM..

Exceptions raised by the first level are subprocess or requests related. We
leave them alone. If we got valid Responses but do not get valid json formatted
result data we raise InvalidResponse. This for sure can have many different
reasons.

For all api related exceptions (level 2, 3 and 4) we use either AccessDenied or
ApiError. (We try hard to distinguish them from not api related ones... which is
not always possible.)
"""


class ApiCallError(Exception):
    """
    Base class for all civicrmapi exceptions.
    """


class ApiError(ApiCallError):
    """
    Raised when CiviCRM's api returns an error-code, respectively the cv api v4
    command returns a specific stderr indicating a malformed api call.

    :params data: api result data as dict or error message as string
    :type data: dict or str
    """
    @property
    def data(self):
        """
        Result data the exception was initialized with.
        """
        return self.args[0]

    def __str__(self):
        """
        Return error_message from data if possible. Otherwise the data itself.
        """
        try:
            return self.data['error_message']
        except (TypeError, KeyError):
            return str(self.data)


class AccessDenied(ApiError):
    """
    Raised by HTTP api on access denied due to invalid credentials. This class
    uses the :class:`~.ApiError` as base class.

    :params data: api result data as dict or error message as string
    :type data: dict or str
    """


class InvalidResponse(ApiCallError):
    """
    Raised for valid responses with for - which reason ever - invalid response
    data. For example a subprocess call which succeeds but do not return valid
    json data. This may happen if the command does not reach the api at all, but
    do not exit with a proper return code.

    :params value: Either requests or subprocess response
    :type value: requests.Response or subprocess.CompletedProcess
    """
    @property
    def response(self):
        """
        Response object the exception was initialized with.
        """
        return self.args[0]

    def __str__(self):
        """
        Return `text` or `stdout` of response depending on the response type.
        """
        return getattr(self.response, 'text', self.response.stdout)
