# langchain_kaltura - - README

A langchain vector store loader for captions of videos hosted in Kaltura (MiVideo).

Requirements…

* It must return langchain Document class(es).
* This should be a standalone, headless application, which could be invoked as part of a more complex process.
* When processing captions from videos, they should be split into two-minute chunks.
* When queried, it should return URLs to videos which include timestamps to the specific two-minute window of the video.
* It will only work with videos that include captions, which were written or approved by instructors.
* When working with Kaltura, an admin token MUST NOT be required.


