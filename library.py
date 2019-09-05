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
from collections import Mapping

_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()

TYPES = [
    {'msg':_addon.getLocalizedString(30801), 'code':'movies', 'isMovie':True, 'data':{'z':'movies4cat','cs':'37178378331', 'v':'4'}},
    {'msg':_addon.getLocalizedString(30802), 'code':'series', 'isMovie':False, 'data':{'z':'series4cat','cs': '1591', 'v':'4'}} #mask? 1 | 2 | 4 | 16 | 32 | 512 | 1024
]
CATEGORIES = [
    {'msg':_addon.getLocalizedString(30810), 'code':'Action', 'pin':False},
    {'msg':_addon.getLocalizedString(30811), 'code':'Comedy', 'pin':False},
    {'msg':_addon.getLocalizedString(30812), 'code':'Family', 'pin':False},
    {'msg':_addon.getLocalizedString(30813), 'code':'Kids', 'pin':False},
    {'msg':_addon.getLocalizedString(30814), 'code':'Science Fiction', 'pin':False},
    {'msg':_addon.getLocalizedString(30815), 'code':'Fantasy', 'pin':False},
    {'msg':_addon.getLocalizedString(30816), 'code':'Adventure', 'pin':False},
    {'msg':_addon.getLocalizedString(30817), 'code':'Crime', 'pin':False},
    {'msg':_addon.getLocalizedString(30818), 'code':'Drama', 'pin':False},
    {'msg':_addon.getLocalizedString(30819), 'code':'Romance', 'pin':False},
    {'msg':_addon.getLocalizedString(30820), 'code':'Thriller', 'pin':False},
    {'msg':_addon.getLocalizedString(30821), 'code':'Horror', 'pin':False},
    {'msg':_addon.getLocalizedString(30822), 'code':'Documentary', 'pin':False},
    {'msg':_addon.getLocalizedString(30823), 'code':'Biography', 'pin':False},
    {'msg':_addon.getLocalizedString(30824), 'code':'History', 'pin':False},
    {'msg':_addon.getLocalizedString(30825), 'code':'Music', 'pin':False},
    {'msg':_addon.getLocalizedString(30826), 'code':'Sport', 'pin':False},
    {'msg':_addon.getLocalizedString(30827), 'code':'Other', 'pin':False},
    {'msg':_addon.getLocalizedString(30828), 'code':'Erotic', 'pin':True}
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

def categories(sl, ctype):
    title = _addon.getLocalizedString(30800)
    for tp in TYPES:
        if tp['code'] == ctype:
            title += ' / ' + tp['msg']
            break
    xbmcplugin.setPluginCategory(_handle, title)

    for cat in CATEGORIES:
        if (cat['pin'] and sl._show_pin_protected) or not cat['pin']:
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
            title += ' / ' + tp['msg']
            break
    cat = None
    for ct in CATEGORIES:
        if ct['code'] == category:
            cat = ct
            title += ' / ' + ct['msg']
            break
    xbmcplugin.setPluginCategory(_handle, title)

    if ctp is None or cat is None:
        xbmcgui.Dialog().ok(heading=_addon.getLocalizedString(30800), line1=_addon.getLocalizedString(30806))
        xbmcplugin.endOfDirectory(_handle)
        return

    if cat['pin'] and not utils.ask_for_pin(sl):
        xbmcplugin.endOfDirectory(_handle)
        return


    #get possible owners
    owners_data = utils.call(sl, lambda: sl.library_owners())
    products_data = utils.call(sl, lambda: sl.products())
    owners = []
    os = u''

    for owner in owners_data:
        valid = True
        owner.update({'pin':int(owner['flags']) & 4 > 0}) #TODO brutforced test!!!
        if owner['pin'] and not sl._show_pin_protected: 
            valid = False
        else:
            for product in products_data:
                if owner['name'] == product['name'] and not product['owned']:
                    valid = False
        if valid:
            owners.append(owner)

    params = ctp['data'].copy()
    params.update({'c':category, 'os':','.join([o['id'] for o in owners])})

    items = utils.call(sl, lambda: sl.library(params))

    for item in items:
        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setInfo('video', {'title': item['title'], 'plot':item['description'] if 'description' in item else ''})
        list_item.setArt({'thumb': item['poster']})
        link = get_url(library='play' if ctp['isMovie'] else 'episodes', lid=item['id'], ctype=ctype)
        is_folder = not ctp['isMovie']
        if ctp['isMovie']:
            list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

def episodes(sl, lid, ctype):
    ctp = None
    for tp in TYPES:
        if tp['code'] == ctype:
            ctp = tp
            break
    if ctp is None:
        xbmcgui.Dialog().ok(heading=_addon.getLocalizedString(30800), line1=_addon.getLocalizedString(30806))
        xbmcplugin.endOfDirectory(_handle)
        return

    params = {'z':'seriesdetails','cs':'1591','d':'3', 'v':'4', 'lng': sl._lang, 'a': sl._app, 'm':lid} #cs:2
    data = utils.call(sl, lambda: sl.library(params))
    xbmcplugin.setPluginCategory(_handle, data['title'])

    params = {'z':'seasonsforseries','os':data['owner'], 's':lid}
    series = utils.call(sl, lambda: sl.library(params))
    
    for serie in series:
        sz = serie[0]
        prefix = 'S' + sz + ' '
        params = {'z':'episodesforseason','v':'4','cs':'37178378331','sz':sz,'os':data['owner'], 's':lid}
        episodes = utils.call(sl, lambda: sl.library(params))
        for episode in episodes:
            list_item = xbmcgui.ListItem(label=prefix + episode['title'])
            list_item.setInfo('video', {
                'title': prefix + episode['title'],
                'duration':int(episode['duration'])*60
            })
            list_item.setArt({'thumb': episode['poster']})
            list_item.setProperty('IsPlayable', 'true')
            link = get_url(library='play', lid=episode['id'], ctype=ctype)
            is_folder = False
            xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(_handle)

def play(sl, lid, ctype):
    ctp = None
    for tp in TYPES:
        if tp['code'] == ctype:
            ctp = tp
            break
    if ctp is None:
        xbmcgui.Dialog().ok(heading=_addon.getLocalizedString(30800), line1=_addon.getLocalizedString(30806))
        xbmcplugin.endOfDirectory(_handle)
        return

    #show plot
    params = {'z':'moviedetails','cs':'37186922715','d':'3', 'v':'4', 'm':lid}
    data = utils.call(sl, lambda: sl.library(params))

    if 'description' not in data or xbmcgui.Dialog().yesno(heading=data['title'], line1=data['description'], nolabel=_addon.getLocalizedString(30804), yeslabel=_addon.getLocalizedString(30803)):
        params = {}
        if 'deals' in data and data['deals'] and 'n' in data['deals'][0]:
            params.update({'dn':data['deals'][0]['n']})
        info = utils.call(sl, lambda: sl.library_info(lid,params))
        if info and not 'error' in info:
            is_helper = inputstreamhelper.Helper(info['protocol'], drm=info['drm'])
            if is_helper.check_inputstream():
                playitem = xbmcgui.ListItem(path=info['path'])
                playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                playitem.setProperty('inputstream.adaptive.manifest_type', info['protocol'])
                playitem.setProperty('inputstream.adaptive.license_type', info['drm'])
                playitem.setProperty('inputstream.adaptive.license_key', info['key'])
                
                if 'subs' in data:
                    params = {'z':'subtitle', 'lng': sl._lang, 'id':lid}
                    subs = utils.call(sl, lambda: sl.library(params))
                    if 'url' in subs:
                        playitem.setSubtitles([subs['url']])
                video_info = {}

                if 'title' in data:
                    video_info.update({'title': data['title']})

                if 'description' in data:
                    video_info.update({'plot':data['description']})
                
                if 'director' in data:
                    video_info.update({'director':data['director']})

                playitem.setInfo('video', video_info)

                if 'actors' in data:
                    playitem.setCast([{'name':a} for a in data['actors']])

                if 'poster' in data:
                    playitem.setArt({'thumb': data['poster']})

                xbmcplugin.setResolvedUrl(_handle, True, playitem)
            return
        xbmcgui.Dialog().ok(heading=data['title'], line1=_addon.getLocalizedString(30805))

    xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())

def router(args, sl):
    if args:
        if args['library'][0] == 'category':
            categories(sl, args['ctype'][0])
        elif args['library'][0] == 'list':
            listOfItems(sl, args['ctype'][0], args['category'][0])
        elif args['library'][0] == 'episodes':
            episodes(sl, args['lid'][0], args['ctype'][0])
        elif args['library'][0] == 'play':
            play(sl, args['lid'][0], args['ctype'][0])
        else:
            types()
    else:
        types()
