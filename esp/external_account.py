import uuid

from .resource import ESPResource


class ExternalAccount(ESPResource):

    @classmethod
    def create(cls, **kwargs):
        if 'external_id' not in kwargs:
            kwargs['external_id'] = str(uuid.uuid4())
        return super(ExternalAccount, cls).create(**kwargs)
