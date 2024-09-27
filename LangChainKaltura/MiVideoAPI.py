import base64
import os

import requests
from dotenv import load_dotenv

from .AbstractMediaPlatformAPI import AbstractMediaPlatformAPI


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

    def __init__(self, host, authId, authSecret):
        self.host = host
        self.baseUrl = f'https://{self.host}/um/aa/mivideo/v1'
        self.headers = {
            'Authorization': self._getAuthToken(authId, authSecret)}

    def _getAuthToken(self, authId, authSecret):
        auth = f'{authId}:{authSecret}'
        authBase64 = base64.b64encode(auth.encode('utf-8')).decode('utf-8')
        url = f'https://{self.host}/um/oauth2/token'
        params = {'grant_type': 'client_credentials', 'scope': 'mivideo'}
        headers = {'Authorization': f'Basic {authBase64}'}
        response = requests.post(url, params=params, headers=headers)
        response.raise_for_status()
        tokenData = response.json()
        return f"{tokenData['token_type']} {tokenData['access_token']}"

    def getMediaList(self, courseId, userId, pageIndex=1, pageSize=500):
        url = f'{self.baseUrl}/course/{courseId}/media'
        params = {'pageIndex': pageIndex, 'pageSize': pageSize}
        headers = {'LMS-User-Id': userId, **self.headers}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json().get('objects', [])

    def getCaptionList(self, courseId, userId, mediaId):
        url = f'{self.baseUrl}/course/{courseId}/media/{mediaId}/captions'
        headers = {'LMS-User-Id': userId, **self.headers}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('objects', [])

    def getCaptionText(self, courseId, userId, captionId):
        url = f'{self.baseUrl}/course/{courseId}/captions/{captionId}/text'
        headers = {'LMS-User-Id': userId, **self.headers}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text


if '__main__' == __name__:
    load_dotenv()

    api = MiVideoAPI(
        host=os.getenv('MIVIDEO_API_HOST'),
        authId=os.getenv('MIVIDEO_API_AUTH_ID'),
        authSecret=os.getenv('MIVIDEO_API_AUTH_SECRET'),
    )

    courseId = '512931'
    userId = '813788'

    mediaList = api.getMediaList(courseId, userId)
    mediaId = mediaList[0]['id']
    print('Media ID:', mediaId)

    captionList = api.getCaptionList(courseId, userId, mediaId)
    captionId = captionList[0]['id']
    print('Caption ID:', captionId)

    captionTextLines = api.getCaptionText(courseId, userId,
                                          captionId).splitlines()
    print('Caption text…')
    print('\n'.join(captionTextLines[0:6]))
