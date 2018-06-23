import sys

import inputstreamhelper

import logger
import skylink
import xbmc
import xbmcaddon
import xbmcgui
import urlparse

import xbmcplugin

_id = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = xbmc.translatePath(_addon.getAddonInfo('profile')).decode("utf-8")
_user_name = xbmcplugin.getSetting(_id, 'username')
_password = xbmcplugin.getSetting(_id, 'password')
_provider = 'skylink.sk' if int(xbmcplugin.getSetting(_id, 'provider')) == 0 else 'skylink.cz'


def play(channel_id):
    logger.log.info('play: ' + channel_id)
    s = skylink.Skylink(_user_name, _password, _profile, _provider)
    i = s.channel_info(channel_id)
    is_helper = inputstreamhelper.Helper(i['protocol'], drm=i['drm'])
    if is_helper.check_inputstream():
        playitem = xbmcgui.ListItem(path=i['path'])
        playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        playitem.setProperty('inputstream.adaptive.manifest_type', i['protocol'])
        playitem.setProperty('inputstream.adaptive.license_type', i['drm'])
        playitem.setProperty('inputstream.adaptive.license_key', i['key'])
        xbmc.Player().play(item=i['path'], listitem=playitem)


if __name__ == '__main__':
    args = urlparse.parse_qs(sys.argv[2][1:])
    if 'id' in args:
        play(str(args['id'][0]))
