import importlib
import json

from .sdk import requester, make_endpoint
from .packages import six
from .utilities import (pluralize,
                        singularize,
                        titlecase_to_underscore,
                        underscore_to_titlecase)
from .packages.six.moves.urllib.parse import urlencode

GET_REQUEST = 'get'
PATCH_REQUEST = 'patch'
POST_REQUEST = 'post'
PUT_REQUEST = 'put'
DELETE_REQUEST = 'delete'

# list of available predicates for searching and filtering
PREDICATES = ('sorts', 'm', 'eq', 'eq_any', 'eq_all', 'not_eq', 'not_eq_any',
              'not_eq_all', 'matches', 'matches_any', 'matches_all',
              'does_not_match', 'does_not_match_any', 'does_not_match_all',
              'lt', 'lt_any', 'lt_all', 'lteq', 'lteq_any', 'lteq_all', 'gt',
              'gt_any', 'gt_all', 'gteq', 'gteq_any', 'gteq_all', 'in',
              'in_any', 'in_all', 'not_in', 'not_in_any', 'not_in_all', 'cont',
              'cont_any', 'cont_all', 'not_cont', 'not_cont_any',
              'not_cont_all', 'start', 'start_any', 'start_all', 'not_start',
              'not_start_any', 'not_start_all', 'end', 'end_any', 'end_all',
              'not_end', 'not_end_any', 'not_end_all', 'true', 'false',
              'present', 'blank', 'null', 'not_null')


class ObjectMismatchError(Exception):
    pass


class RelationshipDoesNotExist(Exception):
    pass


class PageError(Exception):
    pass


class DataMissingError(Exception):
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

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, idx):
        return self.elements[idx]

    def _parse_links(self, links):
        if 'self' in links:
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
        if not self._next:
            raise PageError('No next page')
        return self.klass.find(endpoint=self._next)

    def prev_page(self):
        if not self._prev:
            raise PageError('No previous page')
        return self.klass.find(endpoint=self._prev)

    def first_page(self):
        if not self._first:
            raise PageError('No first page')
        return self.klass.find(endpoint=self._first)

    def last_page(self):
        if not self._last:
            raise PageError('No last page')
        return self.klass.find(endpoint=self._last)


def find_class_for_resource(name):
    """
    Takes a singular resource name and returns the class object for it

    :param name: name of the resource in singular form (e.g report, alert)
    :type name: string
    """
    name = name.lower()  # always make sure it's lowercase
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
        self._value = None

    def fetch(self):
        """
        Memoized function that stored raw results in self._value
        """
        if not self._value:
            response = requester(self.endpoint, GET_REQUEST)
            if response.status_code != 200:
                response.raise_for_status()
                data = response.json()
                if isinstance(data['data'], list):
                    self._value = PaginatedCollection(self.res_class, data)
                else:
                    self._value = self.res_class(data['data'])
                    return self._value

    def reload(self):
        self._cached_collection = None


class ESPMeta(type):

    def __new__(cls, name, bases, dct):
        dct['plural_name'] = pluralize(titlecase_to_underscore(name))
        dct['singular_name'] = singularize(titlecase_to_underscore(name))
        return super(ESPMeta, cls).__new__(cls, name, bases, dct)


