import json
import logging
import os
from typing import List

from dotenv import load_dotenv  # pip install python-dotenv
from langchain_core.documents import Document

from LangChainKaltura import KalturaCaptionLoader
from LangChainKaltura.MiVideoAPI import MiVideoAPI

logging.basicConfig(level=logging.INFO)


def main() -> List[Document]:
    # Load environment variables from `.env` file
    load_dotenv()

    api = MiVideoAPI(
        host=os.getenv('MIVIDEO_API_HOST'),
        authId=os.getenv('MIVIDEO_API_AUTH_ID'),
        authSecret=os.getenv('MIVIDEO_API_AUTH_SECRET'),
    )

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


if '__main__' == __name__:
    documents = main()
    print(json.dumps([d.to_json()['kwargs'] for d in documents],
                     indent=2, sort_keys=True))
    print('Number of Documents:', len(documents))
