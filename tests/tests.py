import json
import os.path
from http import HTTPMethod
import sys

from LangChainKaltura.MiVideoAPI import MiVideoAPI

try:
    import flask
except ImportError:
    sys.exit('Please install Flask with `pip install flask`')

try:
    from http_server_mock import HttpServerMock
except ImportError:
    sys.exit('Please install http_server_mock with '
             '`pip install http_server_mock`')

from LangChainKaltura import KalturaCaptionLoader

HOST_DEFAULT = 'localhost'
PORT_DEFAULT = 8311

app = HttpServerMock(__name__)

fixturesPathname = os.path.join(os.path.dirname(__file__), 'fixtures', '')


@app.route('/api_v3/service/<service>/action/<action>',
           methods=[HTTPMethod.POST])
def serviceActionHandler(service, action):
    (host, port) = flask.request.server
    return open(f'{fixturesPathname}{service}_{action}.xml').read().format(
        host=host, port=port)


# contrived route, specified in `caption_captionasset_getUrl.xml`
@app.route('/captionAsset/contents/<captionFilename>',
           methods=[HTTPMethod.GET])
def captionAssetContents(captionFilename):
    return open(f'{fixturesPathname}{captionFilename}').read()


def main(host: str = HOST_DEFAULT, port: int = PORT_DEFAULT):
    with app.run(host, port):

        api = MiVideoAPI(
            host=f'{host}:{port}',
            authId='MIVIDEO_API_AUTH_ID',
            authSecret='MIVIDEO_API_AUTH_SECRET',
        )
