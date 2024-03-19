import json
import os.path
from http import HTTPMethod

import flask
from http_server_mock import HttpServerMock

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
@app.route('/captionAsset/contents',
           methods=[HTTPMethod.GET])
def captionAssetContents():
    return open(f'{fixturesPathname}pinball_wizard.srt').read()


def main(host: str = HOST_DEFAULT, port: int = PORT_DEFAULT):
    with app.run(host, port):
        kalturaCaptions = KalturaCaptionLoader(
            '_partner_ID_here_',
            '_app_token_ID_here_',
            '_app_token_value_here_',
            KalturaCaptionLoader.FilterType.MEDIAID,
            '1_mediaId',
            'https://example.edu/v/{mediaId}?t={startSeconds}',
            kalturaApiBaseUrl=f'http://{host}:{port}/')
        documents = kalturaCaptions.load()
        print(json.dumps([d.to_json()['kwargs'] for d in documents],
                         indent=2, sort_keys=True))
