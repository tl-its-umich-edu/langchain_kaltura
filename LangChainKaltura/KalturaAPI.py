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
        return [{'id': mediaEntry.id, 'name': mediaEntry.name} for mediaEntry
                in mediaEntries.objects]

    def getCaptionList(self, mediaId: str, courseId=NotImplemented,
                       userId=NotImplemented) -> List[Dict[str, Any]]:
        """
        Retrieves the list of captions for a media item.

        Args:
            courseId (str): The course ID.
            userId (str): The user ID.
            mediaId (str): The media ID.

        Returns:
            List[Dict[str, Any]]: The list of captions.
        """

        captionFilter = KalturaCaptionAssetFilter()
        captionFilter.entryIdEqual = mediaId
        captionAssets = self.client.caption.captionAsset.list(captionFilter)
        return [{'id': captionAsset.id, 'label': captionAsset.label,
                 'languageCode': captionAsset.languageCode.value,
                 'format': captionAsset.format.value} for captionAsset in
                captionAssets.objects]

    def getCaptionText(self, captionId: str, courseId=NotImplemented,
                       userId=NotImplemented) -> str:
        """
        Retrieves the text of a caption.

        Args:
            courseId (str): The course ID.
            userId (str): The user ID.
            captionId (str): The caption ID.

        Returns:
            str: The caption text.
        """

        captionUrl = self.client.caption.captionAsset.getUrl(captionId)
        captionText = requests.get(captionUrl).text
        return captionText
