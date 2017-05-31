import uuid

from .resource import ESPResource


class ExternalAccount(ESPResource):

    @classmethod
    def create(cls, **kwargs):
        if 'external_id' not in kwargs:
            kwargs['external_id'] = str(uuid.uuid4())
        return super(ExternalAccount, cls).create(**kwargs)


# some API responses return the external account namespaced as credential in the
# relationships field so I'm creating this hack to navigate around that issue.
class Credential(ExternalAccount):

    resource_type = 'external_accounts'
