# -*- coding: utf-8 -*-
# Author: cache
# Created on: 11.4.2019
import sys
import inputstreamhelper
import logger
import requests
import skylink
import exports
import xbmc
import xbmcaddon
import xbmcgui
import urlparse
import urllib
import xbmcplugin
import datetime
import os
import utils

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_skylink_logos = 'false' != xbmcplugin.getSetting(_handle, 'a_sl_logos')
if not _skylink_logos:
    _remote_logos = '1' == xbmcplugin.getSetting(_handle, 'a_logos_location')
    if _remote_logos:
        _logos_base_url = xbmcplugin.getSetting(_handle, 'a_logos_base_url')
        if not _logos_base_url.endswith("/"):
            _logos_base_url = _logos_base_url + "/"
    else:
        _logos_folder = xbmcplugin.getSetting(_handle, 'a_logos_folder')

REPLAY_GAP = 5 #gap after program ends til it shows in replay

def get_url(**kwargs):
	return '{0}?{1}'.format(_url, urllib.urlencode(kwargs, 'utf-8'))

def get_logo(title, sl):
    if _skylink_logos:
        return sl.getUrl() + "/" + exports.logo_sl_location(title)
    
    if _remote_logos:
        return _logos_base_url + exports.logo_id(title)

    return os.path.join(_logos_folder, exports.logo_id(title))



def channels():
    providers = utils.get_available_providers()
    channels = []

    for sl in providers:
        channels = channels + utils.call(sl, lambda: sl.channels(True))

    if bool(_addon.getSetting('playlist_unique')):
        channels = utils.unique_channels(channels)

    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600))
    if channels:
        for channel in channels:
            list_item = xbmcgui.ListItem(label=channel['title'])
            list_item.setInfo('video', {'title': channel['title']}) #TODO - genre?
            list_item.setArt({'thumb': get_logo(channel['title'], sl)})
            link = get_url(replay='days', accountid=channel['account'], stationid=channel['stationid'], channel=channel['title'], askpin=channel['pin'])
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def days(accountid, stationid, channel, askpin):
    sl = utils.get_provider(accountid)

    if not sl:
        return

    now = datetime.datetime.now()
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600) + ' / ' + channel)
    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.endOfDirectory(_handle)
            return
    for day in range (0,7):
        d = now - datetime.timedelta(days=day) if day > 0 else now
        title = _addon.getLocalizedString(30601) if day == 0 else _addon.getLocalizedString(30602) if day == 1 else d.strftime('%d. %m.').decode('UTF-8')
        title = _addon.getLocalizedString(int('3061' + str(d.weekday()))) + ', ' + title
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'icon':'DefaultAddonPVRClient.png'})
        link = get_url(replay='programs', accountid=accountid, stationid=stationid, channel=channel, day=day, first=True)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def programs(accountid, stationid, channel, day=0, first=False):
    sl = utils.get_provider(accountid)

    if not sl:
        return

    today = day == 0
    if today:
        now = datetime.datetime.now()

    epg = utils.call(sl, lambda: sl.epg([{'stationid':stationid}], None, day, True))

    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600) + ' / ' + channel)
    if day < 6:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30604))
        list_item.setArt({'icon':'DefaultVideoPlaylists.png'})
        link = get_url(replay='programs', accountid=accountid, stationid=stationid, channel=channel, day=day+1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    if epg:
        for program in epg[0][stationid]:
            start = datetime.datetime.fromtimestamp(program['start'])
            show_item = not today or start + datetime.timedelta(minutes=program['duration']+REPLAY_GAP) < now
            if show_item:
                title = start.strftime('%H:%M').decode('UTF-8')
                title = title[1:] if title.startswith('0') else title
                title = title + ' - ' + program['title']
                list_item = xbmcgui.ListItem(label=title)
                list_item.setInfo('video', {
                    'title': program['title'],
                    'duration': program['duration'] * 60
                })
                if 'cover' in program:
                    cover = sl.getUrl() + "/" + program['cover']
                    list_item.setArt({'thumb': cover, 'icon': cover})
                
                link = get_url(replay='replay', accountid=accountid, locId=program['locId'])
                is_folder = False
                list_item.setProperty('IsPlayable','true')
                xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    if day > 0:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30603))
        list_item.setArt({'icon':'DefaultVideoPlaylists.png'})
        link = get_url(replay='programs', accountid=accountid, stationid=stationid, channel=channel, day=day-1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    xbmcplugin.endOfDirectory(_handle, updateListing=not first)

def replay(accountid, locId):
    sl = utils.get_provider(accountid)

    if not sl:
        return

    info = utils.call(sl, lambda: sl.replay_info(locId))

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            xbmcplugin.setResolvedUrl(_handle, True, playitem)


def router(args):
    if args:
        if args['replay'][0] == 'programs':
            programs(args['accountid'][0], args['stationid'][0], args['channel'][0], int(args['day'][0]) if 'day' in args else 0, 'first' in args)
        elif args['replay'][0] == 'replay':
            replay(args['accountid'][0], args['locId'][0])
        elif args['replay'][0] == 'days':
            days(args['accountid'][0], args['stationid'][0], args['channel'][0], args['askpin'][0])
        else:
            channels()
    else:
        channels()
