import sys
import inputstreamhelper
import logger
import requests
import skylink
import account
import xbmc
import xbmcaddon
import xbmcgui
import urlparse
import xbmcplugin

_id = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = xbmc.translatePath(_addon.getAddonInfo('profile')).decode("utf-8")
_handle = int(sys.argv[1])


def select_device(devices):
    dialog = xbmcgui.Dialog()
    items = []
    for device in devices:
        items.append(device['name'].replace("+", " "))
    return dialog.select(_addon.getLocalizedString(30403), items)

def get_account(id):
    if id == 'sk':
        return account.Account('sk', xbmcplugin.getSetting(_id, 'username_sk'), xbmcplugin.getSetting(_id, 'password_sk'), 'skylink.sk')

    if id == 'cz':
        return account.Account('cz', xbmcplugin.getSetting(_id, 'username_cz'), xbmcplugin.getSetting(_id, 'password_cz'), 'skylink.cz')

    return account.Account('unknown', '', '', '')

def play(account_id, channel_id):
    account = get_account(account_id)

    if not account.is_valid():
        exit(1)

    logger.log.info('Play channel %s from %s' % (channel_id, account.provider))
    sl = skylink.Skylink(account, _profile)

    info = {}
    try:
        info = sl.channel_info(channel_id)
    except skylink.TooManyDevicesException as e:
        d = select_device(e.devices)
        if d > -1:
            logger.log.info('reconnecting as: ' + e.devices[d]['id'])
            sl.reconnect(e.devices[d]['id'])
            info = sl.channel_info(channel_id)
    except requests.exceptions.ConnectionError:
        dialog = xbmcgui.Dialog()
        dialog.ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30506))

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
    if 'account' in args and 'channel' in args:
        play(str(args['account'][0]), str(args['channel'][0]))