import json
import os
from typing import List

from dotenv import load_dotenv  # pip install python-dotenv
from langchain_core.documents import Document

from LangChainKaltura import KalturaCaptionLoader
from LangChainKaltura.MiVideoAPI import MiVideoAPI


def main() -> List[Document]:
    # Load environment variables from `.env` file
    load_dotenv()

    # JSON not required, but useful for debugging
    mediaFilter = json.loads(
        os.getenv('FILTERJSON', '{}'))

    api = MiVideoAPI(
        host=os.getenv('MIVIDEO_API_HOST'),
        authId=os.getenv('MIVIDEO_API_AUTH_ID'),
        authSecret=os.getenv('MIVIDEO_API_AUTH_SECRET'),
    )

    captionLoader = KalturaCaptionLoader(
        apiClient=api,
        courseId=os.getenv('COURSEID'),
        userId=os.getenv('USERID'),
        urlTemplate=os.getenv('URLTEMPLATE'),
        chunkSeconds=int(os.getenv('CHUNKSECONDS')
                         or KalturaCaptionLoader.CHUNK_SECONDS_DEFAULT),
    )

    documents = captionLoader.load()

    return documents


if '__main__' == __name__:
    documents = main()
    print(json.dumps([d.to_json()['kwargs'] for d in documents],
                     indent=2, sort_keys=True))
