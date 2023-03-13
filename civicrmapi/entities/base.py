
class BaseEntity:
    ENTITY = 'fixme'

    def __init__(self, api):
        self.api = api

    def get(self, params):
        return self.api(self.ENTITY, 'get', params)

    def create(self, params):
        return self.api(self.ENTITY, 'create', params)

    def delete(self, params):
        return self.api(self.ENTITY, 'delete', params)
