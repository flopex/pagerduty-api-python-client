"""Helpful mixins for PagerDuty entity classes."""
import logging

import ujson as json
import requests

from pypd.errors import (BadRequest, UnknownError, InvalidResponse,
                         InvalidHeaders)


CONTENT_TYPE = 'application/vnd.pagerduty+json;version=2'
AUTH_TEMPLATE = 'Token token={0}'
BASIC_AUTH_TEMPLATE = 'Basic {0}'


class ClientMixin(object):
    api_key = None
    base_url = None

    def __init__(self, api_key=None, base_url=None):
        # if no api key is provided try to get one from the packages api_key
        if api_key is None:
            from pypd import api_key
            self.api_key = api_key

        if base_url is None:
            from pypd import base_url
            self.base_url = base_url

        # sanitize the endpoint name incase people make mistakes
        if self.endpoint.endswith('/'):
            logging.warn('Endpoints should not end with a trailing slash, %s',
                         self.__class__)
            self.endpoint = self.endpoint[:-1]

    def _handle_response(self, response):
        if response.status_code == 404:
            response.raise_for_status()
        elif response.status_code / 100 == 4:
            raise BadRequest(response.status_code, response.text)
        elif response.status_code / 100 != 2:
            print dir(response.raw)
            print response.raw.getheaders()
            raise UnknownError(response.status_code, response.text)

        if not response.text:
            return None

        try:
            response = json.loads(response.text)
        except:
            raise InvalidResponse(response.text)

        return response

    def _do_request(self, requests_method, *args, **kwargs):
        """
        Modularized because API was broken.

        Need to be able to inject Mocked response objects here.
        """
        return requests_method(*args, **kwargs)

    def request(self, method='GET', endpoint='', query_params=None,
                data=None, add_headers=None, headers=None,):
        auth = 'Token token={0}'.format(self.api_key)
        if query_params is None:
            query_params = {}

        if headers is None:
            headers = {
                'Accept': CONTENT_TYPE,
                'Authorization': auth,
                'Content-Type': 'application/json',
            }
        elif not isinstance(headers, dict):
            raise InvalidHeaders(headers)

        if add_headers is not None:
            headers.update(**add_headers)

        for k, v in query_params.items():
            if isinstance(v, basestring):
                continue
            try:
                iter(v)
            except:
                continue
            key = '%s[]' % k
            query_params.pop(k)
            query_params[key] = ','.join(v)

        kwargs = {
            'headers': headers,
            'params': query_params,
        }

        if data is not None:
            kwargs['data'] = json.dumps(data)

        response = self._do_request(
            getattr(requests, method.lower()),
            '/'.join((self.base_url, endpoint)),
            **kwargs
        )

        return self._handle_response(response)
