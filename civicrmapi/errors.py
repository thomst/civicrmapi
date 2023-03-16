import json


class BaseException(Exception):
    pass


class RequestError(BaseException):
    pass


class InvokeError(BaseException):
    pass


class HttpError(BaseException):
    def __init__(self, reply):
        self.reply = reply
        self.code = reply.status_code

    def __str__(self):
        lines = list()
        if not self.code == 200:
            lines.append('ERROR {}'.format(self.code))
        try:
            result = json.loads(self.reply.text)
        except json.JSONDecodeError:
            lines.append(self.reply.text)
        else:
            for key, value in result.items():
                lines.append(f'{key}: {value}')
        return '\n'.join(lines)


class InvalidJson(BaseException):
    def __init__(self, result):
        self.result = result

    def __str__(self):
        lines = ['Invalid json:']
        lines.append(self.result)
        return '\n'.join(lines)


class ApiError(BaseException):
    def __init__(self, result):
        self.result = result

    def __str__(self):
        lines = list()
        for key, value in result.items():
            lines.append(f'{key}: {value}')
        return '\n'.join(lines)
