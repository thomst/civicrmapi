import requests
import logging
import json
from . import v3
from . import v4
from .base import BaseApi
from .errors import RestApiError
from .errors import RestConnectionError


logger = logging.getLogger(__name__)


class BaseRestApi(BaseApi):
    def __init__(self, url, htaccess=None, verify_ssl=True, timeout=None, headers=None):
        """
        :param str url: rest api endoint
        :param dict htaccess: htaccess credentials with 'user' and 'pass' keys. (optional)
        :param bool verify_ssl: Verify SSL-certificate or not. Default is True. (optional)
        :param int timeout: Timeout in seconds. (optional)
        :param dict headers: HTTP headers. (optional)
        """
        super().__init__()
        self.url = url
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.headers = headers

        # Setup basic-auth
        if htaccess:
            auth_user = htaccess['user']
            auth_pass = htaccess['pass']
            self.auth = requests.auth.HTTPBasicAuth(auth_user, auth_pass)
        else:
            self.auth = None

    def __call__(self, params, url_path=None):
        """
        :param dict params: api call parameters
        :return dict: api call result
        :raises RestConnectionError: when the api could not be accessed
        :raises RestApiError: when the api call failed
        """
        if url_path:
            url = '{}/{}'.format(self.url.rstrip('/'), url_path.lstrip('/'))
        else:
            url = self.url
        logger.info(f'Perform post request: {url}')
        logger.debug(f'- params: {params}')
        logger.debug(f'- headers: {self.headers}')
        logger.debug(f'- verify: {self.verify_ssl}')
        logger.debug(f'- timeout: {self.timeout}')

        try:
            reply = requests.post(
                url,
                params=params,
                verify=self.verify_ssl,
                auth=self.auth,
                timeout=self.timeout,
                headers=self.headers)
        except requests.exceptions.RequestException as exc:
            raise RestConnectionError(exc)
        else:
            logger.info(f'Post request done: {reply}')
            logger.debug(f'- text: {reply.text}')

        if not reply.status_code == 200:
            raise RestApiError(reply)

        return self._process_json_result(reply.text)


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
        self.api_key = api_key
        self.site_key = site_key
        url = url.rstrip('/') + '/civicrm/ajax/rest'
        super().__init__(url, htaccess, verify_ssl, timeout)

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
        base_params = dict()
        base_params['api_key'] = self.api_key
        base_params['key'] = self.site_key
        base_params['entity'] = entity
        base_params['action'] = action
        base_params['json'] = json.dumps(params)
        return super().__call__(params)


class RestApiV4(BaseRestApi):
    """
    Simple bindings for CiviCRM's RestApiv4.
    """
    VERSION = v4

    def __init__(self, url, api_key, htaccess=None, verify_ssl=True, timeout=None):
        """
        :param str url: CiviCRM's base-url
        :param str api_key: CiviCRM's api-key
        :param dict htaccess: htaccess credentials with 'user' and 'pass' keys. (optional)
        :param bool verify_ssl: Verify SSL-certificate or not. Default is True. (optional)
        :param int timeout: Timeout in seconds. (optional)
        """
        self.api_key = api_key
        url = url.rstrip('/') + '/civicrm/ajax/api4/'
        headers = dict()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['X-Civi-Auth'] = 'Bearer {}'.format(self.api_key)
        super().__init__(url, htaccess, verify_ssl, timeout, headers)

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
        params = dict(params=json.dumps(params))
        url_path = f'{entity}/{action}'
        return super().__call__(params, url_path)