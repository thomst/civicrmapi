import invoke
import shlex
import json
import logging
from . import v3
from . import v4
from .base import BaseApi
from .errors import InvokeError


logger = logging.getLogger(__name__)


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
            if reply.stderr:
                logger.warning(f'stderr: {reply.stderr}')
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
        params['sequential'] = params.get('sequential', 1)
        params = ['echo', json.dumps(params)]
        cv = shlex.split(self.cv)
        cwd = ['--cwd', f'{self.cwd}']
        api = ['api3', f'{entity}.{action}', '--in=json']
        command = cv + cwd + api
        return '{} | {}'.format(shlex.join(params), shlex.join(command))


class ConsoleApiV4(BaseConsoleApi):
    VERSION = v4

    def _get_command(self, entity, action, params):
        cv = shlex.split(self.cv)
        cwd = ['--cwd', f'{self.cwd}']
        api = ['api4', f'{entity}.{action}']
        params = [json.dumps(params)]
        command = cv + cwd + api + params
        return shlex.join(command)

