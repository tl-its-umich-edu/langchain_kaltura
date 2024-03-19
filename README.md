# LangChainKaltura (langchain_kaltura)

A LangChain vector store loader for captions of videos hosted in Kaltura (UMich's MiVideo service).

## Requirements

(See issue umich-its-ai/langchain_kaltura#1 for the most current list of requirements and their completion status.)

* It must return langchain `Document` class(es).
* This should be a standalone, headless application, which could be invoked as part of a more complex process.
* When processing captions from media, it should be split into two-minute chunks.
* Caption chunks' metadata will include source URLs to the media, which include timestamps to the specific two-minute window of the video.
* It will only work with media that include captions, which were written or approved by owners.
* When working with Kaltura, an app token **_MUST_** be required.

## Example

Basic usage of this module is to import it, instantiate it with all the necessary parameters, and call its `run()` method.

```python
import os

from LangChainKaltura import \
    KalturaCaptionLoader

captionLoader = KalturaCaptionLoader(
    os.getenv('PARTNERID'),
    os.getenv('APPTOKENID'),
    os.getenv('APPTOKENVALUE'),
    KalturaCaptionLoader.FilterType(
        os.getenv('FILTERTYPE')),
    os.getenv('FILTERVALUE'),
    os.getenv('URLTEMPLATE'))

documents = captionLoader.load()
print(documents)
```

See the file `example.py` for a more detailed example, which will read parameters from `.env` (based on `.env.example`) and print the results as JSON.

## Testing Suite

Run the `testing` submodule to see a complete test of the `KalturaCaptionLoader`, which includes mocking of the Kaltura API.

```shell
python -m LangChainKaltura.tests
```
