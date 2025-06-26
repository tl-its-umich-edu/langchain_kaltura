import logging
from enum import Enum, auto
from typing import List, Sequence

import pysrt
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document

from LangChainKaltura.AbstractMediaPlatformAPI import AbstractMediaPlatformAPI

logger = logging.getLogger(__name__)


class KalturaCaptionLoader(BaseLoader):
    """
    Load chunked caption assets from Kaltura for a single media entry ID or
    for every media contained in a specific category.

    Following the pattern of other LangChain loaders, all configuration of
    KalturaCaptionLoader is done via constructor parameters.  After an
    instance of the class has been created, call its `load()` method to begin
    working and return results.
    """
    EXPIRY_SECONDS_DEFAULT = 86400  # 24 hours
    CHUNK_SECONDS_DEFAULT = 120
    LANGUAGES_DEFAULT = {
        'en-us', 'en', 'en-ca', 'en-gb', 'en-ie', 'en-au', 'en-nz', 'en-bz',
        'en-jm', 'en-ph', 'en-tt', 'en-za', 'en-zw'}
    """Various English dialects from ISO 639-1, ordered by similarity to 
      `en-us`.  For an unofficial listing of languages with dialects, see: 
      https://gist.github.com/jrnk/8eb57b065ea0b098d571#file-iso-639-1-language-json"""

    # Based on KalturaClient.Plugins.Caption.KalturaCaptionType
    class KalturaCaptionTypeCode(Enum):
        SRT = auto()
        DFXP = auto()
        WEBVTT = auto()
        CAP = auto()
        SCC = auto()

        @classmethod
        def _missing_(cls, key):
            value = cls.__members__.get(key.upper())
            if value is None:
                raise ValueError(f'Invalid key "{key}" for {cls.__name__}')
            return cls(value)

    def __init__(self,
                 apiClient: AbstractMediaPlatformAPI,
                 courseId: str,
                 userId: str,
                 urlTemplate: str,
                 languages: Sequence[str] | None = LANGUAGES_DEFAULT,
                 chunkSeconds: int = CHUNK_SECONDS_DEFAULT,
                 ):

        if not urlTemplate:
            raise ValueError('urlFormat must be specified, with fields for'
                             '"{mediaId}" and "{startSeconds}".')

        self.apiClient = apiClient
        self.courseId = courseId
        self.userId = userId
        self.urlTemplate = urlTemplate
        self.languages = (None if languages is None
                          else set(map(str.lower, languages)))
        self.chunkSeconds = int(chunkSeconds)

    def load(self) -> List[Document]:
        mediaEntries = self.apiClient.getMediaList(self.courseId, self.userId)

        documents: List[Document] = []
        for mediaEntry in mediaEntries:
            documents.extend(self.fetchMediaCaption(mediaEntry))

        return documents

    def fetchMediaCaption(self, mediaEntry: dict) -> \
            List[Document]:
        captionDocuments: List[Document] = []
        captionAssets = self.apiClient.getCaptionList(
            courseId=self.courseId, userId=self.userId,
            mediaId=mediaEntry['id'])

        for captionAsset in captionAssets:
            # XXX: Kaltura caption assets have an `isDefault` property.
            #   However, media doesn't always have a default caption asset.
            #   It seems wise to load all captions, even if they're all of
            #   the same language or low accuracy ratings.

            # Skip captions not in specified language(s)
            captionLanguage = captionAsset['languageCode'].lower()
            if (self.languages is not None and
                    captionLanguage not in self.languages):
                logger.info(f'Skipping caption ({captionAsset["id"]}) '
                            f'in language "{captionLanguage}" '
                            f'for media ({mediaEntry["id"]})')
                continue

            # Only the SRT format supported at this time
            if (int(captionAsset['format']) ==
                    self.KalturaCaptionTypeCode.SRT.value):
                captionSource = self.apiClient.getCaptionText(
                    courseId=self.courseId, userId=self.userId,
                    captionId=captionAsset['id'])
                captions = pysrt.from_string(captionSource)

                index = 0
                while (captionsSection := captions.slice(
                        starts_after={
                            'seconds': (start := self.chunkSeconds * index)},
                        ends_before={'seconds': start + self.chunkSeconds})):
                    timestamp = captionsSection[0].start
                    captionDocuments.append(Document(
                        page_content=captionsSection.text,
                        metadata={
                            # Start time is sliced to remove milliseconds.
                            'source': self.urlTemplate.format(
                                mediaId=mediaEntry['id'],
                                startSeconds=timestamp.ordinal // 1000),
                            'filename': mediaEntry['name'],
                            'media_id': mediaEntry['id'],
                            'timestamp': str(timestamp)[0:-4],  # no ms
                            'caption_id': captionAsset['id'],
                            'language_code': captionAsset['languageCode'],
                            'caption_format': 'SRT', }))
                    index += 1

        return captionDocuments
