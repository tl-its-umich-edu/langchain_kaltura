'''
Example Kaltura API Proxy Server
This code is only for tutorial purposes. Not for production usage.
Author: Prithvijit Dasgupta
Email: prithvid@umich.edu
'''
from fastapi import FastAPI, Header
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, AliasPath
from typing import Annotated
import os
import httpx

app = FastAPI()


class LMSHeader(BaseModel):
    student_id: str = Field(validation_alias=AliasPath('lms-user-id'))


class KalturaParams():
    host: str = os.environ.get('KALTURA_HOST', None)
    ks: str = os.environ.get('KALTURA_SESSION', None)
    partner_id: str = os.environ.get('KALTURA_PARTNER_ID', None)
    media_search_prefix: str = os.environ.get(
        # this special prefix is a Kaltura category media prefix that is used in the media list query
        'KALTURA_MEDIA_SEARCH_PREFIX', '')


KALTURA_PARAMS = KalturaParams()
KALTURA_MEDIA_LIST_PATH = "media/action/list"
KALTURA_CAPTION_LIST_PATH = "caption_captionasset/action/list"
KALTURA_CAPTION_SERVE_PATH = "caption_captionasset/action/serve"


def check_students(course_id: int, student_id: int):
    # use course_id and student_id to check if the student belongs in the LMS
    # currently this predicate function just returns True
    return True


def get_kaltura_params():
    return {
        'ks': KALTURA_PARAMS.ks,
        'partnerId': KALTURA_PARAMS.partner_id,
        'format': 1  # JSON format response
    }

@app.post("/um/oauth2/token")
async def oauth_token(authorization: Annotated[str | None, Header()], grant_type: str, scope: str):
    try:
        if authorization!='' and grant_type!='' and scope!='':
            return {'access_token':'mock_token'}
        else:
            raise Exception("Invalid token scheme")
    except:
        raise Exception("Error in the server")

# Kaltura API endpoint: media.action.list


@app.get("/um/aa/mivideo/v1/course/{course_id}/media")
async def media_list(headers: Annotated[LMSHeader, Header()], course_id: int, pageIndex: int = 1, pageSize: int = 500):
    try:
        response = httpx.post(f'{KALTURA_PARAMS.host}/{KALTURA_MEDIA_LIST_PATH}', json={
            'filter': {
                # Category should match {prefix_string}{course_id}
                'categoriesMatchAnd': KALTURA_PARAMS.media_search_prefix+f"{course_id}"
            },
            'pager': {
                'pageIndex': pageIndex,
                'pageSize': pageSize
            }
        }, params=get_kaltura_params())
        if check_students(course_id, headers.student_id):
            return response.json()
        else:
            raise Exception("Missing student id")
    except:
        raise Exception("Error in the server")

# Kaltura API endpoint: caption.caption_asset.action.list


@app.get("/um/aa/mivideo/v1/course/{course_id}/media/{media_id}/captions")
async def caption_list(headers: Annotated[LMSHeader, Header()], course_id: int, media_id: str, pageIndex: int = 1, pageSize: int = 500):
    try:
        response = httpx.post(f'{KALTURA_PARAMS.host}/{KALTURA_CAPTION_LIST_PATH}', json={
            'filter': {
                'entryIdEqual': media_id,
            },
            'pager': {
                'pageIndex': pageIndex,
                'pageSize': pageSize
            }
        }, params=get_kaltura_params())
        if check_students(course_id, headers.student_id):
            return response.json()
        else:
            raise Exception("Missing student id")
    except:
        raise Exception("Error in the server")

# Kaltura API endpoint: caption.caption_asset.action.serve


@app.get("/um/aa/mivideo/v1/course/{course_id}/captions/{caption_id}/text", response_class=PlainTextResponse)
async def caption_serve(headers: Annotated[LMSHeader, Header()], course_id: int, caption_id: str):
    try:
        response = httpx.post(f'{KALTURA_PARAMS.host}/{KALTURA_CAPTION_SERVE_PATH}', json={
            'captionAssetId': caption_id
        }, params=get_kaltura_params())
        if check_students(course_id, headers.student_id):
            return response.text
        else:
            raise Exception("Missing student id")
    except Exception as e:
        print(e)
        raise Exception("Error in the server")
