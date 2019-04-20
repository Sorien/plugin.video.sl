# -*- coding: utf-8 -*-
# Author: cache
# Created on: 15.4.2019

import xbmcaddon
import xbmcgui
import xbmc
import skylink
import account
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

def unique_channels(channels):
    names_list = []
    channels_list = []
    for channel in channels:
        if not channel['stationid'] in names_list:
            names_list.append(channel['stationid'])
            channels_list.append(channel)

    return channels_list

def get_accounts():
    accounts = []
    profile =  _addon.getAddonInfo('profile')
    cookies_path = xbmc.translatePath(profile).decode("utf-8")

    account_sk = account.Account('sk', _addon.getSetting('username_sk'), _addon.getSetting('password_sk'), 'skylink.sk', cookies_path, bool(_addon.getSetting('pin_protected_content_sk')))
    account_cz = account.Account('cz', _addon.getSetting('username_cz'), _addon.getSetting('password_cz'), 'skylink.cz', cookies_path, bool(_addon.getSetting('pin_protected_content_cz')))
    accounts.append(account_sk)
    accounts.append(account_cz)

    return accounts

def get_account(id):
    profile =  _addon.getAddonInfo('profile')
    cookies_path = xbmc.translatePath(profile).decode("utf-8")

    if id == 'sk':
        return account.Account('sk', _addon.getSetting('username_sk'), _addon.getSetting('password_sk'), 'skylink.sk', cookies_path, bool(_addon.getSetting('pin_protected_content_sk')))
    if id == 'cz':
        return account.Account('cz', _addon.getSetting('username_cz'), _addon.getSetting('password_cz'), 'skylink.cz', cookies_path, bool(_addon.getSetting('pin_protected_content_cz')))

    return None

def get_available_providers():
    accounts = get_accounts()
    providers = []

    for account in accounts:
        if not account.is_valid():
            continue
        providers.append(skylink.Skylink(account))

    return providers

def get_provider(accountid):
    account = get_account(accountid)

    if not account or not account.is_valid():
        return None

    return skylink.Skylink(account)