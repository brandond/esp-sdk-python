from .external_account import ExternalAccount


# some API responses return the external account namespaced as credential in the
# relationships field so I'm creating this hack to navigate around that issue.
class Credential(ExternalAccount):

    resource_type = 'external_accounts'
