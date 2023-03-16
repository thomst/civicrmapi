

class BaseAction:
    ENTITY = None
    ACTION = None

    def __init__(self, api):
        self._api = api

    def __call__(self, params):
        """
        :param dict params: api call parameters
        :return dict: api call result
        """
        return self._api(self.ENTITY, self.ACTION, params)


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

    def __call__(self, action, params):
        """
        :param str action: api call action
        :param dict params: api call parameters
        :return dict: api call result
        """
        return self._api(self.ENTITY, action, params)


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

    def __call__(self, entity, action, params):
        """
        :param str entity: CiviCRM-entitiy
        :param str action: api call action
        :param dict params: api call parameters
        :raises NotImplementedError: always
        """
        raise NotImplementedError
