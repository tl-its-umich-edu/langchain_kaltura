import hashlib
import json
import os
from enum import Enum, auto
from typing import List, Self

import pysrt
import requests
from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Caption import (
    KalturaCaptionAssetFilter, KalturaCaptionType, KalturaCaptionAsset)
from KalturaClient.Plugins.Core import (
    KalturaMediaEntryFilter, KalturaSessionType, KalturaMediaEntry)
from dotenv import load_dotenv
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document


class KalturaCaptionLoader(BaseLoader):
    """
    Load chunked caption assets from Kaltura for a single media entry ID or
    for every media contained in a specific category.
    """
    EXPIRYSECONDSDEFAULT = 86400  # 24 hours
    CHUNKMINUTESDEFAULT = 2

    class FilterType(Enum):
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
        If a `sessionKey` is given, a rare occurrence, it overrides all
        other parameters.

        Exactly **ONE** of `mediaEntryId` or `categoryText` must be specified.

        Most other parameters are as documented for
        `KalturaClient.Client.KalturaClient.generateSession()`, except…

        :param mediaEntryId: ID string of a `KalturaMediaEntry` object.
        :param categoryText: Category string that may be applied to one or
            more `KalturaMediaEntry` objects.  Note that this must be the
            **FULL** "path" to the category, not only the desired category.
            E.g., 'Top_Level_Name>Sublevel_A>Sublevel_B>Desired_Category'.
        :param chunkMinutes: An integer number of minutes specifying the
            size of each caption chunk.
        :param urlTemplate: A template string to be used with `str.format()`
            to make a URL for the `source` metadata of the langchain `Document`
            objects.  Fields used in the template must be ONLY "{mediaId}" and
            "{startSeconds}".
        """

        if not all((partnerId, appTokenId, appTokenValue)):
            raise ValueError('partnerId and appToken* parameters must be '
                             'specified')

        if type(filterType) is not self.FilterType:
            raise TypeError(f'filterType "{filterType}" ({type(filterType)}) '
                            f'is not a {self.FilterType.__name__}')

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


def main() -> List[Document]:
    load_dotenv()

    mediaFilter = json.loads(os.getenv('FILTERJSON', '{}'))

    captionLoader = KalturaCaptionLoader(
        os.getenv('PARTNERID'),
        os.getenv('APPTOKENID'),
        os.getenv('APPTOKENVALUE'),
        KalturaCaptionLoader.FilterType(mediaFilter.get('type')),
        mediaFilter.get('value'),
        os.getenv('URLTEMPLATE'),
        expirySeconds=int(os.getenv(
            'EXPIRYSECONDS', KalturaCaptionLoader.EXPIRYSECONDSDEFAULT)),
        chunkMinutes=int(os.getenv(
            'CHUNKMINUTES', KalturaCaptionLoader.CHUNKMINUTESDEFAULT)),
    )

    documents = captionLoader.load()

    return documents


if '__main__' == __name__:
    # E.g., execute this code with `python -i -m kaltura_caption_loader`,
    # then inspect the contents of `documents` at the Python prompt
    documents = main()
    print(json.dumps([d.to_json()['kwargs'] for d in documents],
                     indent=2, sort_keys=True))
