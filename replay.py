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

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()

LOGO_BASE = 'https://koperfieldcz.github.io/skylink-livetv-logos/'
REPLAY_GAP = 5 #gap after program ends til it shows in replay

def get_url(**kwargs):
	return '{0}?{1}'.format(_url, urllib.urlencode(kwargs, 'utf-8'))

def channels(sl):
    try:
        channels = sl.channels(True)
    except skylink.TooManyDevicesException as e:
        if _addon.getSetting('reuse_last_device') == 'true':
            device = get_last_used_device(e.devices)
        else:
            device = select_device(e.devices)

        if device != '':
            logger.log.info('reconnecting as: ' + device)
            sl.reconnect(device)
            info = sl.channel_info(channel_id)
    except requests.exceptions.ConnectionError:
        dialog = xbmcgui.Dialog()
        dialog.ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30506))

    xbmcplugin.setPluginCategory(_handle, '')
    xbmcplugin.setContent(_handle, 'videos')
    if channels:
        for channel in channels:
            logo_id = exports.logo_id(channel['title'])
            list_item = xbmcgui.ListItem(label=channel['title'])
            list_item.setInfo('video', {'title': channel['title']}) #TODO genre?
            list_item.setArt({'thumb': LOGO_BASE + logo_id + '.png',
                                'icon': LOGO_BASE + logo_id + '.png'})
            link = get_url(replay='programs', stationid=channel['stationid'])
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def programs(sl, stationid, day=0, hasDay = False):
    today = day == 0
    if today:
        now = datetime.datetime.now()
    try:
        epg = sl.epg([{'stationid':stationid}], None, day, True)
    except skylink.TooManyDevicesException as e:
        if _addon.getSetting('reuse_last_device') == 'true':
            device = get_last_used_device(e.devices)
        else:
            device = select_device(e.devices)

        if device != '':
            logger.log.info('reconnecting as: ' + device)
            sl.reconnect(device)
            info = sl.channel_info(channel_id)
    except requests.exceptions.ConnectionError:
        dialog = xbmcgui.Dialog()
        dialog.ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30506))

    xbmcplugin.setPluginCategory(_handle, '')
    xbmcplugin.setContent(_handle, 'videos')
    if day > 0:
        list_item = xbmcgui.ListItem(label='previous day TODO')
        link = get_url(replay='programs', stationid=stationid, day=day-1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    if epg:
        for program in epg[0][stationid]:
            show_item = not today or datetime.datetime.fromtimestamp(program['start']) + datetime.timedelta(minutes=program['duration']+REPLAY_GAP) < now
            if show_item:
                list_item = xbmcgui.ListItem(label=program['title'])
                list_item.setInfo('video', {'title': program['title']}) #TODO genre?
                if 'cover' in program:
                    cover = sl.getUrl() + "/" + program['cover']
                    list_item.setArt({'thumb': cover, 'icon': cover})
                
                link = get_url(replay='replay', locId=program['locId'])
                is_folder = False
                list_item.setProperty('IsPlayable','true')
                xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    if day < 6:
        list_item = xbmcgui.ListItem(label='next day TODO')
        link = get_url(replay='programs', stationid=stationid, day=day+1)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    xbmcplugin.endOfDirectory(_handle, updateListing=hasDay)

def replay(sl, locId):
    try:
        info = sl.replay_info(locId)
    except skylink.TooManyDevicesException as e:
        if _addon.getSetting('reuse_last_device') == 'true':
            device = get_last_used_device(e.devices)
        else:
            device = select_device(e.devices)

        if device != '':
            logger.log.info('reconnecting as: ' + device)
            sl.reconnect(device)
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


def router(args, sl):
    if args:
        if args['replay'][0] == 'programs':
            hasDay = 'day' in args
            if hasDay:
                programs(sl, args['stationid'][0], int(args['day'][0]), hasDay)
            else:
                programs(sl, args['stationid'][0])
        elif args['replay'][0] == 'replay':
            replay(sl, args['locId'][0])
        else:
            channels(sl)
    else:
        channels(sl)
