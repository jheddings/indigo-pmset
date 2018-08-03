#!/usr/bin/env python2.5

import time
import pmset

import iplug

# TODO track state changes and only warn on transitions:
# e.g. "battery level critical" -> "battery level normal"
# e.g. "external power lost" -> "external power restored"

################################################################################
class Plugin(iplug.ThreadedPlugin):

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
    def loadPluginPrefs(self, prefs):
        iplug.ThreadedPlugin.loadPluginPrefs(self, prefs)

        self._updateLoopDelay()

    #---------------------------------------------------------------------------
    def runLoopStep(self):
        self._updateAllDevices()
        self._updateLoopDelay()

    #---------------------------------------------------------------------------
    def _updateLoopDelay(self):
        # this plugin configures the polling interval in minutes
        interval = self._getCurrentUpdateInterval()

        # iplug loop delay is in seconds...
        self.threadLoopDelay = (60 * interval)

    #---------------------------------------------------------------------------
    def _getCurrentUpdateInterval(self):
        # TODO it would be nice if we could just use the information collected
        # during a device update; the issue would be that users won't always add
        # all batteries to their list of devices - so we have to call it here
        batts = pmset.getBatteryInfo()

        # XXX maybe we only care about critical device states if users add them?

        # we allow floats in case users choose less than 1 minute for updates
        critThresh = self.getPrefAsFloat(self.pluginPrefs, 'critThreshold', 20)

        isCritical = False

        for batt in batts:
            if batt.level <= critThresh:
                self.logger.warn(u'Critical battery level: %s [%f]', batt.name, batt.level)
                isCritical = True

        interval = self.getPrefAsFloat(self.pluginPrefs, 'stdUpdateInt', 5)

        if isCritical:
            interval = self.getPrefAsFloat(self.pluginPrefs, 'critUpdateInt', 1)

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

