import logging
from typing import List, Dict, Any

import requests
from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Caption import (KalturaCaptionAssetFilter)
from KalturaClient.Plugins.Core import (KalturaMediaEntryFilter,
                                        KalturaCategoryFilter)

from .AbstractMediaPlatformAPI import AbstractMediaPlatformAPI

logger = logging.getLogger(__name__)


class KalturaAPI(AbstractMediaPlatformAPI):
    """
    Support use of Kaltura API via an existing session token.

    This is not a full implementation of the Kaltura API, but rather
    a simplified interface that allows access to media and captions
    associated with a course in the University of Michigan's MiVideo
    service, which is based on Kaltura.

    Specifically, the limitations of this API are…

    * `getMediaList()` only returns media associated with a
        course, identified by the course ID from Canvas formatted in a
        category string.  It gets only the media available in the course's
        Media Gallery, not those embedded in Canvas Pages or Assignments.
        This is to emulate the behavior of the MiVideo API.

    Attributes:
        client (KalturaClient): Instance of Kaltura API client.
    """

    def __init__(self, authSecret: str, host=NotImplemented,
                 authId=NotImplemented, timeout=NotImplemented,
                 version=NotImplemented) -> None:
        """
        Initializes the KalturaAPI instance.

        Args:
            authSecret (str): An existing Kaltura API session ID.
        """

        self.client = KalturaClient(KalturaConfiguration())
        self.client.setKs(authSecret)

    def _getCategoryId(self, categoryFullName: str) -> str:
        """
        Retrieves the category ID for a given category full name.

        Args:
            categoryFullName (str): The full name of the category.

        Returns:
            str: The category ID.
        """
        categoryFilter = KalturaCategoryFilter()
        categoryFilter.fullNameEqual = categoryFullName

        categories = self.client.category.list(categoryFilter)

        if categories.objects:
            return categories.objects[0].id
        else:
            raise ValueError(
                f'Category with full name "{categoryFullName}" not found.')

    def _makeCategoryFullNameForCourse(self, courseId: str) -> str:
        """
        Constructs the full name of the category for a course.

        Args:
            courseId (str): The course ID.

        Returns:
            str: The full name of the category.
        """
        return f'Canvas_UMich>site>channels>{courseId}'

    def getMediaList(self, courseId: str, userId=NotImplemented,
                     pageIndex=NotImplemented, pageSize=NotImplemented) -> \
            List[Dict[str, Any]]:
        """
        Retrieves the list of media for a course.

        Only returns media associated with a course, identified by the course
        ID from Canvas formatted in a category string.  It gets only the media
        available in the course's Media Gallery, not those embedded in Canvas
        Pages or Assignments.

        This is to emulate the behavior of the MiVideo API.

        Args:
            courseId (str): The course ID.

        Returns:
            List[Dict[str, Any]]: The list of media.
        """

        categoryFullName = self._makeCategoryFullNameForCourse(courseId)

        mediaFilter = KalturaMediaEntryFilter()
        # mediaFilter.categoriesMatchAnd = categoryFullName
        mediaFilter.categoriesIdsMatchOr = self._getCategoryId(
            categoryFullName)

        mediaEntries = self.client.media.list(mediaFilter)
        return [{
            'id': mediaEntry.id,
            'name': mediaEntry.name
        } for mediaEntry in mediaEntries.objects]

    def getCaptionList(self, mediaId: str, courseId=NotImplemented,
                       userId=NotImplemented) -> List[Dict[str, Any]]:
        """
        Retrieves the list of captions for a media item.

        Args:
            mediaId (str): The media ID.

        Returns:
            List[Dict[str, Any]]: The list of captions.
        """

        captionFilter = KalturaCaptionAssetFilter()
        captionFilter.entryIdEqual = mediaId
        captionAssets = self.client.caption.captionAsset.list(captionFilter)
        return [{
            'id': captionAsset.id,
            'languageCode': captionAsset.languageCode.getValue(),
            'format': captionAsset.format.getValue()
        } for captionAsset in captionAssets.objects]

    def getCaptionText(self, captionId: str, courseId=NotImplemented,
                       userId=NotImplemented) -> str:
        """
        Retrieves the text of a caption.

        Args:
            captionId (str): The caption ID.

        Returns:
            str: The caption text.
        """

        captionUrl = self.client.caption.captionAsset.getUrl(captionId)
        captionText = requests.get(captionUrl).text
        return captionText
