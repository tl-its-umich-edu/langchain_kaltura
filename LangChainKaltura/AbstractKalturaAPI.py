from abc import ABC, abstractmethod


class AbstractKalturaAPI(ABC):
    # @abstractmethod
    # def __init__(self, host, authId, authSecret, courseId, userId):
    #     pass
    #
    # @abstractmethod
    # def _getAuthToken(self, authId, authSecret):
    #     pass

    @abstractmethod
    def getMediaList(self, courseId, userId, pageIndex=1, pageSize=500):
        pass

    @abstractmethod
    def getCaptionList(self, courseId, userId, mediaId):
        pass

    @abstractmethod
    def getCaptionText(self, courseId, userId, captionId):
        pass
