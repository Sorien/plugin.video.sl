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
import replay
import utils

_id = int(sys.argv[1])
_addon = xbmcaddon.Addon()

def play(account_id, channel_id, askpin):
    sl = utils.get_provider(account_id)

    if not sl:
        return

    logger.log.info('Play channel %s from %s' % (channel_id, sl.account.provider))

    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
            return


    info = {}

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
    if 'account' in args and 'channel' in args:
        play(str(args['account'][0]), str(args['channel'][0]), str(args['askpin'][0]) if 'askpin' in args else 'False')
    elif 'replay' in args:
        replay.router(args)
    else:
        xbmcplugin.setPluginCategory(_id, '')
        xbmcplugin.setContent(_id, 'videos')
        xbmcplugin.addDirectoryItem(_id, replay.get_url(replay='channels'), xbmcgui.ListItem(label=_addon.getLocalizedString(30600)), True)
        xbmcplugin.endOfDirectory(_id)

