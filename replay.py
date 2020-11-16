# -*- coding: utf-8 -*-
# Author: cache-sk
# Created on: 11.4.2019
import sys, os, io
import inputstreamhelper
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import urllib
import datetime
import utils
from skylink import StreamNotResolvedException

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_profile = xbmc.translatePath(_addon.getAddonInfo('profile'))

REPLAY_GAP = 5  # gap after program ends til it shows in replay
REPLAY_LAST_GAP = 3*60*60 #gap before program vanish - now - 7 days + last+gap
REPLAY_OFFSET = 3*60 #start offset
REPLAY_LAST_PLAYED = os.path.join(_profile, 'replay_last_played')
if os.path.isfile(REPLAY_LAST_PLAYED):
    os.unlink(REPLAY_LAST_PLAYED)

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, utils.urlencode(kwargs))


def channels(sl):
    channels = utils.call(sl, lambda: sl.channels())
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600))
    if channels:
        for channel in channels:
            if channel['replayable']:
                list_item = xbmcgui.ListItem(label=channel['title'])
                list_item.setInfo('video', {'title': channel['title']})  # TODO - genre?
                list_item.setArt({'thumb': utils.get_logo(channel['title'], sl._api_url)})
                link = get_url(replay='days', stationid=channel['stationid'], channel=channel['title'],
                               askpin=channel['pin'])
                is_folder = True
                xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

#source - http://wontonst.blogspot.com/2017/08/time-until-end-of-day-in-python.html
def time_until_end_of_day(dt=None):
    # type: (datetime.datetime) -> datetime.timedelta
    """
    Get timedelta until end of day on the datetime passed, or current time.
    """
    if dt is None:
        dt = datetime.datetime.now()
    tomorrow = dt + datetime.timedelta(days=1)
    return datetime.datetime.combine(tomorrow, datetime.time.min) - dt


def days(sl, stationid, channel, askpin):
    now = datetime.datetime.now()
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600) + ' / ' + channel)
    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.endOfDirectory(_handle)
            return
    for day in range(0, 8):
        if day < 7 or time_until_end_of_day(now).seconds > REPLAY_LAST_GAP :
            d = now - datetime.timedelta(days=day) if day > 0 else now
            title = _addon.getLocalizedString(30601) if day == 0 else _addon.getLocalizedString(30602) if day == 1 else utils.dec_utf8(d.strftime('%d. %m.'))
            title = _addon.getLocalizedString(int('3061' + str(d.weekday()))) + ', ' + title
            list_item = xbmcgui.ListItem(label=title)
            list_item.setArt({'icon': 'DefaultAddonPVRClient.png'})
            link = get_url(replay='programs', stationid=stationid, channel=channel, day=day, first=True)
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)


def programs(sl, stationid, channel, day=0, first=False):
    today = day == 0
    lastday = day == 7
    now = datetime.datetime.now()
    if today:
        from_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        to_date = now
        start_date = from_date
    elif lastday:
        then = now - datetime.timedelta(days=day)
        start_date = then.replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = then + datetime.timedelta(seconds=REPLAY_LAST_GAP)
        to_date = start_date + datetime.timedelta(days=1)
    else: #other days
        from_date = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=day)
        to_date = from_date + datetime.timedelta(days=1)
        start_date = from_date

    epg = utils.call(sl, lambda: sl.epg([{'stationid': stationid}], from_date, to_date, False))

    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600) + ' / ' + channel)
    if day < 6 or (day == 6 and time_until_end_of_day(now).seconds > REPLAY_LAST_GAP):
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30604))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        link = get_url(replay='programs', stationid=stationid, channel=channel, day=day + 1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    if epg:
        lastLocId = None
        for program in epg[0][stationid]:
            start = datetime.datetime.fromtimestamp(program['start'])
            show_item = (start.replace(hour=0, minute=0, second=0, microsecond=0) - start_date).days == 0 #started today
            if today:
                show_item = show_item and (start + datetime.timedelta(minutes=program['duration'] + REPLAY_GAP) < now)
            if lastday:
                show_item = show_item and (start > then and (start - then).seconds > REPLAY_LAST_GAP)
            if show_item:
                title = utils.dec_utf8(start.strftime('%H:%M'))
                title = title[1:] if title.startswith('0') else title
                title = title + ' - ' + program['title']
                list_item = xbmcgui.ListItem(label=title)
                duration = program['duration'] * 60
                list_item.setInfo('video', {
                    'title': program['title'],
                    'duration': duration
                })
                if 'cover' in program:
                    list_item.setArt({'thumb': program['cover'], 'icon': program['cover']})

                link = get_url(replay='replay', locId=program['locId'], duration=duration, lastLocId=lastLocId)
                lastLocId=program['locId']
                is_folder = False
                list_item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    if day > 0:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30603))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        link = get_url(replay='programs', stationid=stationid, channel=channel, day=day - 1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    xbmcplugin.endOfDirectory(_handle, updateListing=not first)


def replay(sl, locId, duration, lastLocId):
    try:
        info = utils.call(sl, lambda: sl.replay_info(locId))
    except StreamNotResolvedException as e:
        xbmcgui.Dialog().ok(heading=_addon.getAddonInfo('name'), line1=_addon.getLocalizedString(e.id))
        xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
        return
    
    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            if (sys.version_info[0] >= 3): # Python 3.x
                playitem.setProperty('inputstream', is_helper.inputstream_addon)
            else: # Python 2.5+
                playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            lastPlayed = None
            if os.path.isfile(REPLAY_LAST_PLAYED):
                with io.open(REPLAY_LAST_PLAYED, 'r', encoding='utf8') as f:
                    lastPlayed = f.read()
            if 'resume:true' not in sys.argv[3] and lastLocId == lastPlayed:
                playitem.setProperty('ResumeTime', str(REPLAY_OFFSET))
                playitem.setProperty('TotalTime', duration)
            with io.open(REPLAY_LAST_PLAYED, 'w', encoding='utf8') as f:
                lastPlayed = f.write(unicode(locId))
            xbmcplugin.setResolvedUrl(_handle, True, playitem)


def router(args, sl):
    if args:
        if args['replay'][0] == 'programs':
            programs(sl, args['stationid'][0], args['channel'][0], int(args['day'][0]) if 'day' in args else 0, 'first' in args)
        elif args['replay'][0] == 'replay':
            replay(sl, args['locId'][0], args['duration'][0], args['lastLocId'][0])
        elif args['replay'][0] == 'days':
            days(sl, args['stationid'][0], args['channel'][0], args['askpin'][0])
        else:
            channels(sl)
    else:
        channels(sl)
