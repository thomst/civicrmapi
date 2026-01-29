import logging
import json
from .errors import ApiError
from .errors import InvalidJSON


logger = logging.getLogger('civicrmapi')


class BaseAction:
    """
    Base class for CiviCRM API actions. Subclasses must define the
    :attr:`.ENTITY` and :attr:`.ACTION` attributes.

    By calling an instance of this class the specific api call will be
    performed. See :meth:`.__call__`.

    :param api: CiviCRM API instance
    :type api: :class:`~civicrmapi.base.BaseApi`
    :raises NotImplemented: when ENTITY is not defined
    :raises NotImplemented: when ACTION is not defined
    """
    ENTITY = None
    """
    The CiviCRM entity this action operates on. Set by a subclass of
    :class:`~.BaseAction`.
    """
    ACTION = None
    """
    The action name. Set by a subclass of :class:`~.BaseAction`.
    """

    def __init__(self, api):
        if not self.ENTITY or not self.ACTION:
            raise NotImplemented('ENTITY and ACTION must be defined.')
        self._api = api

    def __call__(self, params=None):
        """
        Perform the api call.

        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.ENTITY, self.ACTION, params or dict())


class BaseEntity:
    """
    Base class for CiviCRM entities. Subclasses must define the :attr:`.ENTITY`
    attribute.

    This class will be initialized with all default actions defined for the
    specific api version as attributes. By setting the :attr:`.ACTIONS` attribute
    extra actions can be added.

    By calling an instance of this class the specific api call will be
    performed. See :meth:`.__call__`.

    :param api: CiviCRM API instance
    :type api: :class:`~civicrmapi.base.BaseApi`
    :raises NotImplemented: when ENTITY is not defined
    """

    ENTITY = None
    """
    The entity name. Set by a subclass of :class:`~.BaseEntity`.
    """
    ACTIONS = list()
    """
    List of extra api actions for this entity. Set by a subclass of
    :class:`~.BaseEntity`.
    """

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
        Perform an api call on this entity.

        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.ENTITY, action, params or dict())


class BaseApi:
    """
    Base CiviCRM API class. Subclasses must define the :attr:`.VERSION`
    attribute and overwrite the :meth:`._perform_api_call` method.

    This class will be initialized with all entities defined for its api version
    (either :mod:`~civicrmapi.api_v3` or :mod:`~civicrmapi.api_v4`) added as
    attributes. Use the :attr:`.ENTITIES` attribute to add extra entities.

    By calling an instance of this class the specific api call will be
    performed. See :meth:`.__call__`.

    :raises NotImplemented: when VERSION is not defined
    :raises NotImplemented: when :meth:`._perform_api_call` is not implemented
    """

    VERSION = None
    """
    The CiviCRM API version. Either :mod:`~civicrmapi.api_v3` or
    :mod:`~civicrmapi.api_v4`. Must be set by a subclass of :class:`~.BaseApi`.
    """
    ENTITIES = list()
    """
    List of extra entities this api should work on.
    """

    # FIXME: Add standard entities in __new__(), while extra entities in __init__()?
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
                # FIXME: First try to use entity.ENTITY attribute.
                entity_name = entity.__name__
                entity_class = entity
            else:
                msg = 'ENTITIES item must be string or subclass of BaseEntity.'
                raise ValueError(msg)

            # Avoid overwriting existing entities.
            # FIXME: Transform entity name into snake case?
            if not hasattr(self, entity_name):
                setattr(self, entity_name, entity_class(self))

    def __call__(self, entity, action, params=None):
        """
        Perform an api call.

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
        """
        Must be implemented by subclasses.
        """
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
        # (That should not happen at all.)
        else:
            return result
