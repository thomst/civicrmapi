import requests
import logging
import json
from . import v3
from . import v4
from .base import BaseApi
from .errors import InvalidApiCall


logger = logging.getLogger('civicrmapi')


class BaseRestApi(BaseApi):
    """
    Base class for CiviCRM Rest API implementations. Subclasses must define the
    :attr:`~base.BaseApi.VERSION` attribute and implement the :meth:`._perform_api_call` method.

    :raises NotImplemented: when :attr:`~base.BaseApi.VERSION` is not defined
    :raises NotImplemented: when :meth:`._perform_api_call` is not implemented
    """
    def __init__(self, url, htaccess=None, verify_ssl=True, timeout=None, headers=None):
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

    def _perform_post_request(self, params, url_path=None):
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
                headers=self.headers
                )

        # Any http request related error like invalid url or network issues.
        except requests.exceptions.RequestException:
            raise

        else:
            logger.info(f'Request result: {reply}')

            # ApiV4 uses status code 401 for invalid credentials.
            if reply.status_code == 401:
                raise InvalidApiCall(reply.text)

            else:
                return reply

    def _perform_api_call(self, entity, action, params):
        raise NotImplemented


class RestApiV3(BaseRestApi):
    """
    API bindings for CiviCRM's RestApiv3.

    :param str url: CiviCRM's base-url
    :param str api_key: CiviCRM's api-key
    :param str site_key: CiviCRM's api-site_key
    :param dict htaccess: htaccess credentials with 'user' and 'pass' keys. (optional)
    :param bool verify_ssl: Verify SSL-certificate or not. Default is True. (optional)
    :param int timeout: Timeout in seconds. (optional)
    """
    VERSION = v3

    def __init__(self, url, api_key, site_key, htaccess=None, verify_ssl=True, timeout=None):
        self.api_key = api_key
        self.site_key = site_key
        url = url.rstrip('/') + '/civicrm/ajax/rest'
        super().__init__(url, htaccess, verify_ssl, timeout)

    def _perform_api_call(self, entity, action, params):
        params['sequential'] = params.get('sequential', 1)
        base_params = dict()
        base_params['api_key'] = self.api_key
        base_params['key'] = self.site_key
        base_params['entity'] = entity
        base_params['action'] = action
        base_params['json'] = json.dumps(params)
        return self._perform_post_request(base_params)


class RestApiV4(BaseRestApi):
    """
    API bindings for CiviCRM's RestApiv4.

    :param str url: CiviCRM's base-url
    :param str api_key: CiviCRM's api-key
    :param dict htaccess: htaccess credentials with 'user' and 'pass' keys. (optional)
    :param bool verify_ssl: Verify SSL-certificate or not. Default is True. (optional)
    :param int timeout: Timeout in seconds. (optional)
    """
    VERSION = v4

    def __init__(self, url, api_key, htaccess=None, verify_ssl=True, timeout=None):
        self.api_key = api_key
        url = url.rstrip('/') + '/civicrm/ajax/api4/'
        headers = dict()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['X-Civi-Auth'] = 'Bearer {}'.format(self.api_key)
        super().__init__(url, htaccess, verify_ssl, timeout, headers)

    def _perform_api_call(self, entity, action, params):
        params = dict(params=json.dumps(params))
        url_path = f'{entity}/{action}'
        return self._perform_post_request(params, url_path)