import logging
import json
from .errors import ApiError
from .errors import InvalidJSON


logger = logging.getLogger('civicrmapi')


class BaseAction:
    ENTITY = None
    ACTION = None

    def __init__(self, api):
        if not self.ENTITY or not self.ACTION:
            raise NotImplemented('ENTITY and ACTION must be defined.')
        self._api = api

    def __call__(self, params=None):
        """
        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.ENTITY, self.ACTION, params or dict())


class BaseEntity:
    ENTITY = None
    ACTIONS = list()

    def __init__(self, api):
        if not self.ENTITY:
            raise NotImplemented('ENTITY must be defined.')
        self._api = api
        self._add_actions()

    def _add_actions(self):
        for action in self.ACTIONS + self._api.VERSION.ACTIONS:
            if isinstance(action, str):
                action_name = action
                attrs = dict(ENTITY=self.ENTITY, ACTION=action)
                action_class = type(action, (BaseAction,), attrs)
            elif isinstance(action, type) and issubclass(action, BaseAction):
                action_name = action.__name__
                action_class = action
            else:
                msg = 'ACTIONS item must be string or subclass of BaseAction.'
                raise ValueError(msg)
            if not hasattr(self, action_name):
                setattr(self, action_name, action_class(self._api))

    def __call__(self, action, params=None):
        """
        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.ENTITY, action, params or dict())


class BaseApi:
    VERSION = None
    ENTITIES = list()

    def __init__(self):
        if not self.VERSION:
            raise NotImplemented('VERSION must be defined.')
        self._add_entities()

    def _add_entities(self):
        for entity in self.ENTITIES + self.VERSION.ENTITIES:
            if isinstance(entity, str):
                entity_name = entity
                entity_class = type(entity, (BaseEntity,), dict(ENTITY=entity))
            elif isinstance(entity, type) and issubclass(entity, BaseEntity):
                entity_name = entity.__name__
                entity_class = entity
            else:
                msg = 'ENTITIES item must be string or subclass of BaseEntity.'
                raise ValueError(msg)
            if not hasattr(self, entity_name):
                setattr(self, entity_name, entity_class(self))

    def __call__(self, entity, action, params=None):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: normalized api call result
        :raises RequestError: when the rest api could not be accessed
        :raises InvokeError: when the console api could not be accessed
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
