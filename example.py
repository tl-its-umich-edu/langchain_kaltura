import json
import os
from typing import List

from dotenv import load_dotenv  # pip install python-dotenv
from langchain_core.documents import Document

from LangChainKaltura import KalturaCaptionLoader


def main() -> List[Document]:
    load_dotenv()

    mediaFilter = json.loads(
        os.getenv('FILTERJSON', '{}'))

    captionLoader = KalturaCaptionLoader(
        os.getenv('PARTNERID'),
        os.getenv('APPTOKENID'),
        os.getenv('APPTOKENVALUE'),
        KalturaCaptionLoader.FilterType(
            mediaFilter.get('type')),
        mediaFilter.get('value'),
        os.getenv('URLTEMPLATE'),
    )

    documents = captionLoader.load()

    return documents


if '__main__' == __name__:
    documents = main()
    print(json.dumps([d.to_json()['kwargs'] for d in documents],
                     indent=2, sort_keys=True))
