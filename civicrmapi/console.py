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
    def __init__(self, cv, cwd=None, context=None):
        """
        :param str cv: cv command
        :param str cwd: working directory for cv
        :param str context:
            If a context is given the original command will be tokenized and
            given to the context as positional argument. The simplest context
            migth be a 'sh -c'. But it could also be a docker-exec- or
            ssh-command to run the api call within a docker container or on a
            remote machine.
        """
        super().__init__()
        self.cv = shlex.split(cv)
        self.cwd = ['--cwd', shlex.quote(f'{cwd}')] if cwd else list()
        self.context = context

    def _run(self, command):
        if self.context:
            context = shlex.split(self.context)
            command = '{} {}'.format(' '.join(context), shlex.quote(command))
        logger.info(f'Run command: {command}')
        try:
            reply = invoke.run(command, hide=True)
        except invoke.exceptions.UnexpectedExit as exc:
            raise ApiError(exc.result)
        except invoke.exceptions.Failure as exc:
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
        echo_params = ['echo', shlex.quote(json.dumps(params))]
        api = ['api3', shlex.quote(f'{entity}.{action}'), '--in=json']
        command = self.cv + self.cwd + api
        return '{} | {}'.format(' '.join(echo_params), ' '.join(command))


class ConsoleApiV4(BaseConsoleApi):
    VERSION = v4

    def _get_command(self, entity, action, params):
        api = ['api4', shlex.quote(f'{entity}.{action}')]
        params = [shlex.quote(json.dumps(params))] if params else list()
        command = self.cv + self.cwd + api + params
        return ' '.join(command)

