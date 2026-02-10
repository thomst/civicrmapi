import shlex
import json
import logging
import subprocess
from . import v3
from . import v4
from .base import BaseApi
from .errors import ApiError
from .errors import InvalidResponse


logger = logging.getLogger('civicrmapi')


class BaseCvApi(BaseApi):
    """
    Base class for cv API implementations. Subclasses must define the
    :attr:`~base.BaseApi.VERSION` attribute and implement the
    :meth:`._get_command` method.

    :raises NotImplemented: when :attr:`~base.BaseApi.VERSION` is not defined
    :raises NotImplemented: when :meth:`._get_command` is not implemented
    """

    # FIXME: Instead of using cwd, cv --cwd=/path/to/civicrm could be used directly
    # as cv parameter. There should be a hint within the docs.
    def __init__(self, cv='cv', cwd=None, context=None):
        super().__init__()
        self.cv = shlex.split(cv)
        self.cwd = ['--cwd', shlex.quote(f'{cwd}')] if cwd else list()
        self.context = shlex.split(context) if context else None

    def _get_command(self, entity, action, params):
        raise NotImplemented

    def _perform_api_call(self, entity, action, params):
        command = self._get_command(entity, action, params)

        # To run the command within a given context we tokenize the original
        # command and give it as positional argument to the context.
        if self.context:
            command = f'{" ".join(self.context)} {shlex.quote(command)}'

        # Log the command.
        logger.info(f'Run command: {command}')

        # Run the command.
        try:
            reply = subprocess.run(command, shell=True, capture_output=True, check=True, text=True)

        except subprocess.CalledProcessError as exc:
            # Unfortunately we have no chance to identify invalid api calls by
            # just the return code. So we need some further diggin.

            # An invalid api v4 call should be contain this pattern in stderr.
            if 'api4 [--in IN] [--out OUT]'.lower() in exc.stderr.lower():
                raise ApiError(exc.stderr)

            # If we have json formatted stdout with an is_error key we are sure
            # to have an invalid api v3 call which will be handled by the the
            # base api class.
            try:
                data = json.loads(exc.stdout)
                data['is_error']
            except (json.JSONDecodeError, KeyError):
                raise exc
            else:
                return data

        else:
            # Try to load reply as json formatted string.
            try:
                data = json.loads(reply.stdout)
            except json.JSONDecodeError:
                raise InvalidResponse(reply)
            else:
                return data


class CvApiV3(BaseCvApi):
    """
    Cv API bindings for CiviCRM APIv3.

    :param str cv: cv command
    :param str cwd: working directory for cv
    :param str context:
        If a context is given the original command will be tokenized and
        given to the context as positional argument. The simplest context
        migth be a 'sh -c'. But it could also be a docker-exec- or
        ssh-command to run the api call within a docker container or on a
        remote machine.
    """
    VERSION = v3

    def _get_command(self, entity, action, params):
        params['sequential'] = 1
        echo_params = ['echo', shlex.quote(json.dumps(params))]
        api = ['api3', shlex.quote(f'{entity}.{action}'), '--in=json']
        command = self.cv + self.cwd + api
        return '{} | {}'.format(' '.join(echo_params), ' '.join(command))


class CvApiV4(BaseCvApi):
    """
    Cv API bindings for CiviCRM APIv4.

    :param str cv: cv command
    :param str cwd: working directory for cv
    :param str context:
        If a context is given the original command will be tokenized and
        given to the context as positional argument. The simplest context
        migth be a 'sh -c'. But it could also be a docker-exec- or
        ssh-command to run the api call within a docker container or on a
        remote machine.
    """
    VERSION = v4

    def _get_command(self, entity, action, params):
        api = ['api4', shlex.quote(f'{entity}.{action}')]
        params = [shlex.quote(json.dumps(params))] if params else list()
        command = self.cv + self.cwd + api + params
        return ' '.join(command)

