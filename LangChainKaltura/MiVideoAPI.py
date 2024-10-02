import base64
import logging

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, before_log

from .AbstractMediaPlatformAPI import AbstractMediaPlatformAPI

logging.basicConfig(level=logging.INFO)
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
    """

    _METHOD_GET = 'GET'
    _METHOD_POST = 'POST'

    def __init__(self, host, authId, authSecret, version='v1', timeout=2):
        self.host = host
        self.baseUrl = f'https://{self.host}/um/aa/mivideo/{version}'
        self.timeout = timeout
        self.headers = {
            'Authorization': self._getAuthToken(authId, authSecret)}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(max=10),
           before=before_log(logger, logging.INFO))
    def _requestWithRetry(self, url, method=_METHOD_GET, params=None,
                          headers=None):
        """
        Necessary to avoid intermittent long delays in response times.

        :param url: URL to request
        :param method: HTTP method to use (Default: 'GET')
        :param params: URL parameters (Default: None)
        :param headers: HTTP headers (Default: None)
        """
        response = requests.request(
            method, url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _getAuthToken(self, authId, authSecret):
        auth = f'{authId}:{authSecret}'
        authBase64 = base64.b64encode(auth.encode('utf-8')).decode('utf-8')

        url = f'https://{self.host}/um/oauth2/token'
        params = {'grant_type': 'client_credentials', 'scope': 'mivideo'}
        headers = {'Authorization': f'Basic {authBase64}'}

        response = self._requestWithRetry(
            url, method=self._METHOD_POST, params=params, headers=headers)
        response.raise_for_status()
        tokenData = response.json()
        logger.info(f'_getAuthToken {response.elapsed.total_seconds()}s')
        return f"{tokenData['token_type']} {tokenData['access_token']}"

    def getMediaList(self, courseId, userId, pageIndex=1, pageSize=500):
        url = f'{self.baseUrl}/course/{courseId}/media'
        params = {'pageIndex': pageIndex, 'pageSize': pageSize}
        headers = {'LMS-User-Id': userId, **self.headers}
        response = self._requestWithRetry(url, params=params,
                                          headers=headers)
        response.raise_for_status()
        logger.info(f'getMediaList {response.elapsed.total_seconds()}s')
        return response.json().get('objects', [])

    def getCaptionList(self, courseId, userId, mediaId):
        url = f'{self.baseUrl}/course/{courseId}/media/{mediaId}/captions'
        headers = {'LMS-User-Id': userId, **self.headers}
        response = self._requestWithRetry(url, headers=headers)
        response.raise_for_status()
        logger.info(f'getCaptionList {response.elapsed.total_seconds()}s')
        return response.json().get('objects', [])

    def getCaptionText(self, courseId, userId, captionId):
        url = f'{self.baseUrl}/course/{courseId}/captions/{captionId}/text'
        headers = {'LMS-User-Id': userId, **self.headers}
        response = self._requestWithRetry(url, headers=headers)
        response.raise_for_status()
        logger.info(f'getCaptionText {response.elapsed.total_seconds()}s')
        return response.text
