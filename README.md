# langchain_kaltura — README

A langchain vector store loader for captions of videos hosted in Kaltura (UMich's MiVideo service).

## Requirements

(See issue umich-its-ai/langchain_kaltura#1 for the most current list of requirements and their completion status.)

* It must return langchain `Document` class(es).
* This should be a standalone, headless application, which could be invoked as part of a more complex process.
* When processing captions from videos, they should be split into two-minute chunks.
* When queried, it should return URLs to videos which include timestamps to the specific two-minute window of the video.
* It will only work with videos that include captions, which were written or approved by instructors.
* When working with Kaltura, an admin token **_MUST NOT_** be required.
