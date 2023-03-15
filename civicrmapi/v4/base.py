
class BaseEntity:
    """
    """
    ENTITY = 'fixme'
    ACTIONS = [
        'checkAccess',
        'getActions',
        'getFields',
        'get',
        'create',
        'update',
        'save',
        'delete',
        'replace',
    ]

    def __init__(self, api):
        self._api = api
        self._add_actions()

    def _add_actions(self):
        for action in self.ACTIONS:
            attrs = dict(
                ENTITY=self.ENTITY,
                ACTION=action)
            action_class = type(action, (BaseAction,), attrs)
            setattr(self, action, action_class(self._api))

    def __call__(self, action, params):
        return self._api(self.ENTITY, action, params)


class BaseAction:
    ENTITY = 'fixme'
    ACTION = 'fixme'

    def __init__(self, api):
        self._api = api

    def __call__(self, params):
        return self._api(self.ENTITY, self.ACTION, params)
