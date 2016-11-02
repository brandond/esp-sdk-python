# coding: utf-8
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging
import json

from .auth import ESPAuth, UnauthorizedError
from .packages import requests
from .settings import settings

logger = logging.getLogger(__name__)
session = requests.Session()


def make_endpoint(uri):
    url = '{}{}/{}'.format(settings.host, settings.api_prefix, uri)
    return url


def requester(url, request_type, headers={}, data=None):
    logging.debug('Making request to {}'.format(url))
    headers['User-Agent'] = settings.user_agent
    method = getattr(session, request_type)
    proxies = None
    if settings.http_proxy:
        proxies = [settings.http_proxy]
    response = method(
        url,
        data=data,
        headers=headers,
        auth=ESPAuth(access_key_id=settings.access_key_id,
                     secret_access_key=settings.secret_access_key),
        proxies=proxies)
    if response.status_code == 401:
        raise UnauthorizedError
    if logger.getEffectiveLevel() == logging.DEBUG:
        logger.debug('Response: {}'.format(json.dumps(response.json(),indent=4)))
    return response
