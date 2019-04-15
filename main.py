import sys
import inputstreamhelper
import logger
import requests
import skylink
import xbmc
import xbmcaddon
import xbmcgui
import urlparse
import xbmcplugin
import replay
import utils

_id = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = xbmc.translatePath(_addon.getAddonInfo('profile')).decode("utf-8")
_user_name = xbmcplugin.getSetting(_id, 'username')
_password = xbmcplugin.getSetting(_id, 'password')
_provider = 'skylink.sk' if int(xbmcplugin.getSetting(_id, 'provider')) == 0 else 'skylink.cz'
_handle = int(sys.argv[1])


#def select_device(devices):
#    dialog = xbmcgui.Dialog()
#    items = []
#    for device in devices:
#        items.append(device['name'].replace("+", " "))
#    d = dialog.select(_addon.getLocalizedString(30403), items)
#    return devices[d]['id'] if d > -1 else ''
#
#
#def get_last_used_device(devices):
#    la = 9999999999999
#    device = ''
#    for d in devices:
#        if d['lastactivity'] < la:
#            device = d['id']
#            la = d['lastactivity']
#    return device


def play(channel_id, askpin):
    logger.log.info('play: ' + channel_id)
    sl = skylink.Skylink(_user_name, _password, _profile, _provider)

    if askpin != 'False' and not utils.ask_for_pin(sl):
        xbmc.log("bad pin",level=xbmc.LOGNOTICE)
        xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
        return


    info = {}
    #try:
    #    info = sl.channel_info(channel_id)
    #except skylink.TooManyDevicesException as e:
    #    if _addon.getSetting('reuse_last_device') == 'true':
    #        device = get_last_used_device(e.devices)
    #    else:
    #        device = select_device(e.devices)
    #
    #    if device != '':
    #        logger.log.info('reconnecting as: ' + device)
    #        sl.reconnect(device)
    #        info = sl.channel_info(channel_id)
    #
    #except requests.exceptions.ConnectionError:
    #    dialog = xbmcgui.Dialog()
    #    dialog.ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30506))

    info = utils.call(sl, lambda: sl.channel_info(channel_id))

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            xbmcplugin.setResolvedUrl(_handle, True, playitem)


if __name__ == '__main__':
    args = urlparse.parse_qs(sys.argv[2][1:])
    if 'id' in args:
        play(str(args['id'][0]), str(args['askpin'][0]) if 'askpin' in args else 'False')
    elif 'replay' in args:
        replay.router(args, skylink.Skylink(_user_name, _password, _profile, _provider))
    else:
        xbmcplugin.setPluginCategory(_handle, '')
        xbmcplugin.setContent(_handle, 'videos')
        xbmcplugin.addDirectoryItem(_handle, replay.get_url(replay='channels'), xbmcgui.ListItem(label=_addon.getLocalizedString(30600)), True)
        xbmcplugin.endOfDirectory(_handle)

