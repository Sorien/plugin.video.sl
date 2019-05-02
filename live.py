# -*- coding: utf-8 -*-
# Author: cache
# Created on: 23.4.2019
import sys
import inputstreamhelper
import logger
import xbmcaddon
import xbmcgui
import xbmcplugin
import urllib
import datetime
import utils

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
try:
    _a_live_epg_next = int(xbmcplugin.getSetting(_handle, 'a_live_epg_next'))
except:
    logger.log.info('exception, 7 is ok')
    _a_live_epg_next = 7

EPG_GAP = 5  # gap for previous program


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urllib.urlencode(kwargs, 'utf-8'))


def channels(sl):
    channels = utils.call(sl, lambda: sl.channels(False))
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600))
    if channels:
        for channel in channels:
            list_item = xbmcgui.ListItem(label=channel['title'])
            list_item.setInfo('video', {'title': channel['title']})  # TODO - genre?
            list_item.setArt({'thumb': utils.get_logo(channel['title'], sl)})
            list_item.setProperty('IsPlayable', 'true')
            link = get_url(live='play', lid=channel['id'], stationid=channel['stationid'], askpin=channel['pin'])
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)


def play(sl, lid, stationid, askpin):
    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
            return

    # improvised epg
    def get_plot_line(start, title):
        return '[B]' + start.strftime('%H:%M').decode('UTF-8') + '[/B] ' + title + '[CR]'

    plot = ''
    today = datetime.datetime.now()
    epg = utils.call(sl, lambda: sl.epg([{'stationid': stationid}], today, today + datetime.timedelta(days=2)))
    if epg:
        now = datetime.datetime.now()
        last_program = None
        items_left = _a_live_epg_next
        for program in epg[0][stationid]:
            start = datetime.datetime.fromtimestamp(program['start'])
            show_item = start + datetime.timedelta(minutes=program['duration']) > now
            if show_item:
                if last_program is not None:
                    last_start = datetime.datetime.fromtimestamp(last_program['start'])
                    if last_start + datetime.timedelta(minutes=last_program['duration'] + EPG_GAP) > now:
                        plot += + get_plot_line(last_start, last_program['title'])
                        items_left -= 1
                        last_program = None
                plot += get_plot_line(start, program['title'])
                items_left -= 1
                if items_left == 0:
                    break
            else:
                last_program = program
        plot = plot[:-4]

    info = utils.call(sl, lambda: sl.channel_info(lid))

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            if plot:
                playitem.setInfo('video', {'plot': plot})
            playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            xbmcplugin.setResolvedUrl(_handle, True, playitem)


def router(args, sl):
    if args:
        if args['live'][0] == 'play':
            play(sl, args['lid'][0], args['stationid'][0], args['askpin'][0])
        else:
            channels(sl)
    else:
        channels(sl)
