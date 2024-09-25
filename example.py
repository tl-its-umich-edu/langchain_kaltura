import json
import os
from typing import List

from dotenv import load_dotenv  # pip install python-dotenv
from langchain_core.documents import Document

from LangChainKaltura import KalturaCaptionLoader


def main() -> List[Document]:
    # Load environment variables from `.env` file
    load_dotenv()

    # JSON not required, but useful for debugging
    mediaFilter = json.loads(
        os.getenv('FILTERJSON', '{}'))

    # Most arguments don't need keywords, but useful for debugging
    captionLoader = KalturaCaptionLoader(
        partnerId=os.getenv('PARTNERID'),
        appTokenId=os.getenv('APPTOKENID'),
        appTokenValue=os.getenv('APPTOKENVALUE'),
        filterType=KalturaCaptionLoader.FilterType(
            mediaFilter.get('type')),
        filterValue=mediaFilter.get('value'),
        urlTemplate=os.getenv('URLTEMPLATE'),
    )

    documents = captionLoader.load()

    return documents


if '__main__' == __name__:
    documents = main()
    print(json.dumps([d.to_json()['kwargs'] for d in documents],
                     indent=2, sort_keys=True))
