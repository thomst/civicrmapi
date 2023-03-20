import logging
import json
from .errors import ApiError
from .errors import InvalidJSON


logger = logging.getLogger('civicrmapi')


class BaseAction:
    ENTITY = None
    ACTION = None

    def __init__(self, api):
        self._api = api

    def __call__(self, params=None):
        """
        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.ENTITY, self.ACTION, params or dict())


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

    def __call__(self, action, params=None):
        """
        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.ENTITY, action, params or dict())


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

    def __call__(self, entity, action, params=None):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: api call result
        :raises RequestError: when the rest api could not be accessed
        :raises InvokeError: when the console api could not be accessed
        :raises HttpError: when the rest api return an error code
        :raises ApiError: when the api call failed
        :raises InvalidJson: when the response is invalid json code
        """
        logger.info(f'Perform api call: {entity}.{action} with {params}')
        result = self._perform_api_call(entity, action, params or dict())
        return self._process_json_result(result)

    def _perform_api_call(self, entity, action, params):
        raise NotImplemented

    def _process_json_result(self, json_response):
        """
        Called by __call__ to process json response.
        """
        try:
            result = json.loads(json_response)
        except json.JSONDecodeError as exc:
            raise InvalidJSON(exc)
        else:
            logger.info(f'Valid json response.')
            logger.debug(f'Decoded json: {result}')

        # Check api-v3 result for an api error.
        if isinstance(result, dict) and result.get('is_error', False):
            raise ApiError(result)
        # Check api-v4 result for an api error.
        elif isinstance(result, dict) and 'error_code' in result:
            raise ApiError(result)
        else:
            return self._normalize_result_values(result)

    def _normalize_result_values(self, result):
        # Console api v4 returns values as list.
        if isinstance(result, list):
            return result
        # If we have a dict with values we return only those.
        elif 'values' in result:
            return result['values']
        # Returning the result as dict as a fallback.
        # (That should not happen at all at all.)
        else:
            return result
