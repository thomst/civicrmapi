import logging
import json
from .errors import InvalidApiCall
from .errors import InvalidResponse


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
        """
        logger.info(f'Perform api call: {entity}.{action} with {params}')
        response = self._perform_api_call(entity, action, params or dict())
        data = self._get_data_from_response(response)
        data = self._check_api_response(data)
        return self._normalize_result_values(data)

    def _perform_api_call(self, entity, action, params):
        """
        Must be implemented by subclasses.

        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: api response data
        """
        raise NotImplemented

    def _get_data_from_response(self, response):
        """
        Takes a response object (either a requests response instance or a
        subprocess completed process instance) and try to parse it as json data.

        :param requests or subprocess response: response instance
        :return dict: api response data

        :raises InvalidResponse: when the response value is no valid json
        """
        value = response.text if hasattr(response, 'text') else response.stdout
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            raise InvalidResponse(response)
        else:
            return data

    def _check_api_response(self, data):
        """
        Process the json response from an api call.

        :param dict data: api response data
        :return dict: api response data

        :raises InvalidApiCall: when an error code is found in the api response
        """
        # Check api-v3 data for an api error.
        if isinstance(data, dict) and data.get('is_error', False):
            raise InvalidApiCall(data)
        # Check api-v4 data for an api error.
        elif isinstance(data, dict) and 'error_code' in data:
            raise InvalidApiCall(data)
        else:
            return data

    def _normalize_result_values(self, data):
        """
        Normalize api v3 and v4 response. Always return api results as a list.

        :param dict data: api response data
        :return dict: normalized api response data

        :raises InvalidResponse: when data has not the expected type or keys.
        """
        # Console api v4 returns values as list.
        if isinstance(data, list):
            return data
        # If we have a dict with values we return the values list instead.
        elif 'values' in data:
            return data['values']
        # Otherwise something is weird. We raise InvalidResponse exception.
        else:
            raise InvalidResponse(data)
