import base64
import logging
import uuid
from typing import List, Dict, Any, Optional

import requests
from requests.exceptions import RequestException, HTTPError, Timeout
from tenacity import (retry, stop_after_attempt, wait_exponential,
                      before_sleep_log, RetryError, retry_if_exception_type)

from .AbstractMediaPlatformAPI import AbstractMediaPlatformAPI

logger = logging.getLogger(__name__)


class MiVideoAPI(AbstractMediaPlatformAPI):
    """
    MiVideo API client

    MiVideo is the name of the University of Michigan's video service based
    on Kaltura.  This API offers more access control than Kaltura's API.
    Internally, course and user IDs are used by the API to determine
    whether the user has access to media associated with the LMS course.
    (UMich uses Canvas.)  The API also uses the course ID to construct a
    Kaltura category string, which identifies which media are associated
    with the course.  In addition to improved access control, the MiVideo
    API also offers authorization via OAuth2, which is a common method, as
    opposed to Kaltura's proprietary method.

    Attributes:
        DEFAULT_TIMEOUT (int): Default timeout for requests.
        DEFAULT_VERSION (str): Default API version.
        host (str): Hostname of the MiVideo API.
        baseUrl (str): Base URL for the MiVideo API.
        timeout (int): Timeout for requests.
        headers (Dict[str, str]): Headers for requests.
    """

    DEFAULT_TIMEOUT: int = 2
    DEFAULT_VERSION: str = 'v1'

    _METHOD_GET: str = 'GET'
    _METHOD_POST: str = 'POST'

    def __init__(self, host: str, authId: str, authSecret: str,
                 timeout: int = DEFAULT_TIMEOUT,
                 version: str = DEFAULT_VERSION) -> None:
        """
        Initializes the MiVideoAPI instance.

        Args:
            host (str): Hostname of the MiVideo API.
            authId (str): Authentication ID.
            authSecret (str): Authentication secret.
            timeout (int, optional): Timeout for requests. Defaults to
                DEFAULT_TIMEOUT.
            version (str, optional): API version. Defaults to DEFAULT_VERSION.
        """
        self.host: str = host
        self.baseUrl: str = f'https://{self.host}/um/aa/mivideo/{version}'
        self.timeout: int = timeout
        self.headers: Dict[str, str] = {
            'Authorization': self._getAuthToken(authId, authSecret)}

    @retry(before_sleep=before_sleep_log(logger, logging.WARNING),
           retry=retry_if_exception_type(Timeout),
           stop=stop_after_attempt(3),
           wait=wait_exponential(max=10), )
    def _requestWithRetry(self, url: str, method: str = _METHOD_GET,
                          params: Dict[str, Any] = {},
                          headers: Dict[str, str] = {}) -> requests.Response:
        """
        Makes a request with retry logic.

        Args:
            url (str): The URL to make the request to.
            method (str, optional): HTTP method to use. Defaults to _METHOD_GET.
            params (Optional[Dict[str, Any]], optional): Query parameters.
                Defaults to None.
            headers (Optional[Dict[str, str]], optional): Request headers.
                Defaults to None.

        Returns:
            requests.Response: The response from the request.

        Raises:
            HTTPError: If an HTTP error occurs.
            Timeout: If the request times out.
            RequestException: If a request exception occurs.
            Exception: If an unexpected error occurs.
        """

        # requestID logged on server and used for debugging
        requestId = str(uuid.uuid4())
        headers['X-Request-Id'] = requestId

        try:
            response: requests.Response = requests.request(
                method, url, params=params, headers=headers,
                timeout=self.timeout)
            response.raise_for_status()
            return response
        except Timeout as e:
            logger.warning(f'Request "{url}" timed out: {e};'
                           f' requestId: {requestId}')
            raise
        except (HTTPError, Timeout, RequestException) as e:
            logger.error(f'Request failed: {e}; requestId: {requestId}')
            raise
        except Exception as e:
            logger.error(f'An unexpected error occurred: {e};'
                         f' requestId: {requestId}')
            raise

    def _getAuthToken(self, authId: str, authSecret: str) -> str:
        """
        Retrieves the authentication token.

        Args:
            authId (str): Authentication ID.
            authSecret (str): Authentication secret.

        Returns:
            str: The authentication token.

        Raises:
            RetryError: If retry attempts fail.
            HTTPError: If an HTTP error occurs.
            Timeout: If the request times out.
            RequestException: If a request exception occurs.
            Exception: If an unexpected error occurs.
        """
        try:
            auth: str = f'{authId}:{authSecret}'
            authBase64: str = base64.b64encode(auth.encode('utf-8')).decode(
                'utf-8')

            # FIXME: this API raises HTTP 500 error if authSecret is incorrect
            url: str = f'https://{self.host}/um/oauth2/token'
            params: Dict[str, str] = {'grant_type': 'client_credentials',
                                      'scope': 'mivideo'}
            headers: Dict[str, str] = {'Authorization': f'Basic {authBase64}'}

            response: requests.Response = self._requestWithRetry(
                url, method=self._METHOD_POST, params=params, headers=headers)
            response.raise_for_status()
            tokenData: Dict[str, Any] = response.json()
            logger.debug(f'_getAuthToken {response.elapsed.total_seconds()}s')
            return f"{tokenData['token_type']} {tokenData['access_token']}"
        except RetryError as e:
            logger.error(f'Retry attempts failed: {e}')
            raise
        except (HTTPError, Timeout, RequestException) as e:
            if e.response.status_code == 401:
                logger.error(f'Authorization failed: {e}')
                raise HTTPError('Authorization failed') from e
            else:
                logger.error(f'Failed to get authZ token: {e}')
                raise HTTPError('Failed to get authZ token') from e
        except Exception as e:
            logger.error(
                f'An unexpected error occurred while getting authZ token: {e}')
            raise

    def getMediaList(self, courseId: str, userId: str, pageIndex: int = 1,
                     pageSize: int = 500) -> List[Dict[str, Any]]:
        """
        Retrieves the list of media for a course.

        Args:
            courseId (str): The course ID.
            userId (str): The user ID.
            pageIndex (int, optional): The page index. Defaults to 1.
            pageSize (int, optional): The page size. Defaults to 500.

        Returns:
            List[Dict[str, Any]]: The list of media.
        """
        url: str = f'{self.baseUrl}/course/{courseId}/media'
        params: Dict[str, int] = {'pageIndex': pageIndex, 'pageSize': pageSize}
        headers: Dict[str, str] = {'LMS-User-Id': userId, **self.headers}
        response: requests.Response = self._requestWithRetry(url,
                                                             params=params,
                                                             headers=headers)
        response.raise_for_status()
        logger.debug(f'getMediaList {response.elapsed.total_seconds()}s')
        return response.json().get('objects', [])

    def getCaptionList(self, courseId: str, userId: str, mediaId: str) \
            -> List[Dict[str, Any]]:
        """
        Retrieves the list of captions for a media item.

        Args:
            courseId (str): The course ID.
            userId (str): The user ID.
            mediaId (str): The media ID.

        Returns:
            List[Dict[str, Any]]: The list of captions.
        """
        url: str = f'{self.baseUrl}/course/{courseId}/media/{mediaId}/captions'
        headers: Dict[str, str] = {'LMS-User-Id': userId, **self.headers}
        response: requests.Response = self._requestWithRetry(url,
                                                             headers=headers)
        response.raise_for_status()
        logger.debug(f'getCaptionList {response.elapsed.total_seconds()}s')
        return response.json().get('objects', [])

    def getCaptionText(self, courseId: str, userId: str,
                       captionId: str) -> str:
        """
        Retrieves the text of a caption.

        Args:
            courseId (str): The course ID.
            userId (str): The user ID.
            captionId (str): The caption ID.

        Returns:
            str: The caption text.
        """
        url: str = f'{self.baseUrl}/course/{courseId}/captions/{captionId}/text'
        headers: Dict[str, str] = {'LMS-User-Id': userId, **self.headers}
        response: requests.Response = self._requestWithRetry(url,
                                                             headers=headers)
        response.raise_for_status()
        logger.debug(f'getCaptionText {response.elapsed.total_seconds()}s')
        return response.text
