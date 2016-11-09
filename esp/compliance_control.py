from .resource import ESPResource


class ComplianceControl(ESPResource):

    @classmethod
    def create(cls):
        raise NotImplementedError('Role does not implement a create method')

    def save(self):
        raise NotImplementedError('Role does not implement a save method')

    def destroy(self):
        raise NotImplementedError('Role does not implement a destroy method')
