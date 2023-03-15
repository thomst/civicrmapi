import requests
import logging
import json
from . import v3
from . import v4
from .errors import RestApiError
from .errors import RestConnectionError


logger = logging.getLogger(__name__)


class BaseAction:
    ENTITY = None
    ACTION = None

    def __init__(self, api):
        self._api = api

    def __call__(self, params):
        """
        :param dict params: api call parameters
        :return dict: api call result
        """
        return self._api(self.ENTITY, self.ACTION, params)


class BaseEntity:
    ENTITY = None

    def __init__(self, api):
        self._api = api
        if api.VERSION:
            self._add_actions(api.VERSION)

    def _add_actions(self, version_mod):
        for action in version_mod.ACTIONS:
            if hasattr(self, action):
                continue
            else:
                attrs = dict(ENTITY=self.ENTITY, ACTION=action)
                action_class = type(action, (BaseAction,), attrs)
                setattr(self, action, action_class(self._api))

    def __call__(self, action, params):
        """
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        """
        return self._api(self.ENTITY, action, params)


class BaseApi:
    VERSION = None

    def __init__(self):
        if self.VERSION:
            self._add_entities(self.VERSION)

    def _add_entities(self, version_mod):
        for entity in version_mod.ENTITIES:
            if hasattr(version_mod, entity):
                setattr(self, entity, getattr(version_mod, entity)(self))
            else:
                attrs = dict(ENTITY=entity)
                entity_class = type(entity, (BaseEntity,), attrs)
                setattr(self, entity, entity_class(self))

    def __call__(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        """
        raise NotImplementedError


class BaseRestApi(BaseApi):
    def __init__(self, url, api_key, htaccess=None, verify_ssl=True, timeout=None):
        """
        :param str url: CiviCRM's base-url
        :param str api_key: CiviCRM's api-key
        :param dict htaccess: htaccess credentials with 'user' and 'pass' keys. (optional)
        :param bool verify_ssl: Verify SSL-certificate or not. Default is True. (optional)
        :param int timeout: Timeout in seconds. (optional)
        """
        super().__init__()
        self.base_url = url
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Setup basic-auth
        if htaccess:
            auth_user = htaccess['user']
            auth_pass = htaccess['pass']
            self.auth = requests.auth.HTTPBasicAuth(auth_user, auth_pass)
        else:
            self.auth = None

    def __call__(self, url, params, headers=None):
        """
        :param str url: rest api endpoint
        :param dict params: api call parameters
        :param dict headers: http headers
        :return dict: api call result
        :raises RestConnectionError: when the api could not be accessed
        :raises RestApiError: when the api call failed
        """
        logger.info(f'Perform post request: {url}')
        logger.debug(f'- params: {params}')
        logger.debug(f'- headers: {headers}')
        logger.debug(f'- verify: {self.verify_ssl}')
        logger.debug(f'- timeout: {self.timeout}')

        try:
            reply = requests.post(
                url,
                params=params,
                verify=self.verify_ssl,
                auth=self.auth,
                timeout=self.timeout,
                headers=headers)
        except requests.exceptions.RequestException as exc:
            raise RestConnectionError(exc)
        else:
            logger.info(f'Post request done: {reply}')
            logger.debug(f'- text: {reply.text}')

        if not reply.status_code == 200:
            raise RestApiError(reply)

        try:
            result = json.loads(reply.text)
        except json.JSONDecodeError:
            raise RestApiError(reply)
        else:
            logger.info(f'Valid json response.')
            logger.debug(f'Decoded json: {result}')

        if result.get('is_error', False) or result.get('error_message', None):
            raise RestApiError(reply)
        else:
            return result


class RestApiV3(BaseRestApi):
    """
    Simple bindings for CiviCRM's RestApiv3.
    """
    VERSION = v3

    def __init__(self, url, api_key, site_key, htaccess=None, verify_ssl=True, timeout=None):
        """
        :param str url: CiviCRM's base-url
        :param str api_key: CiviCRM's api-key
        :param str site_key: CiviCRM's api-site_key
        :param dict htaccess: htaccess credentials with 'user' and 'pass' keys. (optional)
        :param bool verify_ssl: Verify SSL-certificate or not. Default is True. (optional)
        :param int timeout: Timeout in seconds. (optional)
        """
        self.site_key = site_key
        super().__init__(url, api_key, htaccess, verify_ssl, timeout)

    def __call__(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        :raises HttpError: when the api could not be accessed
        :raises RestApiError: when the api call failed
        """
        logger.info(f'Perform api call: {entity}.{action} with {params}')
        url = self.base_url.strip('/') + '/civicrm/ajax/rest'
        base_params = dict()
        base_params['api_key'] = self.api_key
        base_params['key'] = self.site_key
        base_params['entity'] = entity
        base_params['action'] = action
        base_params['json'] = json.dumps(params)
        return super().__call__(url, params)


class RestApiV4(BaseRestApi):
    """
    Simple bindings for CiviCRM's RestApiv4.
    """
    VERSION = v4

    def __call__(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        :raises RestConnectionError: when the api could not be accessed
        :raises RestApiError: when the api call failed
        """
        logger.info(f'Perform api call: {entity}.{action} with {params}')
        url = self.base_url.strip('/') + '/civicrm/ajax/api4/'
        url += '{}/{}'.format(entity, action)
        headers = dict()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['X-Civi-Auth'] = 'Bearer {}'.format(self.api_key)
        params = dict(params=json.dumps(params))
        return super().__call__(url, params, headers)
