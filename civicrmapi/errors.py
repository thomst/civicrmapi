
class RestConnectionError(Exception):
    pass


class RestApiError(Exception):
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
