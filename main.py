import sys
import inputstreamhelper
import logger
import skylink
import xbmc
import xbmcaddon
import xbmcgui
import urlparse
import xbmcplugin
import replay
import live
import utils

_id = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = xbmc.translatePath(_addon.getAddonInfo('profile')).decode("utf-8")
_user_name = xbmcplugin.getSetting(_id, 'username')
_password = xbmcplugin.getSetting(_id, 'password')
_provider = 'skylink.sk' if int(xbmcplugin.getSetting(_id, 'provider')) == 0 else 'skylink.cz'
_pin_protected_content = 'false' != xbmcplugin.getSetting(_id, 'pin_protected_content')
_a_show_live = 'false' != xbmcplugin.getSetting(_id, 'a_show_live')


def play(channel_id, askpin):
    logger.log.info('play: ' + channel_id)
    sl = skylink.Skylink(_user_name, _password, _profile, _provider)

    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
            return

    info = utils.call(sl, lambda: sl.channel_info(channel_id))

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            xbmcplugin.setResolvedUrl(_id, True, playitem)


if __name__ == '__main__':
    args = urlparse.parse_qs(sys.argv[2][1:])
    if 'id' in args:
        play(str(args['id'][0]), str(args['askpin'][0]) if 'askpin' in args else 'False')
    elif 'replay' in args:
        replay.router(args, skylink.Skylink(_user_name, _password, _profile, _provider, _pin_protected_content))
    elif 'live' in args:
        live.router(args, skylink.Skylink(_user_name, _password, _profile, _provider, _pin_protected_content))
    else:
        xbmcplugin.setPluginCategory(_id, '')
        xbmcplugin.setContent(_id, 'videos')
        xbmcplugin.addDirectoryItem(_id, replay.get_url(replay='channels'), xbmcgui.ListItem(label=_addon.getLocalizedString(30600)), True)
        if _a_show_live:
            xbmcplugin.addDirectoryItem(_id, replay.get_url(live='channels'), xbmcgui.ListItem(label=_addon.getLocalizedString(30700)), True)
        xbmcplugin.endOfDirectory(_id)
