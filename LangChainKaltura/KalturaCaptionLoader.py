import hashlib
from enum import Enum, auto
from typing import List, Self

import pysrt
import requests
from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Caption import (
    KalturaCaptionAssetFilter, KalturaCaptionType, KalturaCaptionAsset)
from KalturaClient.Plugins.Core import (
    KalturaMediaEntryFilter, KalturaSessionType, KalturaMediaEntry)
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document


class KalturaCaptionLoader(BaseLoader):
    """
    Load chunked caption assets from Kaltura for a single media entry ID or
    for every media contained in a specific category.

    Following the pattern of other LangChain loaders, all configuration of
    KalturaCaptionLoader is done via constructor parameters.  After an
    instance of the class has been created, call its `load()` method to begin
    working and return results.
    """
    EXPIRYSECONDSDEFAULT = 86400  # 24 hours
    CHUNKMINUTESDEFAULT = 2

    class FilterType(Enum):
        """
        Types of supported filter strings.

        - `MEDIAID` indicates a Kaltura media entry ID.
        - `CATEGORY` indicates a Kaltura category text "full path", e.g.,
          `root>site>courses>course_category_name`.

        For convenience, the constructor parameter is case-insensitive.
        E.g., `FilterType('CATEGORY')` and `FilterType('category')` are
        equivalent.
        """
        CATEGORY = auto()
        MEDIAID = auto()

        @classmethod
        def _missing_(cls, key):
            value = cls.__members__.get(key.upper())
            if value is None:
                raise ValueError(f'Invalid key "{key}" for {cls.__name__}')
            return cls(value)

    def __init__(self,
                 partnerId: str,
                 appTokenId: str,
                 appTokenValue: str,
                 filterType: FilterType,
                 filterValue: str,
                 urlTemplate: str,
                 expirySeconds: int = EXPIRYSECONDSDEFAULT,
                 chunkMinutes: int = CHUNKMINUTESDEFAULT,
                 kalturaApiBaseUrl: str = None):
        """
        :param partnerId: Partner ID in Kaltura (i.e., the KAF ID).
        :param appTokenId: ID of the app token configured in Kaltura.
        :param appTokenValue: Value of the app token referred to by ID above.
            This value is considered to be a sensitive secret, akin to a
            password.
        :param filterType: One of the `FilterType` values, `FilterType.MEDIAID`
            or `FilterType.CATEGORY`, which determines how `filterValue`
            will be used.
        :param filterValue: String containing the media ID or full category
            name of the media in Kaltura to be processed.
            Depends on `filterType`.
        :param urlTemplate: String template to construct URLs for the `source`
            metadata property of LangChain `Document` objects.  It must contain
            the fields `mediaId` and `startSeconds` ONLY to be filled in by
            `str.format()`.  E.g.,
            `https://example.edu/v/{mediaId}?t={startSeconds}`.
        :param expirySeconds: *Optional* Integer number of seconds for length
            of the Kaltura auth. session.  *Defaults to value of
            `KalturaCaptionLoader.EXPIRYSECONDSDEFAULT`.*
        :param chunkMinutes: *Optional* Integer number of minutes of the length
            of each caption chunk loaded from Kaltura.  *Defaults to value of
            `KalturaCaptionLoader.CHUNKMINUTESDEFAULT`.*
        :param kalturaApiBaseUrl: *Optional* String base URL of the Kaltura API
            service.  *Defaults to value of
            `KalturaConfiguration().serviceUrl`.*
        """

        if not all((partnerId, appTokenId, appTokenValue)):
            raise ValueError('partnerId and appToken* parameters must be '
                             'specified')

        if type(filterType) is not self.FilterType:
            raise TypeError(f'filterType "{filterType}" ({type(filterType)}) '
                            f'is not a {repr(self.FilterType)}')

        if not filterValue:
            raise ValueError('filterValue must be specified')

        if not urlTemplate:
            raise ValueError('urlFormat must be specified, with fields for'
                             '"{mediaId}" and "{startSeconds}".')

        config = KalturaConfiguration()
        if kalturaApiBaseUrl is not None:
            config.serviceUrl = kalturaApiBaseUrl
        client = KalturaClient(config)

        widgetSession = client.session.startWidgetSession(f'_{partnerId}')

        appTokenHash = hashlib.sha512(
            (widgetSession.ks + appTokenValue).encode('ascii')).hexdigest()

        client.setKs(widgetSession.ks)

        appSession = client.appToken.startSession(
            appTokenId, appTokenHash, type=KalturaSessionType.USER,
            expiry=expirySeconds)

        client.setKs(appSession.ks)
        self.client = client

        self.mediaFilter: KalturaMediaEntryFilter | None = None
        if filterType == self.FilterType.CATEGORY:
            self.setMediaCategory(filterValue)
        else:
            self.setMediaEntry(filterValue)

        self.chunkMinutes = int(chunkMinutes)
        self.urlTemplate = urlTemplate

    def setMediaEntry(self, mediaEntryId: str) -> Self:
        self.mediaFilter = KalturaMediaEntryFilter()
        self.mediaFilter.idEqual = mediaEntryId
        return self

    def setMediaCategory(self, categoryText: str) -> Self:
        self.mediaFilter = KalturaMediaEntryFilter()
        self.mediaFilter.categoriesMatchAnd = categoryText
        return self

    def load(self) -> List[Document]:
        if self.mediaFilter is None:
            raise ValueError('Media filter is not defined')

        mediaEntries = self.client.media.list(self.mediaFilter)

        documents: List[Document] = []
        for mediaEntry in mediaEntries.objects:
            documents.extend(self.fetchMediaCaption(mediaEntry))

        return documents

    def fetchMediaCaption(self, mediaEntry: KalturaMediaEntry) -> \
            List[Document]:
        captionFilter = KalturaCaptionAssetFilter()
        captionFilter.entryIdEqual = mediaEntry.id

        captionDocuments: List[Document] = []
        captionAssets = self.client.caption.captionAsset.list(captionFilter)
        captionAsset: KalturaCaptionAsset
        for captionAsset in captionAssets.objects:
            # XXX: Kaltura caption assets have an `isDefault` property.
            #   However, media doesn't always have a default caption asset.
            #   It seems wise to load all captions, even if they're all of
            #   the same language or low accuracy ratings.

            # Only the SRT format supported at this time
            if captionAsset.format.value == KalturaCaptionType.SRT:
                # Kaltura's `caption.captionAsset.serve()` seemed like it
                # would give caption contents, but it also only
                # returned a URL to the captions.
                captionUrl = self.client.caption.captionAsset.getUrl(
                    captionAsset.id)
                captionSource = requests.get(captionUrl).text
                captions = pysrt.from_string(captionSource)

                index = 0
                while (captionsSection := captions.slice(
                        starts_after={
                            'minutes': (start := self.chunkMinutes * index)},
                        ends_before={'minutes': start + self.chunkMinutes})):
                    captionDocuments.append(Document(
                        page_content=captionsSection.text,
                        # TODO: What other metadata should be included?
                        metadata={
                            # Start time is sliced to remove milliseconds.
                            'source': self.urlTemplate.format(
                                mediaId=mediaEntry.id,
                                startSeconds=str(
                                    captionsSection[0].start.ordinal)[0:-3]),
                            'filename': mediaEntry.name,
                            'media_id': mediaEntry.id,
                            'caption_id': captionAsset.id,
                            'language_code': captionAsset.languageCode.value,
                            'caption_format': 'SRT', }))
                    index += 1

        return captionDocuments
