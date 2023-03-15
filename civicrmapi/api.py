import requests
import logging
import json
from . import v4
from .v4.base import BaseEntity


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


class BaseApi:
    def __init__(self):
        self._add_entities()

    def _add_entities(self):
        for entity in v4.ENTITIES:
            if hasattr(v4, entity):
                setattr(self, entity, getattr(v4, entity)(self))
            else:
                attrs = dict(ENTITY=entity)
                entity_class = type(entity, (BaseEntity,), attrs)
                setattr(self, entity, entity_class(self))

    def __call__(self, entity, action, params):
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
        logging.debug(f'Perform post request:')
        logging.debug(f'- url: {url}')
        logging.debug(f'- params: {params}')
        logging.debug(f'- headers: {headers}')
        logging.debug(f'- verify: {self.verify_ssl}')
        logging.debug(f'- timeout: {self.timeout}')

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
            logging.debug(f'Post request returned: {reply}')

        if not reply.status_code == 200:
            raise RestApiError(reply)

        try:
            result = json.loads(reply.text)
        except json.JSONDecodeError:
            raise RestApiError(reply)
        else:
            logging.debug(f'Decoded json: {result}')

        if result.get('is_error', False) or result.get('error_message', None):
            raise RestApiError(reply)
        else:
            return result


class RestApiV4(BaseRestApi):
    """
    Simple bindings for CiviCRM's RestApiv4.
    """
    def __call__(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        :raises HttpError: when the api could not be accessed
        :raises RestApiError: when the api call failed
        """
        logging.info(f'Perform api call: {entity}.{action} with {params}')
        url = self.base_url.strip('/') + '/civicrm/ajax/api4/'
        url += '{}/{}'.format(entity, action)
        headers = dict()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['X-Civi-Auth'] = 'Bearer {}'.format(self.api_key)
        params = dict(params=json.dumps(params))
        return super().__call__(url, params, headers)


class RestApiV3(BaseRestApi):
    """
    Simple bindings for CiviCRM's RestApiv3.
    """
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
        logging.info(f'Perform api call: {entity}.{action} with {params}')
        url = self.base_url.strip('/') + '/civicrm/ajax/rest'
        base_params = dict()
        base_params['api_key'] = self.api_key
        base_params['key'] = self.site_key
        base_params['entity'] = entity
        base_params['action'] = action
        base_params['json'] = json.dumps(params)
        return super().__call__(url, params)
