from os import environ
from typing import Optional, Callable, Iterator
from logging import getLogger
from datetime import datetime, timedelta

from requests import Response
from requests.exceptions import ConnectionError
from json.decoder import JSONDecodeError
from urllib3.util.retry import Retry

from citrine.exceptions import (
    NotFound,
    Unauthorized,
    UnauthorizedRefreshToken,
    WorkflowConflictException,
    WorkflowNotReadyException,
    BadRequest, CitrineException)

import jwt
import requests
import time

# Choose a 5 second buffer so that there's no chance of the access token
# expiring during the check for expiration
EXPIRATION_BUFFER_MILLIS: timedelta = timedelta(milliseconds=5000)
logger = getLogger(__name__)


class Session(requests.Session):
    """Wrapper around requests.Session that is both refresh-token and schema aware."""

    def __init__(self,
                 refresh_token: str = environ.get('CITRINE_API_TOKEN'),
                 scheme: str = 'https',
                 host: str = 'citrine.io',
                 port: Optional[str] = None):
        super().__init__()
        self.scheme: str = scheme
        self.authority = ':'.join([host, port or ''])
        self.refresh_token: str = refresh_token
        self.access_token: Optional[str] = None
        self.access_token_expiration: datetime = datetime.utcnow()

        # Following scheme:[//authority]path[?query][#fragment] (https://en.wikipedia.org/wiki/URL)
        self.headers.update({"Content-Type": "application/json"})

        # Default parameters for S3 connectivity. Can be changed by tests.
        self.s3_endpoint_url = None
        self.s3_use_ssl = True
        self.s3_addressing_style = 'auto'

        # Use a custom adapter so we can use retries with control over fine grained details.  Retries happen by default
        # with codes [503, 413, 429], use status_forcelist to add *additional* codes to retry on.  We're using this to
        # retry on several custom CloudFlare errors.
        retries = Retry(total=10,
                        connect=5,
                        read=5,
                        status=5,
                        backoff_factor=0.25,
                        status_forcelist=[500, 502, 504, 520, 521, 522, 524, 527])
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.mount('https://', adapter)
        self.mount('http://', adapter)

    def _versioned_base_url(self, version: str = 'v1'):
        return '{}://{}/api/{}/'.format(self.scheme, self.authority, version)

    def _is_access_token_expired(self):
        return self.access_token_expiration - EXPIRATION_BUFFER_MILLIS <= datetime.utcnow()

    def _refresh_access_token(self) -> None:
        """Optionally refresh our access token (if the previous one is about to expire)."""
        data = {'refresh_token': self.refresh_token}
        response = super().request(
            'POST', self._versioned_base_url() + 'tokens/refresh', json=data)
        if response.status_code != 200:
            raise UnauthorizedRefreshToken()
        self.access_token = response.json()['access_token']
        self.access_token_expiration = datetime.utcfromtimestamp(
            jwt.decode(self.access_token, verify=False)['exp']
        )

    def checked_request(self, method: str, path: str,
                        version: str = 'v1', **kwargs) -> requests.Response:
        """Check response status code and throw an exception if relevant."""
        if self._is_access_token_expired():
            self._refresh_access_token()
        uri = self._versioned_base_url(version) + path.lstrip('/')

        logger.debug('BEGIN request details:')
        logger.debug('\tmethod: {}'.format(method))
        logger.debug('\tpath: {}'.format(path))
        logger.debug('\turi: {}'.format(uri))
        logger.debug('\tversion: {}'.format(version))
        for k, v in kwargs.items():
            logger.debug('\t{}: {}'.format(k, v))
        logger.debug('END request details.')

        response = super().request(method, uri, **kwargs)

        try:
            if response.status_code == 401 and response.json().get("reason") == "invalid-token":
                self._refresh_access_token()
                response = super().request(method, uri, **kwargs)
        except ValueError:
            # Ignore ValueErrors thrown by attempting to decode json bodies. This
            # might occur if we get a 401 response without a JSON body
            pass

        # TODO: More substantial/careful error handling
        if 200 <= response.status_code <= 299:
            logger.info('%s %s %s', response.status_code, method, path)
            return response
        else:
            stacktrace = self._extract_response_stacktrace(response)
            if stacktrace is not None:
                logger.error('Response arrived with stacktrace:')
                logger.error(stacktrace)
            if response.status_code == 400:
                logger.error('%s %s %s', response.status_code, method, path)
                logger.error(response.text)
                raise BadRequest(path, response)
            elif response.status_code == 401:
                logger.error('%s %s %s', response.status_code, method, path)
                raise Unauthorized(path, response)
            elif response.status_code == 404:
                logger.error('%s %s %s', response.status_code, method, path)
                raise NotFound(path, response)
            elif response.status_code == 409:
                logger.debug('%s %s %s', response.status_code, method, path)
                raise WorkflowConflictException(response.text)
            elif response.status_code == 425:
                logger.debug('%s %s %s', response.status_code, method, path)
                msg = 'Cant execute at this time. Try again later. Error: {}'.format(response.text)
                raise WorkflowNotReadyException(msg)
            else:
                logger.error('%s %s %s', response.status_code, method, path)
                raise CitrineException(response.text)

    @staticmethod
    def _extract_response_stacktrace(response: Response) -> Optional[str]:
        try:
            json_value = response.json()
            if isinstance(json_value, dict):
                return json_value.get('debug_stacktrace')
        except ValueError:
            pass
        return None

    def get_resource(self, path: str, **kwargs) -> dict:
        """GET a particular resource as JSON."""
        response = self.checked_get(path, **kwargs)
        return self._extract_response_json(path, response)

    def post_resource(self, path: str, json: dict, **kwargs) -> dict:
        """POST to a particular resource as JSON."""
        response = self.checked_post(path, json=json, **kwargs)
        return self._extract_response_json(path, response)

    def put_resource(self, path: str, json: dict, **kwargs) -> dict:
        """PUT data given by some JSON at a particular resource."""
        response = self.checked_put(path, json=json, **kwargs)
        return self._extract_response_json(path, response)

    def delete_resource(self, path: str) -> dict:
        """DELETE a particular resource as JSON."""
        response = self.checked_delete(path)
        return self._extract_response_json(path, response)

    @staticmethod
    def _extract_response_json(path, response) -> dict:
        """Extract json from the response or log and return an empty dict if extraction fails."""
        try:
            return response.json()
        except JSONDecodeError as err:
            logger.info('Response at path %s with status code %s failed json parsing with'
                        ' exception %s. Returning empty value.',
                        path,
                        response.status_code,
                        err.msg)
            return {}

    @staticmethod
    def cursor_paged_resource(base_method: Callable[..., dict], path: str,
                              forward: bool = True, per_page: int = 100,
                              version: str = 'v2', **kwargs) -> Iterator[dict]:
        """
        Returns a flat generator of results for an API query.

        Results are fetched in chunks of size `per_page` and loaded lazily.
        """
        params = kwargs.get('params', {})
        params['forward'] = forward
        params['ascending'] = forward
        params['per_page'] = per_page
        kwargs['params'] = params
        while True:
            response_json = base_method(path, version=version, **kwargs)
            for obj in response_json['contents']:
                yield obj
            cursor = response_json.get('next')
            if cursor is None:
                break
            params['cursor'] = cursor

    def checked_post(self, path: str, json: dict, **kwargs) -> Response:
        """Execute a POST request to a URL and utilize error filtering on the response."""
        return self.checked_request('POST', path, json=json, **kwargs)

    def checked_put(self, path: str, json: dict, **kwargs) -> Response:
        """Execute a PUT request to a URL and utilize error filtering on the response."""
        return self.checked_request('PUT', path, json=json, **kwargs)

    def checked_delete(self, path: str) -> Response:
        """Execute a DELETE request to a URL and utilize error filtering on the response."""
        return self.checked_request('DELETE', path)

    def checked_get(self, path: str, **kwargs) -> Response:
        """Execute a GET request to a URL and utilize error filtering on the response."""
        return self.checked_request('GET', path, **kwargs)
