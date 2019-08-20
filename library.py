# -*- coding: utf-8 -*-
# Author: cache-sk
# Created on: 20.8.2019
import sys
import inputstreamhelper
import xbmcaddon
import xbmcgui
import xbmcplugin
import urllib
import utils

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()

TYPES = [
    {'msg':_addon.getLocalizedString(30801), 'code':'movies', 'data':{'z':'movies4cat','cs':'37178378331'}},
    {'msg':_addon.getLocalizedString(30802), 'code':'series', 'data':{'z':'series4cat','cs':'1591'}}
]
CATEGORIES = [
    {'msg':_addon.getLocalizedString(30810), 'code':'Action'},
    {'msg':_addon.getLocalizedString(30811), 'code':'Comedy'},
    {'msg':_addon.getLocalizedString(30812), 'code':'Family'},
    {'msg':_addon.getLocalizedString(30813), 'code':'Kids'},
    {'msg':_addon.getLocalizedString(30814), 'code':'Science Fiction'},
    {'msg':_addon.getLocalizedString(30815), 'code':'Fantasy'},
    {'msg':_addon.getLocalizedString(30816), 'code':'Adventure'},
    {'msg':_addon.getLocalizedString(30817), 'code':'Crime'},
    {'msg':_addon.getLocalizedString(30818), 'code':'Drama'},
    {'msg':_addon.getLocalizedString(30819), 'code':'Romance'},    
    {'msg':_addon.getLocalizedString(30820), 'code':'Thriller'},
    {'msg':_addon.getLocalizedString(30821), 'code':'Horror'},
    {'msg':_addon.getLocalizedString(30822), 'code':'Documentary'},
    {'msg':_addon.getLocalizedString(30823), 'code':'Biography'},
    {'msg':_addon.getLocalizedString(30824), 'code':'History'},
    {'msg':_addon.getLocalizedString(30825), 'code':'Music'},
    {'msg':_addon.getLocalizedString(30826), 'code':'Sport'},
    {'msg':_addon.getLocalizedString(30827), 'code':'Other'},
    {'msg':_addon.getLocalizedString(30828), 'code':'Erotic'}
]



def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urllib.urlencode(kwargs, 'utf-8'))

def types():
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30800))
    for tp in TYPES:
        list_item = xbmcgui.ListItem(label=tp['msg'])
        list_item.setInfo('video', {'title': tp['msg']})
        link = get_url(library='category', ctype=tp['code'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def categories(ctype):
    title = _addon.getLocalizedString(30800)
    for tp in TYPES:
        if tp['code'] == ctype:
            title += ' \ ' + tp['msg']
            break
    xbmcplugin.setPluginCategory(_handle, title)

    for cat in CATEGORIES:
        list_item = xbmcgui.ListItem(label=cat['msg'])
        list_item.setInfo('video', {'title': cat['msg']})
        list_item.setArt({'icon': 'DefaultGenre.png'})
        link = get_url(library='list', ctype=ctype, category=cat['code'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def listOfItems(sl, ctype, category):
    title = _addon.getLocalizedString(30800)
    ctp = None
    for tp in TYPES:
        if tp['code'] == ctype:
            ctp = tp
            title += ' \ ' + tp['msg']
            break
    cat = None
    for ct in CATEGORIES:
        if ct['code'] == ctype:
            cat = ct
            title += ' \ ' + ct['msg']
            break
    xbmcplugin.setPluginCategory(_handle, title)

    if ctp is None or cat is None:
        #TODO error!
        pass

    #https://livetv.skylink.cz/m7cziphone/capi.aspx?z=movies4cat&v=4&cs=37178378331&c=Action&os=skylink7,filmboxcz,m7fvfecz,banaxigo,m7svaxn,amc,viasat
    types = ctp['data'].copy()
    types.update({'c':category})

    items = utils.call(sl, lambda: sl.library(types))

    for item in items:
        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setInfo('video', {'title': item['title']}) #, 'plot':item['description'] in series
        list_item.setArt({'thumb': item['poster']})
        list_item.setProperty('IsPlayable', 'true')
        link = get_url(library='play', lid=item['id'])
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def play(sl, lid):
    info = utils.call(sl, lambda: sl.library_info(lid))

    if info and not 'error' in info:
        is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=info['path'])
            playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
            playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
            playitem.setProperty('inputstream.adaptive.license_key', info['key'])
            xbmcplugin.setResolvedUrl(_handle, True, playitem)
        return

    #TODO error!
    xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())

def router(args, sl):
    if args:
        if args['library'][0] == 'category':
            categories(args['ctype'][0])
        elif args['library'][0] == 'list':
            listOfItems(sl, args['ctype'][0], args['category'][0])
        elif args['library'][0] == 'play':
            play(sl, args['lid'][0])
        else:
            types()
    else:
        types()


    #owners - https://livetv.skylink.cz/m7cziphone/capi.aspx?z=owners&d=3&v=5
    #kategorie? - https://livetv.skylink.cz/m7cziphone/capi.aspx?z=catcounts&os=skylink7,filmboxcz,m7fvfecz,banaxigo,m7svaxn,amc,viasat&v=4
    #zoznam - https://livetv.skylink.cz/m7cziphone/capi.aspx?z=movies4cat&v=4&cs=37178378331&c=Action&os=skylink7,filmboxcz,m7fvfecz,banaxigo,m7svaxn,amc,viasat
    #detail - https://livetv.skylink.cz/m7cziphone/capi.aspx?z=moviedetails&d=3&v=4&m=79007&cs=37186922715
    #more like - https://livetv.skylink.cz/m7cziphone/capi.aspx?a=slcz&lng=cs&i=79007&os=filmboxcz&z=morelike&v=5&im=v&om=v&cs=37178378331
    #stream - https://livetv.skylink.cz/m7cziphone/capi.aspx?d=3&u=w78f2ba70-a7ea-11e9-be82-cf65ecb88c92&z=movieurl&v=5&id=79007

    #titulky!!!! - https://livetv.skylink.cz/m7cziphone/capi.aspx?z=subtitle&id=44118&lng=cz
    #'subs' v detaile

    #platene - n: "SD" v deals v liste?