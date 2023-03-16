import invoke
import shlex
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

        if self.VERSION == v3:
            self.version = 'api3'
        elif self.VERSION == v4:
            self.version = 'api4'
        else:
            raise NotImplementedError('VERSION must be defined.')

    def _run(self, command):
        try:
            reply = invoke.run(command)
        except Exception as exc:
            raise InvokeError(exc)
        else:
            logger.info(f'Running command finished [{reply.return_code}]')
            logger.debug(f'- stdout: {reply.stdout}')
            if reply.stderr:
                logger.warning(f'stderr: {reply.stderr}')
            return reply

    def _get_command(self, entity, action, params):
        cd_cwd = ['cd', f'{self.cwd}']
        if isinstance(params, str):
            params = shlex.split(params)
        if isinstance(self.cv, str):
            cv = shlex.split(self.cv)
        api_call = cv + [self.version, f'{entity}.{action}'] + params
        return shlex.join(cd_cwd) + ' && ' + shlex.join(api_call)

    def __call__(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        :raises InvokeError: when the api could not be accessed
        :raises ApiError: when the api call failed
        :raises InvalidJson: when the response is invalid json code
        """
        command = self._get_command(entity, action, params)
        logger.info(f'Run command: {command}')
        reply = self._run(command)
        return self._process_json_result(reply.stdout)


class ConsoleApiV3(BaseConsoleApi):
    VERSION = v3


class ConsoleApiV4(BaseConsoleApi):
    VERSION = v4
