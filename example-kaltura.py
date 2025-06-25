import json
import logging
import os
import sys
from typing import List

from dotenv import load_dotenv  # pip install python-dotenv
from langchain_core.documents import Document

from LangChainKaltura import KalturaCaptionLoader
from LangChainKaltura.KalturaAPI import KalturaAPI
from KalturaClient.Plugins.Core import (KalturaSessionType, KalturaMediaEntry,
                                        KalturaMediaEntryFilter)


logging.basicConfig(level=logging.INFO)


def main() -> List[Document]:
    # Load environment variables from `.env` file
    load_dotenv()

    api = KalturaAPI(
        host='HOST',
        authId='AUTHID',
        authSecret=os.getenv('KALTURA_SESSION_TOKEN'),
    )

    courseId = os.getenv('COURSEID')
    print(f'Course ID: {courseId}')

    media = api.getMediaList(
        courseId=courseId,
        userId='USERID',
    )

    print(objectToJson(media))

    print(f'Found {len(media)} media items.')


    m: KalturaMediaEntry = media[0]
    print(objectToJson(m))

    sys.exit()

    languages = os.getenv('LANGUAGE_CODES_CSV')
    if not languages:
        languages = KalturaCaptionLoader.LANGUAGES_DEFAULT
    else:
        languages = set(languages.split(','))

    courseId = os.getenv('COURSEID')

    captionLoader = KalturaCaptionLoader(
        apiClient=api,
        courseId=courseId,
        userId=os.getenv('USERID'),
        languages=languages,
        urlTemplate=os.getenv('SOURCEURLTEMPLATE'),
        chunkSeconds=int(os.getenv('CHUNKSECONDS')
                         or KalturaCaptionLoader.CHUNK_SECONDS_DEFAULT),
    )

    documents = captionLoader.load()

    courseUrlTemplate = os.getenv('COURSEURLTEMPLATE')

    if courseUrlTemplate:
        for document in documents:
            document.metadata['course_context'] = courseUrlTemplate.format(
                courseId=courseId)

    return documents


def objectToDict(obj):
    objDict = {}
    for key, value in getattr(obj, '__dict__', {}).items():
        try:
            json.dumps(value)
            objDict[key] = value
        except (TypeError, ValueError):
            if hasattr(value, '__dict__'):
                objDict[key] = objectToDict(value)
                objDict[key]['@type'] = type(value).__name__
            else:
                objDict[key] = str(value)
    return objDict

def objectToJson(obj):
    return json.dumps(objectToDict(obj), indent=2)


if '__main__' == __name__:
    documents = main()
    print(json.dumps([d.to_json()['kwargs'] for d in documents],
                     indent=2, sort_keys=True))
    print('Number of Documents:', len(documents))
