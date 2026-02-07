import logging
import json
from . import v4
from .utils import dict_to_where_clause_list
from .errors import InvalidApiCall
from .errors import InvalidResponse


logger = logging.getLogger('civicrmapi')


class BaseAction:
    """
    Base class for CiviCRM API actions. Instances are callables performing api
    calls on the entity instance the class was initialized with.

    :param entity: entity instance
    :type entity: :class:`~.BaseEntity`

    :raises NotImplemented: when :attr:`~BaseAction.NAME` is not defined
    """
    NAME = None
    """
    Must be set by a subclass.
    """

    def __init__(self, entity):
        if not self.NAME:
            raise NotImplemented('NAME attribute must be set.')

        self._entity = entity

    def __call__(self, params=None):
        """
        Perform an api call with this action using its entity.

        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._entity(self.NAME, params or dict())


class BaseEntity:
    """
    Base class for CiviCRM entities. Instances are callables performing api
    calls with the api instance the class was initialized with.

    The api version's default actions are added automatically on initialization.
     (See :attr:`civicrmapi.v3.ACTIONS` and :attr:`civicrmapi.v4.ACTIONS`.)

    :param api: CiviCRM API instance
    :type api: :class:`~.BaseApi`

    :raises NotImplemented: when :attr:`~BaseEntity.NAME` is not defined
    """

    NAME = None
    """
    Must be set by a subclass.
    """

    def __init__(self, api):
        if not self.NAME:
            raise NotImplemented('NAME attribute must be set.')

        self._api = api
        self.add_default_actions()

    def add_action(self, action):
        """
        Add an action to this entity. The action parameter could either be a
        string or an Action class. If it's a string the :class:`~.BaseAction`
        class will be used using the string as its :attr:`~.BaseAction.NAME`
        parameter. The action will be become a callable attribute of the entity
        instance.

        :param action: action to perform for this entity
        :type action: str or :class:`~.BaseAction`
        """
        if isinstance(action, str):
            action = type(action, (BaseAction,), dict(NAME=action))
        setattr(self, action.NAME, action(self))

    def add_default_actions(self):
        """
        Add all actions defined in the version module of the api this entity was
        initialized with. Either :attr:`civicrmapi.v3.ACTIONS` or
        :attr:`civicrmapi.v4.ACTIONS`.
        """
        for action in self._api.VERSION.ACTIONS:
            self.add_action(action)

    def __call__(self, action, params=None):
        """
        Perform an api call on this entity using its api.

        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: api call result
        """
        return self._api(self.NAME, action, params or dict())


class BaseApi:
    """
    Base CiviCRM API class. Instances are callables performing api calls.

    This class will be initialized with the standard entities for the specific
    api version as instance attributes. (See :attr:`civicrmapi.v3.ENTITIES` and
    :attr:`civicrmapi.v4.ENTITIES`.)

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
        self.add_default_entities()

    def add_entity(self, entity):
        """
        Add an entity to this api. The entity parameter could either be a
        string or an Entity class. If it's a string the :class:`~.BaseEntity`
        class will be used using the string as its :attr:`~.BaseEntity.NAME`
        parameter. The entity will be become a callable attribute of the api
        instance.

        :param entity: entity to work with
        :type entity: str or :class:`~.BaseEntity`
        """
        if isinstance(entity, str):
            entity = type(entity, (BaseEntity,), dict(NAME=entity))
        setattr(self, entity.NAME, entity(self))

    def add_default_entities(self):
        """
        Add all entities defined in the version module of the api this entity was
        initialized with. Either :attr:`civicrmapi.v3.ENTITIES` or
        :attr:`civicrmapi.v4.ENTITIES`.
        """
        for entity in self.VERSION.ENTITIES:
            self.add_entity(entity)

    def __call__(self, entity, action, params=None):
        """
        Perform an api call.

        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters (optional)
        :return dict: normalized api call result
        """
        logger.info(f'Perform api call: {entity}.{action} with {params}')
        params = self._prepare_api_v4_parameters(action, params)
        response = self._perform_api_call(entity, action, params or dict())
        data = self._get_data_from_response(response)
        data = self._check_api_response(data)
        return self._normalize_result_values(data)

    def _prepare_api_v4_parameters(self, action, params):
        """
        The `API v3`_ and `API v4`_ have different formats for their api
        parameters. While the API v3 uses a flat dictonary with entity field
        parameters as well as meta informations like `limit` on the same level,
        the API v4 has a more structured and "sql-like" way to format the
        parameters - using keywords like `values`, `where` and `join`.

        .. _API v3: https://docs.civicrm.org/dev/en/latest/api/v3/usage/
        .. _API v4: https://docs.civicrm.org/dev/en/latest/api/v4/usage/

        For complex api calls you will need to lookup the api version's specific
        way on how to build your parameters dict. (Use the api explorer of a
        civicrm installation or just read the `docs`_.)

        .. _docs: https://docs.civicrm.org/dev/

        Simple api calls using only entity field parameters to fetch or create
        objects can be passed in as they are. This method will ensure that
        those parameters are prepared for the API v4 adding them to a `values`
        or `where` key.

        :param dict params: api parameters
        :return dict: prepared api parameters
        """
        if params and self.VERSION is v4:
            if action in ['get', 'delete'] and not 'where' in params:
                params = dict(where=dict_to_where_clause_list(params))
            elif action == 'create' and not 'values' in params:
                params = dict(values=params)
            elif action == 'update' and not 'where' in params and 'id' in params:
                id = params.pop('id')
                params = dict(where=dict_to_where_clause_list(dict(id=id)), values=params)
        return params

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

        :param response: response instance
        :type response: requests.Response or subprocess.CompletedProcess
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
