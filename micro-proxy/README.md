### How to start this mini proxy into Kaltura

1. Ensure you have the following environment variables:
    - `KALTURA_HOST`
    - `KALTURA_SESSION`
    - `KALTURA_PARTNER_ID`
    - `KALTURA_MEDIA_SEARCH_PREFIX`

2. Create a Python virtual environment and activate it.
3. Run `pip install -r requirements.txt`
4. Run `fastapi dev app.py`
5. Use Postman to test the API Paths.

*Based on standard **FastAPI** library*
