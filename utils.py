# -*- coding: utf-8 -*-
# Author: cache
# Created on: 15.4.2019

import xbmcaddon
import xbmcgui
import skylink
import requests
import logger

_addon = xbmcaddon.Addon()

def strip_devices(devices):
    strip = _addon.getSetting('device_web_only') == 'true'
    if not strip:
        return devices
    stripped = []
    for device in devices:
        if device['type'] == 'web':
            stripped.append(device)
    if stripped == []:
        dialog = xbmcgui.Dialog()
        dialog.ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30506))

    return stripped
    

def select_device(devices):
    devices = strip_devices(devices)
    dialog = xbmcgui.Dialog()
    items = []
    for device in devices:
        items.append(device['name'].replace("+", " "))
    d = dialog.select(_addon.getLocalizedString(30403), items)
    return devices[d]['id'] if d > -1 else ''


def get_last_used_device(devices):
    devices = strip_devices(devices)
    la = 9999999999999
    device = ''
    for d in devices:
        if d['lastactivity'] < la:
            device = d['id']
            la = d['lastactivity']
    return device


def call(sl, fn):
    result = None
    try:
        result = fn()
    except skylink.TooManyDevicesException as e:
        if _addon.getSetting('reuse_last_device') == 'true':
            device = get_last_used_device(e.devices)
        else:
            device = select_device(e.devices)

        if device != '':
            logger.log.info('reconnecting as: ' + device)
            sl.reconnect(device)
            result = fn()
    except requests.exceptions.ConnectionError:
        dialog = xbmcgui.Dialog()
        dialog.ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30506))

    return result
    
def ask_for_pin(sl):
    pin = sl.pin_info()
    if pin is not None:
        dialog = xbmcgui.Dialog()
        d = dialog.input(_addon.getLocalizedString(30508), type=xbmcgui.INPUT_NUMERIC)
        if d != pin:
            dialog.ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30509))
            return False
    return True
