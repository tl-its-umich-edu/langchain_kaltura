# LangChainKaltura

A LangChain vector store loader for captions of videos hosted in Kaltura (the basis of UMich's MiVideo service).

## Installation

```shell
pip install LangChainKaltura
```

## Usage

Instantiate `KalturaCaptionLoader` with all the required parameters, then invoke its `load()` method…

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

See the repo for `example.py`, a more detailed example which reads parameters from `.env` (based on `.env.example`) and prints the results as JSON.

## Features

(See issue [#1](https://github.com/umich-its-ai/langchain_kaltura/issues/1) for the most current list of requirements and their completion status.)

* Connecting to Kaltura requires an app token.
* It works only with captioned media, which was presumably written by or approved by media owners.  At this time, only SRT captions are supported.
* Captions from media are reorganized into chunks.  The chunk duration is configurable, with a default of two minutes.
* It returns a list of LangChain `Document` object(s), each containing a caption chunk and metadata.
* Caption chunks' metadata contains source URLs to the media, which includes timestamps to the specific chunk of the video.

## Test Suite

Run the `testing` submodule to see a complete test of the `KalturaCaptionLoader`, which includes mocking of the Kaltura API.

```shell
python -m tests
```

## Credits

* Mr. Lance E Sloan (@lsloan) - Development
* Melinda Kraft - Kaltura advising
