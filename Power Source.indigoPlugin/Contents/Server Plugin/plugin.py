#!/usr/bin/env python2.5

import time
import pmset

# TODO track state changes and only warn on transitions:
# e.g. "battery level critical" -> "battery level normal"
# e.g. "external power lost" -> "external power restored"

################################################################################
class Plugin(indigo.PluginBase):

    #---------------------------------------------------------------------------
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self._loadPluginPrefs(pluginPrefs)

    #---------------------------------------------------------------------------
    def __del__(self):
        indigo.PluginBase.__del__(self)

    #---------------------------------------------------------------------------
    def deviceStartComm(self, device):
        self.logger.debug(u'Starting device: %s', device.name)
        self._updateDevice(device)

    #---------------------------------------------------------------------------
    def deviceStopComm(self, device):
        self.logger.debug(u'Stopping device: %s', device.name)

    #---------------------------------------------------------------------------
    def getBatteryNameList(self, filter='', valuesDict=None, typeId='', targetId=0):
        battNames = []
        batts = pmset.getBatteryInfo()

        if len(batts) < 1:
            battNames.append('- No Batteries Found -')

        for batt in batts:
            battNames.append(batt.name)

        return battNames

    #---------------------------------------------------------------------------
    def refreshDeviceStatus(self):
        self.logger.info(u'Updating all devices.')
        self._updateAllDevices()

    #---------------------------------------------------------------------------
    def runConcurrentThread(self):
        try:

            while not self.stopThread:
                self._runLoopStep()

        except self.StopThread:
            pass

    #---------------------------------------------------------------------------
    def _loadPluginPrefs(self, values):
        logLevelTxt = values.get('logLevel', None)

        if logLevelTxt is None:
            self.logLevel = 20
        else:
            logLevel = int(logLevelTxt)
            self.logLevel = logLevel

        self.indigo_log_handler.setLevel(self.logLevel)

    #---------------------------------------------------------------------------
    def _runLoopStep(self):
        # devices are updated when added, so we'll start with a sleep
        updateInterval = self._getCurrentUpdateInterval();
        self.logger.debug(u'Next update in %f minutes' % updateInterval)

        # sleep for the designated time (convert to seconds)
        self.sleep(updateInterval * 60)

        self._updateAllDevices()

    #---------------------------------------------------------------------------
    def _getCurrentUpdateInterval(self):
        isCritical = False

        # TODO it would be nice if we could just use the information collected
        # during a device update; the issue would be that users won't always add
        # all batteries to their list of devices - so we have to call it here
        batts = pmset.getBatteryInfo()

        # XXX maybe we only care about critical device states if users add them?

        # we allow floats in case users choose less than 1 minute for updates
        critThresh = float(self.pluginPrefs.get('critThreshold', 20))

        for batt in batts:
            if batt.level <= critThresh:
                self.logger.warn(u'Critical battery level: %s', batt.name)
                isCritical = True

        interval = 0

        if isCritical:
            interval = float(self.pluginPrefs.get('critUpdateInt', 1))
        else:
            interval = float(self.pluginPrefs.get('stdUpdateInt', 5))

        return interval

    #---------------------------------------------------------------------------
    def _updateAllDevices(self):
        for device in indigo.devices.itervalues('self'):
            if device.enabled:
                self._updateDevice(device)
            else:
                self.logger.debug(u'Device disabled: %s', device.name)

    #---------------------------------------------------------------------------
    def _updateDevice(self, device):
        self.logger.debug(u'Update device: %s', device.name)

        typeId = device.deviceTypeId

        if typeId == 'PowerSupply':
            self._updateDevice_PowerSupply(device)
        elif typeId == 'Battery':
            self._updateDevice_Battery(device)

    #---------------------------------------------------------------------------
    def _updateDevice_Battery(self, device):
        name = device.pluginProps['name']
        self.logger.debug(u'Updating battery: %s', name)

        batt = pmset.getBatteryInfo(name)

        if batt is None:
            self.logger.error(u'Unknown battery: %s', name)

        else:
            self.logger.debug(u'Battery: %s, [%d] - %s', batt.name, batt.level, batt.status)

            device.updateStateOnServer('level', batt.level)
            device.updateStateOnServer('status', batt.status)
            device.updateStateOnServer('displayStatus', '%d%%' % batt.level)
            device.updateStateOnServer('lastUpdatedAt', time.strftime('%c'))

    #---------------------------------------------------------------------------
    def _updateDevice_PowerSupply(self, device):
        power = pmset.getCurrentPowerInfo()

        self.logger.debug(u'Power source: %s [%s]', power.source,
            'external' if power.isExternal else 'internal'
        )

        device.updateStateOnServer('source', power.source)
        device.updateStateOnServer('hasExternalPower', power.isExternal)
        device.updateStateOnServer('displayStatus', 'on' if power.isExternal else 'off')
        device.updateStateOnServer('lastUpdatedAt', time.strftime('%c'))

