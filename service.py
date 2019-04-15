import datetime
import os
import time
import requests
import exports
import logger
import skylink
import xbmc
import xbmcaddon
import xbmcgui
import utils

_addon = xbmcaddon.Addon()

class SkylinkMonitor(xbmc.Monitor):

    _next_update = 0

    def __init__(self):
        xbmc.Monitor.__init__(self)
        ts = _addon.getSetting('next_update')
        self._next_update = datetime.datetime.now() if ts == '' else datetime.datetime.fromtimestamp(float(ts))

    def notify(self, text, error=False):
        icon = u'DefaultIconError.png' if error else ''
        logger.log.info(str(type(icon)) + ' - ' + icon)
        logger.log.info(str(type(_addon.getAddonInfo('name').encode("utf-8"))) + ' - ' + _addon.getAddonInfo('name').encode("utf-8"))
        logger.log.info(str(type(text)) + ' - ' + text)
        xbmc.executebuiltin(u'Notification("%s","%s",5000, %s)' % (_addon.getAddonInfo('name').encode("utf-8"), text, icon))

    #def get_last_used_device(self, devices):
    #    la = 9999999999999
    #    device = ''
    #    for d in devices:
    #        if d['lastactivity'] < la:
    #            device = d['id']
    #            la = d['lastactivity']
    #    return device
    #
    #def select_device(self, devices):
    #    dialog = xbmcgui.Dialog()
    #    items = []
    #    for device in devices:
    #        items.append(device['name'].replace("+", " "))
    #    d = dialog.select(_addon.getLocalizedString(30403), items)
    #    return devices[d]['id'] if d > -1 else ''

    def onSettingsChanged(self):
        if not self.abortRequested():
            try:
                res = self.update(True)
                self.notify(_addon.getLocalizedString(30400 + res))
            except skylink.SkylinkException as e:
                self.notify(_addon.getLocalizedString(e.id), True)

    def shedule_next(self, seconds):
        dt = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        logger.log.info('Next update %s' % dt)
        self._next_update = dt

    def update(self, try_reconnect=False):
        sl = skylink.Skylink(_addon.getSetting('username'), _addon.getSetting('password'),
                             xbmc.translatePath(_addon.getAddonInfo('profile')),
                             'skylink.sk' if int(_addon.getSetting('provider')) == 0 else 'skylink.cz')

        try:
            channels = sl.channels()
        except skylink.TooManyDevicesException as e:
            if _addon.getSetting('reuse_last_device') == 'true':
                device = utils.get_last_used_device(e.devices)
            else:
                device = utils.select_device(e.devices) if try_reconnect else ''

            if device != '':
                logger.log.info('reconnecting as: ' + device)
                sl.reconnect(device)
                channels = sl.channels()
            else:
                raise

        logger.log.info('Updating playlist [%d channels]' % len(channels))
        try:
            path = os.path.join(_addon.getSetting('playlist_folder'), _addon.getSetting('playlist_file'))
            _skylink_logos = 'true' == _addon.getSetting('sl_logos')
            exports.create_m3u(channels, path, sl.getUrl() + '/' if _skylink_logos else None)
            result = 1
        except IOError as e:
            logger.log.error(str(e))
            raise skylink.SkylinkException(30503)

        if bool(_addon.getSetting('epg_generate')):
            days = int(_addon.getSetting('epg_days'))
            logger.log.info('Updating EPG [%d days from %s]' % (days, datetime.datetime.now()))
            path = os.path.join(_addon.getSetting('epp_folder'), _addon.getSetting('epg_file'))
            try:
                exports.create_epg(channels, sl.epg(channels, datetime.datetime.now(), days), path, _addon, sl.getUrl() + '/')
                result = 2
            except IOError as e:
                logger.log.error(str(e))
                raise skylink.SkylinkException(30504)

        return result

    def tick(self):
        if datetime.datetime.now() > self._next_update:
            try:
                self.shedule_next(12 * 60 * 60)
                self.update()
            except skylink.UserNotDefinedException:
                pass
            except requests.exceptions.ConnectionError:
                self.shedule_next(60)
                logger.log.info('Can''t update, no internet connection')
                pass
            except skylink.SkylinkException as e:
                self.notify(_addon.getLocalizedString(e.id), True)

    def save(self):
        _addon.setSetting('next_update', str(time.mktime(self._next_update.timetuple())))
        logger.log.info('Saving next update %s' % self._next_update)


if __name__ == '__main__':
    monitor = SkylinkMonitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            monitor.save()
            break

        monitor.tick()
