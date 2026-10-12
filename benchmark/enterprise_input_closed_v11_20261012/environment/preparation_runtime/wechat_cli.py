"""Real official-account draft operations; credentials and tokens stay in files."""
from pathlib import Path
import argparse, hashlib, ipaddress, json, mimetypes, re, time, urllib.parse, urllib.request, uuid

DEFAULT_CONFIG = '/run/secrets/wechat_official_account.json'
API = 'https://api.weixin.qq.com'
ALLOWED_API_PATHS = frozenset({
    '/cgi-bin/token', '/cgi-bin/material/add_material',
    '/cgi-bin/media/uploadimg', '/cgi-bin/draft/add', '/cgi-bin/draft/get',
    '/cgi-bin/draft/update',
})


class WechatError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__('Official-account operation failed')


def write(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class Client:
    def __init__(self, config, state):
        self.config = json.loads(Path(config).read_text(encoding='utf-8-sig'))
        self.state = Path(state)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def configured(self):
        return bool(self.config.get('app_id') and self.config.get('app_secret'))

    def egress(self):
        text = self.opener.open('https://myip.ipip.net', timeout=30).read().decode('utf-8')
        candidates = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
        if not candidates:
            raise WechatError('egress_ip_not_observed')
        return str(ipaddress.ip_address(candidates[0]))

    def check_ip(self):
        actual = self.egress()
        expected = self.config.get('expected_egress_ip')
        if not expected or actual != expected:
            raise WechatError('experiment_egress_condition_not_met')
        return actual

    def call(self, path, query=None, body=None, payload=None, content_type=None):
        if path not in ALLOWED_API_PATHS:
            raise WechatError('operation_outside_draft_test_scope')
        url = API + path
        if query:
            url += '?' + urllib.parse.urlencode(query)
        headers = {}
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode('utf-8')
            headers['Content-Type'] = 'application/json; charset=utf-8'
        elif content_type:
            headers['Content-Type'] = content_type
        request = urllib.request.Request(url, data=payload, headers=headers)
        with self.opener.open(request, timeout=45) as response:
            result = json.load(response)
        if result.get('errcode', 0):
            raise WechatError(result['errcode'])
        return result

    def token(self):
        if not self.configured():
            raise WechatError('credentials_not_configured')
        self.check_ip()
        cache = self.state / 'token.private.json'
        fingerprint = hashlib.sha256((self.config['app_id'] + '\0' + self.config['app_secret']).encode()).hexdigest()
        if cache.exists():
            saved = json.loads(cache.read_text(encoding='utf-8'))
            if saved.get('credential_fingerprint') == fingerprint and saved.get('expires_at', 0) > time.time() + 120:
                return saved['access_token']
        data = self.call('/cgi-bin/token', query={'grant_type': 'client_credential', 'appid': self.config['app_id'], 'secret': self.config['app_secret']})
        if not data.get('access_token'):
            raise WechatError('token_response_missing')
        write(cache, {'access_token': data['access_token'], 'expires_at': time.time() + data['expires_in'], 'credential_fingerprint': fingerprint})
        return data['access_token']

    def upload(self, file, cover=False):
        file = Path(file)
        if not file.is_file():
            raise WechatError('input_image_missing')
        token = self.token()
        boundary = 'skillloop_' + uuid.uuid4().hex
        mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        filename = re.sub(r'[^A-Za-z0-9._-]', '_', file.name)
        payload = ('--' + boundary + '\r\nContent-Disposition: form-data; name="media"; filename="' + filename + '"\r\nContent-Type: ' + mime + '\r\n\r\n').encode()
        payload += file.read_bytes() + ('\r\n--' + boundary + '--\r\n').encode()
        path = '/cgi-bin/material/add_material' if cover else '/cgi-bin/media/uploadimg'
        query = {'access_token': token}
        if cover:
            query['type'] = 'image'
        return self.call(path, query=query, payload=payload, content_type='multipart/form-data; boundary=' + boundary)

    def add_draft(self, articles):
        body = json.loads(Path(articles).read_text(encoding='utf-8-sig'))
        if not body.get('articles'):
            raise WechatError('draft_articles_missing')
        return self.call('/cgi-bin/draft/add', query={'access_token': self.token()}, body=body)

    def get_draft(self, media_id):
        return self.call('/cgi-bin/draft/get', query={'access_token': self.token()}, body={'media_id': media_id})

    def update_verification_draft(self, media_id, articles):
        # Verification only: no CLI command exposes updates to pre-existing
        # drafts. The operator must explicitly bind the one draft just created
        # by this recorded native experiment, before the request is possible.
        if getattr(self, 'native_verification_draft_id', None) != media_id:
            raise WechatError('verification_draft_id_not_authorized')
        body = json.loads(Path(articles).read_text(encoding='utf-8-sig'))
        if len(body.get('articles', [])) != 1:
            raise WechatError('one_verification_article_required')
        return self.call('/cgi-bin/draft/update', query={'access_token': self.token()},
                         body={'media_id': media_id, 'index': 0, 'articles': body['articles'][0]})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default=DEFAULT_CONFIG)
    p.add_argument('--state', default='/tmp/wechat-private')
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('ready')
    sub.add_parser('token')
    for name in ['upload-cover', 'upload-image']:
        sub.add_parser(name).add_argument('--file', required=True)
    sub.add_parser('draft-add').add_argument('--articles', required=True)
    sub.add_parser('draft-get').add_argument('--media-id', required=True)
    a = p.parse_args()
    try:
        client = Client(a.config, a.state)
        if a.command == 'ready':
            actual = client.egress()
            result = {'configured': client.configured(), 'actual_egress_ip': actual, 'expected_ip_matches': actual == client.config.get('expected_egress_ip'), 'scope': 'draft_only', 'live_api_pass': False}
        elif a.command == 'token':
            token = client.token()
            result = {'token_received': True, 'token_sha256': hashlib.sha256(token.encode()).hexdigest(), 'token_printed': False}
        elif a.command in ['upload-cover', 'upload-image']:
            result = client.upload(a.file, a.command == 'upload-cover')
        elif a.command == 'draft-add':
            result = client.add_draft(a.articles)
        else:
            result = client.get_draft(a.media_id)
        print(json.dumps({'ok': True, 'command': a.command, 'data': result}, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({'ok': False, 'command': a.command, 'error_type': type(error).__name__, 'code': getattr(error, 'code', None), 'no_mock_success': True}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
