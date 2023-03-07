import requests
import json


class ApiError(Exception):
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


class CivicrmApi:
    """
    Simple bindings for CiviCRM's API (v3 and v4).
    """
    def __init__(self, url, api_key, site_key=None, htaccess=None, verify_ssl=True, timeout=None):
        """
        :param str url: CiviCRM's base-url
        :param str api_key: CiviCRM's api-key
        :param str site_key: CiviCRM's site-key - needed only for api-v3. (optional)
        :param dict htaccess: htaccess credentials with 'user' and 'pass' keys. (optional)
        :param bool verify_ssl: Verify SSL-certificate or not. Default is True. (optional)
        :param int timeout: Timeout in seconds. (optional)
        """
        self.base_url = 'https://' + url
        self.api_key = api_key
        self.site_key = site_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        if htaccess:
            auth_user = htaccess['user']
            auth_pass = htaccess['pass']
            self.auth = requests.auth.HTTPBasicAuth(auth_user, auth_pass)
        else:
            self.auth = None

    def call(self, *args):
        """
        Wrapper for :meth:`.callv4`.
        """
        return self.callv4(*args)

    def callv4(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        :raises HttpError: when the api could not be accessed
        :raises ApiError: when the api call failed
        """
        url = self.base_url.strip('/') + '/civicrm/ajax/api4/'
        url += '{}/{}'.format(entity, action)
        headers = dict()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        headers['X-Civi-Auth'] = 'Bearer {}'.format(self.api_key)
        params = dict(params=json.dumps(params))
        return self._call(url, params, headers)

    def callv3(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        :raises HttpError: when the api could not be accessed
        :raises ApiError: when the api call failed
        """
        url = self.base_url.strip('/') + '/civicrm/ajax/rest'
        base_params = dict()
        base_params['api_key'] = self.api_key
        base_params['key'] = self.site_key
        base_params['entity'] = entity
        base_params['action'] = action
        base_params['json'] = json.dumps(params)
        return self._call(url, base_params)

    def _call(self, url, params, headers=None):
        reply = requests.post(
            url,
            params=params,
            verify=self.verify_ssl,
            auth=self.auth,
            timeout=self.timeout,
            headers=headers)

        if not reply.status_code == 200:
            raise ApiError(reply)

        try:
            result = json.loads(reply.text)
        except json.JSONDecodeError:
            raise ApiError(reply)

        if result.get('is_error', False) or result.get('error_message', None):
            raise ApiError(reply)
        else:
            return result
