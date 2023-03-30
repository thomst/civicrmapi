import json
import requests
import invoke


class BaseException(Exception):
    """
    All exceptions possibly raised by civicrmapi inherit from BaseException.
    """
    pass

class RequestError(BaseException):
    """
    A simple wrapper for all exceptions raised by requests.
    """
    pass


class InvokeError(BaseException):
    """
    A simple wrapper for all exceptions raised by invoke.
    """
    pass


class InvalidJSON(BaseException):
    """
    A simple wrapper for a json.JSONDecodeError.
    """
    pass


class ApiError(BaseException):
    """
    Raised for all api related errors as well as return-code and http errors.
    """
    def __init__(self,value, msg=None):
        self.value = value
        self.msg = msg

    def _as_json(self, value):
        try:
            result = json.loads(value)
        except json.JSONDecodeError:
            return value
        else:
            return json.dumps(result, sort_keys=True, indent=4)

    def __str__(self):
        if self.msg:
            msg = [f'ERROR: {self.msg}']
        else:
            msg = list()
        if isinstance(self.value, requests.Response):
            msg.append(f'URL: {self.value.url}')
            msg.append(f'HTTP-CODE: {self.value.status_code}')
            msg.append('RESPONSE: {}'.format(self._as_json(self.value.text)))
        elif isinstance(self.value, invoke.runners.Result):
            msg.append(f'COMMAND: {self.value.command}')
            msg.append(f'RETURN-CODE: {self.value.return_code}')
            msg.append('STDOUT: {}'.format(self._as_json(self.value.stdout)))
            msg.append('STDERR: {}'.format(self._as_json(self.value.stderr)))
        elif isinstance(self.value, dict) or isinstance(self.value, list):
            msg.append(json.dumps(self.value, sort_keys=True, indent=4))
        else:
            msg.append(self.value)
        return '\n'.join(msg)
