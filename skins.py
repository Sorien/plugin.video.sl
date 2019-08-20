# -*- coding: utf-8 -*-
# Author: cache-sk
# Created on: 12.6.2019
import xbmc
import xbmcgui
import xbmcaddon
import shutil
import xbmcvfs
from contextlib import closing
import xml.etree.ElementTree as ET
import time
import random

SKINS = {'skin.estuary':'Estuary','skin.confluence':'Confluence'}

def cleanup(copy_settings, destination, destsettings):
    shutil.rmtree(xbmc.translatePath(destination))
    if copy_settings:
        shutil.rmtree(xbmc.translatePath(destsettings))

def modify():
    __language__ = xbmcaddon.Addon(id='plugin.video.sl').getLocalizedString
    if not xbmcgui.Dialog().yesno(xbmc.getLocalizedString(19194), __language__(30372)):
        return
    
    skin = xbmc.getSkinDir() #simplified skin detection
    if skin not in SKINS:
        xbmcgui.Dialog().ok(__language__(30373), __language__(30374))
        return

    newSkin = skin + '.skylink'
    newName = SKINS[skin] + '.Skylink'

    xbmc.executebuiltin( 'XBMC.ReloadSkin()' )

    destination = 'special://home/addons/' + newSkin
    destsettings = 'special://userdata/addon_data/' + newSkin
    if xbmcvfs.exists(destination + "/"):
        xbmcgui.Dialog().ok(newName, __language__(30375))
        xbmc.executebuiltin("ActivateWindow(10040,addons://user/xbmc.gui.skin,return)")
        return
    if not xbmcvfs.exists(destsettings + "/"):
        copy_settings = xbmcgui.Dialog().yesno(SKINS[skin], __language__(30376))
    else:
        copy_settings = False
    
    try:
        shutil.copytree(xbmc.translatePath('special://skin'), xbmc.translatePath(destination))
        #alter copy addon.xml
        with closing(xbmcvfs.File(destination + '/addon.xml')) as f:
            addonxml = f.read()
        addonxml = addonxml.replace(skin,newSkin)
        addonxml = addonxml.replace('name="' + SKINS[skin] + '"','name="' + newName + '"')
        with closing(xbmcvfs.File(destination + '/addon.xml', 'w')) as f:
            f.write(addonxml)
        if copy_settings:
            #TODO special://profile
            shutil.copytree(xbmc.translatePath('special://userdata/addon_data/' + skin), xbmc.translatePath(destsettings))

        #update language
        enpo = destination + '/language/resource.language.en_gb/strings.po'
        skpo = destination + '/language/resource.language.sk_sk/strings.po'
        czpo = destination + '/language/resource.language.cs_cz/strings.po'
        with closing(xbmcvfs.File(enpo)) as f:
            enstrings = f.read()
        with closing(xbmcvfs.File(skpo)) as f:
            skstrings = f.read()
        with closing(xbmcvfs.File(czpo)) as f:
            czstrings = f.read()
        
        newId = str(random.randint(31000,31999))
        newIdString = '"#' + newId + '"'
        while newIdString in enstrings or newIdString in skstrings or newIdString in czstrings:
            newId = str(random.randint(31000,31999))
            newIdString = '"#' + newId + '"'
        
        enstrings += '\nmsgctxt ' + newIdString + '\nmsgid "Skylink Archive"\nmsgstr "Skylink Archive"\n'
        skstrings += '\nmsgctxt ' + newIdString + '\nmsgid "Skylink Archive"\nmsgstr "Skylink Archív"\n'
        czstrings += '\nmsgctxt ' + newIdString + '\nmsgid "Skylink Archive"\nmsgstr "Skylink Archiv"\n'

        with closing(xbmcvfs.File(enpo, 'w')) as f:
            f.write(enstrings)
        with closing(xbmcvfs.File(skpo, 'w')) as f:
            f.write(skstrings)
        with closing(xbmcvfs.File(czpo, 'w')) as f:
            f.write(czstrings)

        #update widgets
        if skin == 'skin.estuary':
            xmlfile = destination + '/xml/Includes_Home.xml'
            with closing(xbmcvfs.File(xmlfile)) as f:
                xml = f.read()
            root = ET.fromstring(xml)
            content = root.findall("include[@name='PVRSubMenuContent']/content")
            if len(content) != 1:
                cleanup(copy_settings, destination, destsettings)
                xbmcgui.Dialog().ok(SKINS[skin], __language__(30377))
                return
            content = content[0]
            
            toRemove = []
            for item in content:
                for child in item:
                    if child.tag == 'onclick' and 'Search' in child.text:
                        searchItem = item
                    if child.tag == 'onclick' and ('Recordings' in child.text or 'Timer' in child.text):
                        toRemove.append(item)

            index = list(content).index(searchItem) + 1
            newItem = ET.fromstring(
                '<item>\n'+
                    '\t\t\t<label>$LOCALIZE[' + newId + ']</label>\n'+
                    '\t\t\t<onclick>ActivateWindow(10025,plugin://plugin.video.sl/?replay=channels,return)</onclick>\n'+
                    '\t\t\t<thumb>special://home/addons/plugin.video.sl/icon-archive.png</thumb>\n'+
                    '\t\t\t<visible>System.HasAddon(plugin.video.sl)</visible>\n'+
                '</item>\n\t\t')
            content.insert(index, newItem)

            for item in toRemove:
                content.remove(item)

            with closing(xbmcvfs.File(xmlfile, 'w')) as f:
                f.write(ET.tostring(root,encoding="utf-8"))
            
        elif skin == 'skin.confluence':
            xmlfile = destination + '/720p/IncludesHomeMenuItems.xml'
            with closing(xbmcvfs.File(xmlfile)) as f:
                xml = f.read()
            print(xml)
            root = ET.fromstring(xml)
            print(root)
            content = root.findall("include[@name='HomeSubMenuTV']")
            if len(content) != 1:
                print(content)
                print(len(content))
                cleanup(copy_settings, destination, destsettings)
                xbmcgui.Dialog().ok(SKINS[skin], __language__(30377))
                return
            content = content[0]
            
            toRemove = []
            for control in content:
                for child in control:
                    if child.tag == 'onclick' and 'TVSearch' in child.text:
                        searchControl = control
                    if child.tag == 'onclick' and ('TVRecordings' in child.text or 'TVTimer' in child.text):
                        toRemove.append(control)

            index = list(content).index(searchControl) + 1
            if len(toRemove) == 0:
                cleanup(copy_settings, destination, destsettings)
                xbmcgui.Dialog().ok(SKINS[skin], __language__(30377))
                return

            newControl = ET.fromstring(
                '<control type="button" id="' + toRemove[0].attrib['id'] + '">\n'+
                    '\t\t\t<include>ButtonHomeSubCommonValues</include>\n'+
                    '\t\t\t<label>' + newId + '</label>\n'+
                    '\t\t\t<onclick>ActivateWindow(10025,plugin://plugin.video.sl/?replay=channels,return)</onclick>\n'+
                    '\t\t\t<visible>System.HasAddon(plugin.video.sl)</visible>\n'
                '</control>\n\t\t')
            content.insert(index, newControl)

            for control in toRemove:
                content.remove(control)

            with closing(xbmcvfs.File(xmlfile, 'w')) as f:
                f.write(ET.tostring(root,encoding="utf-8"))
    except:
        cleanup(copy_settings, destination, destsettings)
        xbmcgui.Dialog().ok(SKINS[skin], __language__(30377))
        return

    xbmc.executebuiltin("UpdateLocalAddons")
    time.sleep(1)
    try:
        #try enabling skin
        xbmc.startServer(xbmc.SERVER_WEBSERVER, True,True)
        time.sleep(1)
        params = '"method":"Addons.SetAddonEnabled","params":{"addonid":"' + newSkin + '","enabled":true}'
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", %s, "id": 1}' % params)
        #xbmc.executebuiltin("ActivateWindow(10040,addons://user/xbmc.gui.skin,return)")
        if xbmcgui.Dialog().yesno(newName, __language__(30378)):
            try: #try activate skin
                xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skin","value":"'+newSkin+'"}}')
                xbmc.executebuiltin('SendClick(11)')
                time.sleep(1)
                xbmc.executebuiltin( 'XBMC.ReloadSkin()' )
                xbmcgui.Dialog().ok(newName, xbmc.getLocalizedString(20177))
            except:
                xbmcgui.Dialog().ok(newName, __language__(30379))
                xbmc.executebuiltin("ActivateWindow(10032,return)")
    except:
        xbmcgui.Dialog().ok(newName, __language__(30380))
        xbmc.executebuiltin("ActivateWindow(10040,addons://user/xbmc.gui.skin,return)")

modify()