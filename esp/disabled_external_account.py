from .external_account import ExternalAccount

# Relationship mapping class. Signatures have a disabled_external_accounts
# attribute that references accounts on which that signature is disabled.
class DisabledExternalAccount(ExternalAccount):

    resource_type = 'external_accounts'

    @classmethod
    def create(cls):
        raise NotImplementedError('DisabledExternalAccount does not implement a create method')

    def save(self):
        raise NotImplementedError('DisabledExternalAccount does not implement a save method')

    def destroy(self):
        raise NotImplementedError('DisabledExternalAccount does not implement a destroy method')

    def update(self):
        raise NotImplementedError('DisabledExternalAccount does not implement an update method')
