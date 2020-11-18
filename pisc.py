# -*- coding: utf-8 -*-
# Author: cache-sk
# Created on: 21.10.2019
import os
import xbmcgui
import xbmcaddon

def set_pisc():
    _self = xbmcaddon.Addon(id='plugin.video.sl')
    try:
        _pisc = xbmcaddon.Addon(id='pvr.iptvsimple')
    except:
        xbmcgui.Dialog().ok(_self.getAddonInfo('name'), _self.getLocalizedString(30392))
        return

    _playlist_generate = 'true' == _self.getSetting('playlist_generate')
    _epg_generate = 'true' == _self.getSetting('epg_generate')

    if not _playlist_generate and not _epg_generate:
        xbmcgui.Dialog().ok(_self.getAddonInfo('name'), _self.getLocalizedString(30393))
        return

    if not xbmcgui.Dialog().yesno(_self.getAddonInfo('name'), _self.getLocalizedString(30394)):
        return

    if _playlist_generate:
        path = os.path.join(_self.getSetting('playlist_folder'), _self.getSetting('playlist_file'))
        _pisc.setSetting('m3uPathType','0')
        _pisc.setSetting('m3uPath',path)
        _pisc.setSetting('startNum','1')

    if _epg_generate:
        path = os.path.join(_self.getSetting('epp_folder'), _self.getSetting('epg_file'))
        _pisc.setSetting('epgPath',path)
        _pisc.setSetting('epgPathType','0')
        _pisc.setSetting('epgTimeShift','0')
        _pisc.setSetting('epgTSOverride','false')
        _pisc.setSetting('logoPathType','1')
        _pisc.setSetting('logoBaseUrl','')
        _pisc.setSetting('logoFromEpg','2')
    
    xbmcgui.Dialog().ok(_self.getAddonInfo('name'), _self.getLocalizedString(30395))

set_pisc()