import sys
import inputstreamhelper
import logger
import skylink
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import replay
import live
import library
import utils
import datetime

_id = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = utils.dec_utf8(xbmc.translatePath(_addon.getAddonInfo('profile')))
_user_name = xbmcplugin.getSetting(_id, 'username')
_password = xbmcplugin.getSetting(_id, 'password')
_provider = 'skylink.sk' if int(xbmcplugin.getSetting(_id, 'provider')) == 0 else 'skylink.cz'
_pin_protected_content = 'false' != xbmcplugin.getSetting(_id, 'pin_protected_content')
_a_show_live = 'false' != xbmcplugin.getSetting(_id, 'a_show_live')
_python3 = sys.version_info[0] >= 3


def play_archive(station_id, catchup_id, askpin):
    logger.log.info('play archive: ' + station_id + ' catchup_id: ' + str(catchup_id))
    sl = skylink.Skylink(_user_name, _password, _profile, _provider)

    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
            return
    try:
        info = utils.call(sl, lambda: sl.replay_info(catchup_id))
    except skylink.StreamNotResolvedException as e:
        xbmcgui.Dialog().ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(e.id))
        xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
        return

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            if (_python3): # Python 3.x
                playitem.setProperty('inputstream', is_helper.inputstream_addon)
            else: # Python 2.5+
                playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            playitem.setProperty('inputstream.adaptive.stream_headers', info['headers'])
            xbmcplugin.setResolvedUrl(_id, True, playitem)


def locId_from_time(sl, stationid, utc):
    now = datetime.datetime.now()
    from_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=7)

    epg = utils.call(sl, lambda: sl.epg([{'stationid': stationid}], from_date, now, False))
    utc = datetime.datetime.fromtimestamp(int(utc))
    if epg:
        for program in epg[0][stationid]:
            start = datetime.datetime.utcfromtimestamp(program['start'])

            if start <= utc <= start + datetime.timedelta(minutes=program['duration']):
                logger.log.info('loc: ' + program['title'] + ',start: ' + str(start) + ',utc: ' + str(utc))
                return program['locId']


def play_archive_utc(station_id, utc, askpin):
    logger.log.info('play archive: ' + station_id + 'utc: ' + utc)
    sl = skylink.Skylink(_user_name, _password, _profile, _provider)

    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
            return
    try:
        info = utils.call(sl, lambda: sl.replay_info(locId_from_time(sl, station_id, utc)))
    except skylink.StreamNotResolvedException as e:
        xbmcgui.Dialog().ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(e.id))
        xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
        return

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            playitem.setProperty('inputstream.adaptive.stream_headers', info['headers'])
            xbmcplugin.setResolvedUrl(_id, True, playitem)


def play(channel_id, askpin):
    logger.log.info('play: ' + channel_id)
    sl = skylink.Skylink(_user_name, _password, _profile, _provider)

    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
            return
    try:
        info = utils.call(sl, lambda: sl.channel_info(channel_id))
    except skylink.StreamNotResolvedException as e:
        xbmcgui.Dialog().ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(e.id))
        xbmcplugin.setResolvedUrl(_id, False, xbmcgui.ListItem())
        return

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            if (_python3): # Python 3.x
                playitem.setProperty('inputstream', is_helper.inputstream_addon)
            else: # Python 2.5+
                playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            playitem.setProperty('inputstream.adaptive.stream_headers', info['headers'])
            xbmcplugin.setResolvedUrl(_id, True, playitem)


if __name__ == '__main__':
    args = utils.parse_qs(sys.argv[2][1:])
    if 'id' in args:
        play(str(args['id'][0]), str(args['askpin'][0]) if 'askpin' in args else 'False')
    elif ('stationid' in args) and ('catchup_id' in args):
        play_archive(
            str(args['stationid'][0]),
            str(args['catchup_id'][0]) if 'catchup_id' in args else None,
            str(args['askpin'][0]) if 'askpin' in args else 'False')
    elif 'replay' in args:
        replay.router(args, skylink.Skylink(_user_name, _password, _profile, _provider, _pin_protected_content))
    elif 'live' in args:
        live.router(args, skylink.Skylink(_user_name, _password, _profile, _provider, _pin_protected_content))
    elif 'library' in args:
        library.router(args, skylink.Skylink(_user_name, _password, _profile, _provider, _pin_protected_content))
    else:
        xbmcplugin.setPluginCategory(_id, '')
        xbmcplugin.setContent(_id, 'videos')
        if _a_show_live:
            xbmcplugin.addDirectoryItem(_id, live.get_url(live='channels'), xbmcgui.ListItem(label=_addon.getLocalizedString(30700)), True)
        xbmcplugin.addDirectoryItem(_id, replay.get_url(replay='channels'), xbmcgui.ListItem(label=_addon.getLocalizedString(30600)), True)
        xbmcplugin.addDirectoryItem(_id, library.get_url(library='types'), xbmcgui.ListItem(label=_addon.getLocalizedString(30800)), True)
        xbmcplugin.endOfDirectory(_id)
