# -*- coding: utf-8 -*-
# Author: cache-sk
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
from skylink import StreamNotResolvedException

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
    return '{0}?{1}'.format(_url, utils.urlencode(kwargs))

def generate_plot(epg, chtitle, items_left = _a_live_epg_next):

    def get_plot_line(start, title):
        return '[B]' + utils.dec_utf8(start.strftime('%H:%M')) + '[/B] ' + title + '[CR]'

    plot = u''
    now = datetime.datetime.now()
    last_program = None
    for program in epg:
        start = datetime.datetime.fromtimestamp(program['start'])
        show_item = start + datetime.timedelta(minutes=program['duration']) > now
        if show_item:
            if last_program is not None:
                last_start = datetime.datetime.fromtimestamp(last_program['start'])
                if last_start + datetime.timedelta(minutes=last_program['duration'] + EPG_GAP) > now:
                    plot += get_plot_line(last_start, last_program['title'])
                    items_left -= 1
                    last_program = None
            plot += get_plot_line(start, program['title'] if 'title' in program else chtitle)
            items_left -= 1
            if items_left == 0:
                break
        else:
            last_program = program
    plot = plot[:-4]
    return plot

def channels(sl):
    channelsData = utils.call(sl, lambda: sl.channels())
    today = datetime.datetime.now()
    epg = utils.call(sl, lambda: sl.epg(channelsData, today, today + datetime.timedelta(days=1), False))
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30600))
    if channelsData:
        for channel in channelsData:
            stationid=str(channel['stationid']) #because it is long
            plot = generate_plot([x for x in epg if stationid in x][0][stationid],channel['title'],4) if epg else u''
            list_item = xbmcgui.ListItem(label=channel['title'])
            list_item.setInfo('video', {'title': channel['title'], 'plot': plot})
            list_item.setArt({'thumb': utils.get_logo(channel['title'], sl._api_url)})
            list_item.setProperty('IsPlayable', 'true')
            link = get_url(live='play', lid=channel['id'], stationid=stationid, askpin=channel['pin'])
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def play(sl, lid, stationid, askpin):
    if askpin != 'False':
        pin_ok = utils.ask_for_pin(sl)
        if not pin_ok:
            xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
            return

    today = datetime.datetime.now()
    epg = utils.call(sl, lambda: sl.epg([{'stationid': stationid}], today, today + datetime.timedelta(days=1), False))
    plot = generate_plot(epg[0][stationid],'') if epg else u''

    try:
        info = utils.call(sl, lambda: sl.channel_info(lid))
    except StreamNotResolvedException as e:
        xbmcgui.Dialog().ok(heading=_addon.getAddonInfo('name'), line1=_addon.getLocalizedString(e.id))
        xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
        return

    if info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            if plot:
                playitem.setInfo('video', {'plot': plot})
            if (sys.version_info[0] >= 3): # Python 3.x
                playitem.setProperty('inputstream', is_helper.inputstream_addon)
            else: # Python 2.5+
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
