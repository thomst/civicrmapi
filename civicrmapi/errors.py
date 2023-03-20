import json
import requests
import invoke


class BaseException(Exception):
    def _as_json(self, value):
        try:
            result = json.loads(value)
        except json.JSONDecodeError:
            return value
        else:
            return json.dumps(result, sort_keys=True, indent=4)


class RequestError(BaseException):
    pass


class InvokeError(BaseException):
    pass


class InvalidJSON(BaseException):
    pass


class HttpError(BaseException):
    def __init__(self, reply):
        self.reply = reply

    def __str__(self):
        msg = list()
        msg.append(f'HTTP-CODE: {self.reply.status_code}')
        msg.append('RESPONSE: {}'.format(self._as_json(self.reply.text)))
        return '\n'.join(msg)


class ApiError(BaseException):
    def __init__(self,value, msg=None):
        self.value = value
        self.msg = msg

    def __str__(self):
        if self.msg:
            msg = [f'ERROR: {self.msg}']
        else:
            msg = list()
        if isinstance(self.value, requests.Response):
            msg.append(f'HTTP-CODE: {self.value.status_code}')
            msg.append('RESPONSE: {}'.format(self._as_json(self.value.text)))
        elif isinstance(self.value, invoke.runners.Result):
            msg.append(f'RETURN-CODE: {self.value.return_code}')
            msg.append('STDOUT: {}'.format(self._as_json(self.value.stdout)))
            msg.append('STDERR: {}'.format(self._as_json(self.value.stderr)))
        elif isinstance(self.value, dict) or isinstance(self.value, list):
            msg.append(json.dumps(self.value, sort_keys=True, indent=4))
        else:
            msg.append(self.value)
        return '\n'.join(msg)
