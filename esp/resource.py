import importlib

from .sdk import requester, make_endpoint
from .packages import six
from .utilities import (pluralize,
                        singularize,
                        titlecase_to_underscore,
                        underscore_to_titlecase)

GET_REQUEST = 'get'
POST_REQUEST = 'post'
PUT_REQUEST = 'put'
DELETE_REQUEST = 'delete'


class ObjectMismatchError(Exception):
    pass


class RelationshipDoesNotExist(Exception):
    pass


class PaginatedCollection(object):

    def __init__(self, resource_class, data):
        self.klass = resource_class
        self.elements = [resource_class(res) for res in data['data']]
        self._first = None
        self._current = None
        self._next = None
        self._prev = None
        self._last = None
        if 'links' in data:
            self._parse_links(data['links'])

    def _parse_links(self, links):
        self._current = links['self']
        if 'first' in links:
            self._first = links['first']
        if 'last' in links:
            self._last = links['last']
        if 'next' in links:
            self._next = links['next']
        if 'prev' in links:
            self._prev = links['prev']

    def next_page(self):
        pass

    def prev_page(self):
        pass

    def first_page(self):
        pass

    def last_page(self):
        pass


def find_class_for_resource(name):
    """
    Takes a singular resource name and returns the class object for it

    :param name: name of the resource in singular form (e.g report, alert)
    :type name: string
    """
    package = '.'.join(__name__.split('.')[:-1])
    module = importlib.import_module('.{}'.format(name), package=package)
    return getattr(module, underscore_to_titlecase(name))


class CachedRelationship(object):
    """
    Used to store the results of an API call for relationship data
    """

    def __init__(self, name, rel):
        self.res_class = find_class_for_resource(name)
        self.endpoint = rel['links']['related']
        self._collection = None

    def fetch(self):
        """
        Memoized function that stored raw results in self._collection
        """
        if not self._collection:
            response = requester(self.endpoint, GET_REQUEST)
            if response.status_code != 200:
                response.raise_for_status()
            data = response.json()
            self._collection = PaginatedCollection(self.res_class, data)
        return self._collection

    def reload(self):
        self._cached_collection = None


class ESPMeta(type):

    def __new__(cls, name, bases, dct):
        dct['resource_name'] = pluralize(titlecase_to_underscore(name))
        return super(ESPMeta, cls).__new__(cls, name, bases, dct)


class ESPResource(six.with_metaclass(ESPMeta, object)):

    def __init__(self, data):
        if data['type'] != self.resource_name:
            raise ObjectMismatchError('{} cannot store data for {}'.format(
                self.resource_name, data['type']))

        self._attributes = {}
        self._attributes['type'] = data['type']
        self._attributes['id'] = data['id']

        for k, v in data['attributes'].items():
            self._attributes[k] = v

        for k, v in data['relationships'].items():
            self._attributes[k] = CachedRelationship(singularize(k), v)
        self.init_complete = True

    def __getattr__(self, attr):
        if '_attributes' in self.__dict__:
            if attr in self._attributes:
                val = self._attributes[attr]
                if isinstance(val, CachedRelationship):
                    return val.fetch()
                return val
        raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if 'init_complete' in self.__dict__:
            if attr in self.__dict__ or getattr(self.__class__, attr, None):
                object.__setattr__(self, attr, value)
            else:
                self._attributes[attr] = value
        else:
            object.__setattr__(self, attr, value)

    @classmethod
    def _make_request(cls, endpoint, request_type):
        return requester(endpoint, request_type)

    @classmethod
    def _resource_path(cls, id):
        return '{name}/{id}'.format(name=pluralize(cls.__name__), id=id)

    @classmethod
    def _resource_collection_path(cls):
        return '{name}'.format(name=pluralize(cls.__name__))

    @classmethod
    def find(cls, id=None):
        if not id:
            return cls._all()
        return cls._get(id)

    @classmethod
    def _get(cls, id):
        endpoint = make_endpoint(cls._resource_path(id))
        response = cls._make_request(endpoint, GET_REQUEST)
        if response.status_code == 200:
            data = response.json()
            return data['data']
        return None

    @classmethod
    def _all(cls):
        endpoint = make_endpoint(cls._resource_collection_path())
        response = cls._make_request(endpoint, GET_REQUEST)
        if response.status_code == 200:
            data = response.json()
            return PaginatedCollection(cls, data)

    @classmethod
    def create(**kwargs):
        pass

    def to_json(self):
        """
        This is the method that will convert class data to a json string
        """

    def save(self):
        raise NotImplementedError
