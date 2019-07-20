import binascii
import datetime
import json
import os
import time
import uuid

import requests.cookies

try:
    from urlparse import urlparse, unquote, parse_qs  # 3.x
except ImportError:
    from urllib.parse import urlparse, unquote, parse_qs  # 2.7

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
M7_DOMAIN = 'm7cz.solocoo.tv'
M7_API_WEB = 'https://' + M7_DOMAIN + "/"
M7_API_URL = M7_API_WEB + 'm7cziphone/'


class SkylinkException(Exception):
    def __init__(self, id):
        self.id = id


class UserNotDefinedException(SkylinkException):
    def __init__(self):
        self.id = 30501


class UserInvalidException(SkylinkException):
    def __init__(self):
        self.id = 30502


class TooManyDevicesException(SkylinkException):
    def __init__(self, data):
        self.id = 30505
        self.devices = data['devices']


class SkylinkSessionData:
    uid = ''
    secret = ''
    id = ''

    def is_valid(self):
        return (self.secret != '') and (self.id != '')

    def clear(self):
        self.secret = ''
        self.id = ''


class Skylink:
    _username = ''
    _password = ''
    _storage_path = ''
    _storage_file = ''
    _session = requests.Session()
    _session.max_redirects = 3
    _data = SkylinkSessionData()
    _url = ''
    _show_pin_protected = True

    def __init__(self, username, password, storage_dir, provider='skylink.sk', show_pin_protected=True):
        self._provider = provider
        self._lang = 'sk' if provider == 'skylink.sk' else 'cs'
        self._app = 'slsk' if provider == 'skylink.sk' else 'slcz'
        self._usermane = username
        self._password = password
        self._storage_path = storage_dir
        self._storage_file = os.path.join(self._storage_path, '%s.session' % username.lower())
        self._url = 'https://livetv.' + provider
        self._show_pin_protected = show_pin_protected
        self._load_session()

    def _store_session(self):
        if not os.path.exists(self._storage_path):
            os.makedirs(self._storage_path)
        with open(self._storage_file, 'w') as f:
            json.dump(self._data.__dict__, f)

    def _load_session(self):
        if os.path.exists(self._storage_file):
            with open(self._storage_file, 'r') as f:
                self._data.__dict__ = json.load(f)

    def _auth(self, device):

        if self._data.is_valid():
            return

        try:
            if (self._usermane == '') or (self._password == ''):
                raise UserNotDefinedException

            session = requests.Session()
            resp = session.get('https://login.' + self._provider + '/authenticate',
                               params={'redirect_uri': 'https://livetv.' + self._provider + '/auth.aspx',
                                       'state': self._time(),
                                       'response_type': 'code',
                                       'scope': 'TVE',
                                       'client_id': 'StreamGroup'
                                       },
                               headers={'User-Agent': UA}
                               )
            resp = session.post('https://login.' + self._provider + '/',
                                data={'Username': self._usermane, 'Password': self._password},
                                headers={'User-Agent': UA, 'Referer': resp.url})

            if self._data.uid == '':
                self._data.uid = 'w' + str(uuid.uuid4())

            ref = resp.url
            params = parse_qs(urlparse(resp.url).query)

            if ('code' in params) and (params['code'] != ''):
                oauthcode = params['code'][0]
            else:
                raise UserInvalidException()

            resp = requests.post(M7_API_URL + 'challenge.aspx',
                                 json={"autotype": "nl",
                                       "app": self._app,
                                       "prettyname": "Chrome",
                                       "model": "web",
                                       "serial": self._data.uid,
                                       "oauthcode": oauthcode,
                                       "apikey": ""},
                                 headers={'User-Agent': UA, 'Referer': ref})

            data = resp.json()

            if ('error' in data) and (data['error'] == 'toomany'):
                if device != '':
                    resp = requests.post(M7_API_URL + 'challenge.aspx?r=1',
                                         json={"autotype": "nl",
                                               "app": self._app,
                                               "prettyname": "Chrome",
                                               "model": "web",
                                               "serial": self._data.uid,
                                               "oldserial": device,
                                               "oauthcode": oauthcode,
                                               "apikey": "",
                                               "secret": data['secret'],
                                               "userid": data['id']},
                                         headers={'User-Agent': UA, 'Referer': ref})
                    data = resp.json()
                else:
                    raise TooManyDevicesException(data)

            self._data.secret = data['secret']
            self._data.id = data['id']
            
            self._store_session()
        except:
            self._data.clear()
            self._store_session()
            raise

    def _login(self):
        if self._data.is_valid():
            resp = self._session.post(M7_API_URL + 'login.aspx',
                                      data={'secret': self._data.id + "\t" + self._data.secret,
                                            'uid': self._data.uid, 'app': self._app},
                                      headers={'User-Agent': UA})
            if resp.text == 'disconnected':
                self._data.clear()
            else:
                return

        self._auth('')
        self._login()

    def reconnect(self, device):
        self._data.clear()
        self._auth(device)

    @staticmethod
    def _time():
        return int(time.time() * 1000)

    def _request(self, method, url, **kwargs):
        return self._session.request(method, url, **kwargs)

    def _get(self, params):
        return self._request('GET', M7_API_URL + 'capi.aspx', params=params, allow_redirects=True,
                             headers={'User-Agent': UA, 'Referer': self._url,
                                      'Accept': 'application/json, text/javascript, */*; q=0.01'})

    def _post(self, params, data):
        return self._request('POST', M7_API_URL + 'capi.aspx', params=params, data=data,
                             json=None,
                             headers={'User-Agent': UA, 'Referer': self._url,
                                      'Accept': 'application/json, text/javascript, */*; q=0.01',
                                      'X-Requested-With': 'XMLHttpRequest'})

    def channels(self, replay=False):
        """Returns available live channels, when reply is set returns replayable channels as well
        :param replay: bool
        :return: Channels data
        """
        self._login()
        res = self._get({'z': 'epg', 'lng': self._lang, 'a': self._app, 'v': 3, 'cs': '111', 'f_format': 'clx', 'streams': 7, 'd': 3}) #15?

        data = res.json()
        result = []
        idx = 0

        for c in data[0][1]:
            is_stream = (len(data[1]) > (idx >> 5)) and (data[1][idx >> 5] & (1 << (idx & 31)) > 0)
            is_live = (len(data[3][0]) > (idx >> 5)) and (data[3][0][idx >> 5] & (1 << (idx & 31)) > 0)
            is_replayable = (c['flags'] & 2048) > 0
            is_pin_protected = (c['flags'] & 256) > 0

            if (is_stream and is_live and (not replay or is_replayable) and
                    (self._show_pin_protected or (not self._show_pin_protected and not is_pin_protected))):
                c['pin'] = is_pin_protected
                result.append(c)

            idx += 1
        return result

    def _headers_str(self, headers):
        res = ''
        for key in headers:
            res = res + '&' + key + '=' + requests.utils.quote(headers[key])
        return res[1:]

    def channel_info(self, channel_id):
        """Returns channel info
        :param channel_id:
        :return: Channel info
        """
        self._login()
        res = self._post({'z': 'stream', 'lng': self._lang, 'v': 1, 'id': channel_id, 'd': 3},
                         json.dumps({'type': 'dash', 'flags': '4096'}).encode())

        stream = res.json()

        mpd_headers = {'Origin': self._url, 'Referer': self._url, 'User-Agent': UA}
        drm_la_headers = {'Origin': self._url, 'Referer': self._url, 'Content-Type': 'application/octet-stream',
                          'User-Agent': UA}

        return {
            'protocol': 'mpd',
            'path': requests.utils.requote_uri(stream['url']) + '|' + self._headers_str(mpd_headers),
            'drm': 'com.widevine.alpha',
            'key': stream['drm']['laurl'] + '|' + self._headers_str(drm_la_headers) + '|R{SSM}|'
        }

    def epg(self, channels, from_date, to_date):
        """Returns EPG data
        :param channels: Result from channels function
        :param from_date: datetime First day of requested Epg
        :param to_date: datetime Last day of requested Epg
        :return: Epg data

        cs param values:
            CS = 10011; CS_DETAILS = 212763; CS_FOR_REMINDERS = 9475; CS_FOR_SEARCH = 42779; CS_TV_GUIDE = 259;
            LIMIT_NONE = -1;
            MASK_AGE = 16; MASK_AIRDATE = 16777216; MASK_CATEGORY = 32; MASK_CHANEL_NAME = 32768; MASK_COVER = 1024;
            MASK_CREDITS = 131072; MASK_DESCRIPTION = 8; MASK_END = 128; MASK_EPISODE_NO = 4096; MASK_FLAGS = 256;
            MASK_GENRE = 512; MASK_GENRES = 65536; MASK_ID = 1; MASK_SEASON_NO = 2048; MASK_SERIES_ID = 8192;
            MASK_START = 64;  MASK_TITLE = 2;
        """

        def tidy_epg(epg_info):

            def times(loc):
                loc_base64 = loc.replace('-', '+').replace('_', '/')
                try:
                    binstr = bytes(loc_base64)  # 2.7
                except:
                    binstr = bytes(loc_base64, encoding='ascii')  # 3.x

                a = list(bytearray(binascii.a2b_base64(binstr)))
                start_in_minutes_since2012 = ((a[3] & 63) << 20) + (a[4] << 12) + (a[5] << 4) + ((a[6] & 240) >> 4)

                return {'duration': ((a[6] & 15) << 8) + a[7], 'start': (start_in_minutes_since2012 * 60) + 1325376000}

            for data in epg_info:
                if 'description' in data:
                    data['description'] = data['description'].strip()
                if 'cover' in data:
                    data['cover'] = M7_API_WEB + data['cover'].replace('satplusimages', 'satplusimages/447x251')
                data.update(times(data['locId']))
            return epg_info

        def ts(dt):
            return int(time.mktime(dt.timetuple())) * 1000

        self._login()
        from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = to_date.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

        i = 0
        channels_count = len(channels)
        channels_str = ''
        result = []
        for data in channels:
            i += 1
            channels_str = channels_str + '!' + str(data['stationid'])
            if ((i % 100) == 0) or (i == channels_count):
                res = self._get({'z': 'epg', 'lng': self._lang, 'a': self._app, 'v': 3, 'f': ts(from_date), 't': ts(to_date),
                                 'f_format': 'pg', 'cs': 1 | 2 | 8 | 512 | 1024 | 65536,
                                 's': channels_str[1:]})  # 212763
                res = res.json()[1]
                for channel_id in res:
                    result.append({channel_id: tidy_epg(res[channel_id])})
                channels_str = ''
        return result

    def replay_info(self, locId):
        """Returns reply info
        :param locId:
        :return: Reply info
        """
        self._login()
        res = self._post({'z': 'replay', 'lng': self._lang, 'v': 1, 'lid': locId, 'd': 3}, json.dumps({'type': 'dash', 'flags': '1024'}).encode())

        stream = res.json()

        mpd_headers = {'Origin': self._url, 'Referer': self._url, 'User-Agent': UA}
        drm_la_headers = {'Origin': self._url, 'Referer': self._url, 'Content-Type': 'application/octet-stream',
                          'User-Agent': UA}

        return {
            'protocol': 'mpd',
            'path': requests.utils.requote_uri(stream['url']) + '|' + self._headers_str(mpd_headers),
            'drm': 'com.widevine.alpha',
            'key': stream['drm']['laurl'] + '|' + self._headers_str(drm_la_headers) + '|R{SSM}|'
        }

    def pin_info(self):
        """Returns pin info
        :return:
       """
        self._login()
        res = self._get({'z': 'parentalPIN', 'lng': self._lang, 'a': self._app, 'r': 1})
        raw = res.text
        if raw.startswith('"') and raw.endswith('"') and not raw.startswith('"-'):
            pin = raw.replace('"', '')
            if len(pin) == 4:
                return pin
        return None
