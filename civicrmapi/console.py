import invoke
import shlex
import json
import logging
from . import v3
from . import v4
from .base import BaseApi
from .errors import InvokeError
from .errors import ApiError


logger = logging.getLogger('civicrmapi')


class BaseConsoleApi(BaseApi):
    def __init__(self, cv, cwd):
        super().__init__()
        self.cv = cv
        self.cwd = cwd

    def _run(self, command):
        logger.info(f'Run command: {command}')
        try:
            reply = invoke.run(command, hide=True)
        except Exception as exc:
            raise InvokeError(exc)
        else:
            logger.info(f'Running command finished [{reply.return_code}]')
            logger.debug(f'- stdout: {reply.stdout}')
            logger.debug(f'- stderr: {reply.stderr}')

        if reply.stderr and not reply.stdout:
            raise ApiError(reply)
        else:
            return reply

    def _get_command(self, entity, action, params):
        raise NotImplemented

    def _perform_api_call(self, entity, action, params):
        command = self._get_command(entity, action, params)
        reply = self._run(command)
        return reply.stdout


class ConsoleApiV3(BaseConsoleApi):
    VERSION = v3

    def _get_command(self, entity, action, params):
        params['sequential'] = 1
        params = ['echo', shlex.quote(json.dumps(params))]
        cv = shlex.split(self.cv)
        cwd = ['--cwd', shlex.quote(f'{self.cwd}')]
        api = ['api3', shlex.quote(f'{entity}.{action}'), '--in=json']
        command = cv + cwd + api
        return '{} | {}'.format(' '.join(params), ' '.join(command))


class ConsoleApiV4(BaseConsoleApi):
    VERSION = v4

    def _get_command(self, entity, action, params):
        cv = shlex.split(self.cv)
        cwd = ['--cwd', shlex.quote(f'{self.cwd}')]
        api = ['api4', shlex.quote(f'{entity}.{action}')]
        params = [shlex.quote(json.dumps(params))] if params else list()
        command = cv + cwd + api + params
        return ' '.join(command)

