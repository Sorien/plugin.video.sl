import binascii
import datetime
import json
import os
import time
import requests.cookies

try:
    from urlparse import urlparse, unquote, parse_qs  # 3
except ImportError:
    from urllib.parse import urlparse, unquote, parse_qs  # 2.7

UA = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36'


class SkylinkException(Exception):
    def __init__(self, id):
        self.id = id


class UserNotDefinedException(SkylinkException):
    def __init__(self):
        self.id = 30501


class UserInvalidException(SkylinkException):
    def __init__(self):
        self.id = 30502


class TooManyDevicesException(Exception):
    def __init__(self, data):
        self.id = data['id']
        self.secret = data['secret']
        self.devices = data['devices']


class Skylink:
    _username = ''
    _password = ''
    _data_root = ''
    _cookies_path = ''
    _session = requests.Session()
    _session.max_redirects = 3
    _u, _q = '', {}
    _url = ''
    _login_url = ''

    def __init__(self, username, password, data_root, provider='skylink.sk'):
        self._usermane = username
        self._password = password
        self._data_root = data_root
        self._cookies_path = os.path.join(self._data_root, '%s.cookie' % username.lower())
        self._url = 'https://livetv.' + provider
        self._login_url = 'https://login.' + provider

    def _store_cookies(self):
        if not os.path.exists(self._data_root):
            os.makedirs(self._data_root)
        with open(self._cookies_path, 'w') as f:
            json.dump(requests.utils.dict_from_cookiejar(self._session.cookies), f)

    def _load_cookies(self):
        if os.path.exists(self._cookies_path):
            with open(self._cookies_path, 'r') as f:
                self._session.cookies = requests.utils.cookiejar_from_dict(json.load(f))
        else:
            self._session.cookies = requests.cookies.RequestsCookieJar()

        ret, self._u, self._q, _ = self._parse_cookies()
        return ret

    def _clear_cookies(self):
        self._session.cookies.clear()
        self._store_cookies()

    def _auth(self):

        if (self._usermane == '') or (self._password == ''):
            raise UserNotDefinedException

        self._session.cookies.clear()
        self._session.get(self._url + '/sso.aspx', headers={'User-Agent': UA})

        self._session.post(self._login_url, data={'Username': self._usermane, 'Password': self._password},
                           headers={'User-Agent': UA, 'Referer': self._url})

        r, self._u, self._q, error = self._parse_cookies()
        if ('error' in error) and (error['error'] == 'toomany'):
            raise TooManyDevicesException(error)

        if self._u == '':
            raise UserInvalidException

        return r

    def _parse_cookies(self):
        u, q, e = '', {}, {}
        for cookie in self._session.cookies:
            if cookie.name == 'solocoo_user':
                q = parse_qs(cookie.value)
            if cookie.name == 'slcuser_stats':
                u = cookie.value
            if cookie.name == 'err':
                e = json.loads(unquote(str(cookie.value)))
        if (u != '') and (q['type'][0] == 'user'):
            return True, u, q, e
        else:
            return False, '', {}, e

    def _login(self):
        if not self._load_cookies():
            try:
                self._auth()
                self._store_cookies()
            except:
                self._clear_cookies()
                raise

    def _time(self):
        return int(time.time() * 1000)

    def _request(self, method, url, **kwargs):
        try:
            return self._session.request(method, url, **kwargs)
        except requests.TooManyRedirects:
            # no error but user is not valid
            r, _, _, _ = self._parse_cookies()
            if not r:
                try:
                    self._auth()
                    self._store_cookies()
                except:
                    self._clear_cookies()
                    raise

    def _get(self, params):
        return self._request('GET', self._url + '/api.aspx', params=params, allow_redirects=True,
                             headers={'User-Agent': UA, 'Referer': self._url,
                                      'Accept': 'application/json, text/javascript, */*; q=0.01'})

    def _post(self, params, data):
        return self._request('POST', self._url + '/api.aspx', params=params, data=data, json=None,
                             headers={'User-Agent': UA, 'Referer': self._url,
                                      'Accept': 'application/json, text/javascript, */*; q=0.01',
                                      'X-Requested-With': 'XMLHttpRequest'})

    def channels(self):

        self._login()
        # https://livetv.skylink.sk/api.aspx?z=epg&lng=cs&_=1528800771023&u=w94e14412-8cef-b880-80ea-60a78b79490a&a=slsk&v=3&cs=111&f_format=clx&streams=7&d=3
        res = self._get({'z': 'epg', 'lng': self._q['lang'][0], '_': self._time(), 'u': self._u,
                         'a': self._q['app'][0], 'v': 3, 'cs': '111', 'f_format': 'clx', 'streams': 7,
                         'd': 3})

        data = res.json()
        result = []
        idx = 0

        for c in data[0][1]:
            is_stream = (len(data[1]) > (idx >> 5)) and (data[1][idx >> 5] & (1 << (idx & 31)) > 0)
            is_live = (len(data[3][0]) > (idx >> 5)) and (data[3][0][idx >> 5] & (1 << (idx & 31)) > 0)

            if is_stream and is_live:
                result.append(c)

            idx += 1
        return result

    def _headers_str(self, headers):
        res = ''
        for key in headers:
            res = res + '&' + key + '=' + requests.utils.quote(headers[key])
        return res[1:]

    def channel_info(self, channel_id):

        self._login()

        # https://livetv.skylink.sk/api.aspx?z=stream&lng=cs&_=1528789722179&u=w94e14412-8cef-b880-80ea-60a78b79490a&v=1&id=rzxqQ-kzUkG3x2PGEaxnFAAAAAE&d=3'
        res = self._post({'z': 'stream', 'lng': self._q['lang'][0], '_': self._time(), 'u': self._u,
                          'v': 1, 'id': channel_id, 'd': 3},
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

    def _ts(self, dt):
        return int(time.mktime(dt.timetuple())) * 1000

    # CS = 10011;
    # CS_DETAILS = 212763;
    # CS_FOR_REMINDERS = 9475;
    # CS_FOR_SEARCH = 42779;
    # CS_TV_GUIDE = 259;
    # LIMIT_NONE = -1;
    # MASK_AGE = 16;
    # MASK_AIRDATE = 16777216;
    # MASK_CATEGORY = 32;
    # MASK_CHANEL_NAME = 32768;
    # MASK_COVER = 1024;
    # MASK_CREDITS = 131072;
    # MASK_DESCRIPTION = 8;
    # MASK_END = 128;
    # MASK_EPISODE_NO = 4096;
    # MASK_FLAGS = 256;
    # MASK_GENRE = 512;
    # MASK_GENRES = 65536;
    # MASK_ID = 1;
    # MASK_SEASON_NO = 2048;
    # MASK_SERIES_ID = 8192;
    # MASK_START = 64;
    # MASK_TITLE = 2;
    def epg(self, channels, start_date=datetime.datetime.now(), days=1):

        self._login()

        # https://livetv.skylink.sk/api.aspx?z=epg&lng=cs&_=1528956297441&a=slsk&v=3&f=1528927200000&t=1529013600000&f_format=pg&cs=9491&s=2458762496!344807296!344809728!592296192

        from_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = from_date + datetime.timedelta(days=days)

        i = 0
        channels_count = len(channels)
        channels_str = ''
        result = []
        for data in channels:
            i += 1
            channels_str = channels_str + '!' + str(data['stationid'])
            if ((i % 100) == 0) or (i == channels_count):
                res = self._get({'z': 'epg', 'lng': 'sk', self._q['lang'][0]: self._time(), 'u': self._u,
                                 'a': self._q['app'][0], 'v': 3, 'f': self._ts(from_date), 't': self._ts(to_date),
                                 'f_format': 'pg', 'cs': 1 | 2 | 8 | 512 | 1024, 's': channels_str[1:]})  # 212763
                res = res.json()[1]
                for channel_id in res:
                    result.append({channel_id: self._epg(res[channel_id])})
                channels_str = ''
        return result

    def _epg(self, epg_info):
        for data in epg_info:
            if 'cover' in data:
                data['cover'] = data['cover'].replace('satplusimages', 'satplusimages/260x145')
            data.update(self._times(data['locId']))
        return epg_info

    def _times(self, loc):
        loc_base64 = loc.replace('-', '+').replace('_', '/')
        try:
            binstr = bytes(loc_base64)  # 2.7
        except:
            binstr = bytes(loc_base64, encoding='ascii')  # 3.x

        byte_array = list(bytearray(binascii.a2b_base64(binstr)))
        start_in_minutes_since2012 = ((byte_array[3] & 63) << 20) + (byte_array[4] << 12) + (byte_array[5] << 4) + (
                (byte_array[6] & 240) >> 4)
        return {'duration': ((byte_array[6] & 15) << 8) + byte_array[7],
                'start': (start_in_minutes_since2012 * 60) + 1325376000}
