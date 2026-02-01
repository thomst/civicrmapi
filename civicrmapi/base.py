import logging
import json
from .errors import ApiError
from .errors import InvalidJSON


logger = logging.getLogger('civicrmapi')


class BaseAction:
    """
    Base class for CiviCRM API actions. Subclasses must define the
    :attr:`~BaseAction.ENTITY` and :attr:`~BaseAction.ACTION` attributes.

    By calling an instance of this class the specific api call will be
    performed. See :meth:`~BaseAction.__call__`.

    :param api: CiviCRM API instance
    :type api: :class:`~civicrmapi.base.BaseApi`
    :raises NotImplemented: when :attr:`~BaseAction.ENTITY` is not defined
    :raises NotImplemented: when :attr:`~BaseAction.ACTION` is not defined
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
        self._api = api

        # Raise NotImplemented if ENTITY or ACTIONis not defined.
        if not self.ENTITY or not self.ACTION:
            raise NotImplemented('ENTITY and ACTION must be defined.')

    def __call__(self, params=None):
        """
        Perform the api call.

        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.ENTITY, self.ACTION, params or dict())


class BaseEntity:
    """
    Base class for CiviCRM entities. Subclasses must define the
    :attr:`~BaseEntity.ENTITY` attribute.

    This class will be initialized with all default actions defined for the
    specific api version as attributes.

    By calling an instance of this class the specific api call will be
    performed. See :meth:`~BaseEntity.__call__`.

    :param api: CiviCRM API instance
    :type api: :class:`~civicrmapi.base.BaseApi`
    :raises NotImplemented: when :attr:`~BaseEntity.ENTITY` is not defined
    """

    ENTITY = None
    """
    The entity name. Set by a subclass of :class:`~.BaseEntity`.
    """

    def __init__(self, api):
        self._api = api

        # Raise NotImplemented if ENTITY is not defined.
        if not self.ENTITY:
            raise NotImplemented('ENTITY must be defined.')

        # Add default actions defined in the api version module.
        for action_name in self._api.VERSION.ACTIONS:
            attrs = dict(ENTITY=self.ENTITY, ACTION=action_name)
            action_class = type(action_name, (BaseAction,), attrs)
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
    Base CiviCRM API class. Subclasses must define the :attr:`~BaseApi.VERSION`
    attribute and overwrite the :meth:`~BaseApi._perform_api_call` method.

    This class will be initialized with the standard entities for the specific
    api version as instance attributes. (See :mod:`~civicrmapi.v3` and
    :mod:`~civicrmapi.v4`.)

    By calling an instance of this class the specific api call will be
    performed. See :meth:`~BaseApi.__call__`.

    :raises NotImplemented: when :attr:`~BaseApi.VERSION` is not defined
    :raises NotImplemented: when :meth:`._perform_api_call` is not implemented
    """

    VERSION = None
    """
    The CiviCRM API version. Use either :mod:`~civicrmapi.v3` or
    :mod:`~civicrmapi.v4` in your subclass.
    """

    # FIXME: Add standard entities in __new__(), while extra entities in __init__()?
    def __init__(self):
        # Raise NotImplemented if VERSION is not defined.
        if not self.VERSION:
            raise NotImplemented('VERSION must be defined.')

        # Add default entities defined in the api version module.
        for entity in self.VERSION.ENTITIES:
            entity_class = type(entity, (BaseEntity,), dict(ENTITY=entity))
            setattr(self, entity, entity_class(self))

    def __call__(self, entity, action, params=None):
        """
        Perform an api call.

        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: normalized api call result

        :raises:
            - :class:`~civicrmapi.errors.RequestError`: when the rest api could not be accessed
            - :class:`~civicrmapi.errors.SubprocessError`: when the console api could not be accessed
            - :class:`~civicrmapi.errors.ApiError`: when the api call failed
            - :class:`~civicrmapi.errors.InvalidJSON`: when the response is invalid json code
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
