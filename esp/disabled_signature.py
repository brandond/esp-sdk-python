from .signature import Signature

class DisabledSignature(Signature):

    resource_class = 'signatures'

    @classmethod
    def create(cls):
        raise NotImplementedError('DisabledSignature does not implement a create method')

    def save(self):
        raise NotImplementedError('DisabledSignature does not implement a save method')

    def destroy(self):
        raise NotImplementedError('DisabledSignature does not implement a destroy method')

    def update(self):
        raise NotImplementedError('DisabledSignature does not implement an update method')
