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

class SkylinkMonitor(xbmc.Monitor):
    _addon = None
    _next_update = 0

    def __init__(self):
        xbmc.Monitor.__init__(self)
        self._addon = xbmcaddon.Addon()
        ts = self._addon.getSetting('next_update')
        self._next_update = datetime.datetime.now() if ts == '' else datetime.datetime.fromtimestamp(float(ts))
    
    def __del__(self):
        logger.log.info('service destroyed')

    def notify(self, text, error=False):
        ltext = text = text.encode("utf-8") if type(text) is unicode else text
        icon = 'DefaultIconError.png' if error else '' #u
        logger.log.info(str(type(icon)) + ' - ' + icon)
        logger.log.info(str(type(self._addon.getAddonInfo('name').encode("utf-8"))) + ' - ' + self._addon.getAddonInfo('name').encode("utf-8"))
        logger.log.info(str(type(text)) + ' - ' + ltext)
        xbmc.executebuiltin('Notification("%s","%s",5000, %s)' % (self._addon.getAddonInfo('name').encode("utf-8"), ltext, icon)) #u

    def onSettingsChanged(self):
        self._addon = xbmcaddon.Addon() #refresh for updated settings!
        if not self.abortRequested():
            try:
                res = self.update(True)
                self.notify(self._addon.getLocalizedString(30400 + res))
            except skylink.SkylinkException as e:
                self.notify(self._addon.getLocalizedString(e.id), True)

    def shedule_next(self, seconds):
        dt = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        logger.log.info('Next update %s' % dt)
        self._next_update = dt

    def update(self, try_reconnect=False):
        providers = utils.get_available_providers()
        channels = []

        for sl in providers:
            logger.log.info('Getting channels for account: %s' % (sl.account.username))

            try:
                channels = channels + sl.channels()
            except skylink.TooManyDevicesException as e:
                if self._addon.getSetting('reuse_last_device') == 'true':
                    device = utils.get_last_used_device(e.devices)
                else:
                    device = utils.select_device(e.devices) if try_reconnect else ''

                if device != '':
                    logger.log.info('reconnecting as: ' + device)
                    sl.reconnect(device)
                    channels = channels + sl.channels()
                else:
                    raise

        # Remove duplicate channels (same channels provided by skylink.sk and skylink.cz)
        if bool(self._addon.getSetting('playlist_unique')):
            logger.log.info('Filtering channels to create unique list...')
            channels = utils.unique_channels(channels)

        logger.log.info('Updating playlist [%d channels]' % len(channels))
        try:
            path = os.path.join(self._addon.getSetting('playlist_folder'), self._addon.getSetting('playlist_file'))
            _skylink_logos = 'true' == self._addon.getSetting('sl_logos')
            exports.create_m3u(channels, path, sl.getUrl() + '/' if _skylink_logos else None)
            result = 1
        except IOError as e:
            logger.log.error(str(e))
            raise skylink.SkylinkException(30503)

        if bool(self._addon.getSetting('epg_generate')):
            days = int(self._addon.getSetting('epg_days'))
            logger.log.info('Updating EPG [%d days from %s]' % (days, datetime.datetime.now()))
            path = os.path.join(self._addon.getSetting('epp_folder'), self._addon.getSetting('epg_file'))
            try:
                exports.create_epg(channels, sl.epg(channels, datetime.datetime.now(), days), path, self._addon, sl.getUrl() + '/')
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
                self.notify(self._addon.getLocalizedString(e.id), True)

    def save(self):
        self._addon.setSetting('next_update', str(time.mktime(self._next_update.timetuple())))
        logger.log.info('Saving next update %s' % self._next_update)


if __name__ == '__main__':
    monitor = SkylinkMonitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            monitor.save()
            break
        monitor.tick()