class ESPResource(six.with_metaclass(ESPMeta, object)):

    def __init__(self, data=None, errors=None):
        self.errors = None
        self._attributes = None
        if errors:
            self.errors = errors
        elif data:
            if data['type'] != self.plural_name:
                raise ObjectMismatchError('{} cannot store data for {}'.format(
                    self.plural_name, data['type']))

            # type and id are python keywords, so we have to append _ to them
            # to avoid collisions
            self.id_ = data['id']
            self.type_ = data['type']
            self._attributes = {}

            for k, v in data['attributes'].items():
                self._attributes[k] = v

            if 'relationships' in data:
                for k, v in data['relationships'].items():
                    self._attributes[k] = CachedRelationship(singularize(k), v)
            else:
                raise DataMissingError(
                    'Resource instances require `data` or `errors` to init')
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
    def _make_request(cls, endpoint, request_type, data=None):
        return requester(endpoint, request_type, data=data)

    @classmethod
    def _resource_path(cls, id, extra=[], querystring=None):
        return cls._make_path([cls.plural_name, id], extra, querystring)

    @classmethod
    def _resource_collection_path(cls, extra=[], querystring=None):
        return cls._make_path([cls.plural_name], extra, querystring)

    @classmethod
    def _make_path(cls, path, extra=[], querystring=None):
        if not isinstance(extra, list):
            raise TypeError('extra needs to be a list')
        path.extend(extra)
        path = '/'.join([str(item) for item in path])
        if querystring:
            path = path + '?' + querystring
        return path

    @classmethod
    def find(cls, id=None, endpoint=None):
        if not id:
            return cls._all(endpoint=endpoint)
        return cls._get(id, endpoint=endpoint)

    @classmethod
    def _get(cls, id, endpoint=None):
        if not endpoint:
            endpoint = make_endpoint(cls._resource_path(id))
            response = cls._make_request(endpoint, GET_REQUEST)
            data = response.json()
            return cls(data['data'])

    @classmethod
    def _all(cls, endpoint=None, filter=None):
        if not endpoint:
            endpoint = make_endpoint(
                cls._resource_collection_path(querystring=filter))
            response = cls._make_request(endpoint, GET_REQUEST)
            data = response.json()
            return PaginatedCollection(cls, data)

    @classmethod
    def where(cls, **clauses):
        filters = {}
        for k, v in six.iteritems(clauses):
            attr = k
            if any(i in k for i in PREDICATES):
                attr = k
            else:
                if isinstance(v, list):
                    attr = '{}_in'.format(k)
                else:
                    attr = '{}_eq'.format(k)
            filters['filter[{}]'.format(attr)] = v
        querystring = urlencode(filters)
        return cls._all(filter=querystring)

    @classmethod
    def create(cls, **kwargs):
        """
        Create a new resource in ESP.

        :param kwargs: arbitrary attributes relating to this resource. See API
        docs for more information about what is required.

        :returns: a new instance of the resource class
        """
        endpoint = make_endpoint(cls._resource_collection_path())
        payload = {
            'type': cls.plural_name,
            'attributes': kwargs
        }

        serialized = json.dumps({'data': payload})

        response = cls._make_request(endpoint, POST_REQUEST, data=serialized)
        data = response.json()
        if response.status_code == 422:
            return cls(errors=data['errors'])
        return cls(data['data'])

    def to_json(self):
        """
        This is the method that will convert class data to a json string

        :returns: string
        """
        return json.dumps({'data': self.to_dict()})

    def to_dict(self):
        """
        This is the method that will convert class data to a dict

        :returns: dict
        """
        attrs = {k: v for k, v in self._attributes.items()
                 if not isinstance(v, CachedRelationship)}
        return {
            'id': self.id_,
            'type': self.type_,
            'attributes': attrs
        }

    def save(self):
        """
        Save (update) a resource in ESP.

        :returns: a new instance of the resource type with updates data
        """
        endpoint = make_endpoint(self._resource_path(self.id_))
        response = self._make_request(endpoint,
                                      PATCH_REQUEST,
                                      data=self.to_json())
        data = response.json()
        cls = find_class_for_resource(self.singular_name)
        if response.status_code == 422:
            return cls(errors=data['errors'])
        return cls(data['data'])

    def destroy(self):
        """
        Destroy (delete) a resource in ESP.

        :returns: None on success and a new instance of the resource class with
        the errors attribute populated on error.
        """
        endpoint = make_endpoint(self._resource_path(self.id_))
        response = self._make_request(endpoint,
                                      DELETE_REQUEST)
        if response.status_code == 422:
            data = response.json()
            cls = find_class_for_resource(self.singular_name)
            return cls(errors=data['errors'])
