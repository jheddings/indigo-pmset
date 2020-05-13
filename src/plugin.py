#!/usr/bin/env python2.5

import time
import pmset

import iplug

# TODO track state changes in device states and trigger on transitions:
# e.g. "battery level critical" -> "battery level normal"
# e.g. "external power lost" -> "external power restored"
# -> maybe use this to log warning message, too (instead of on each loop)

################################################################################
class Plugin(iplug.ThreadedPlugin):

    #---------------------------------------------------------------------------
    def deviceStartComm(self, device):
        iplug.ThreadedPlugin.deviceStartComm(self, device)
        self._updateDevice(device)

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
    # all the work of this plugin is performed in the loop delay hooks
    def runLoopStep(self): pass

    #---------------------------------------------------------------------------
    def preLoopDelayHook(self):
        # update the loop delay before the thread sleeps
        self._updateLoopDelay()

    #---------------------------------------------------------------------------
    def postLoopDelayHook(self):
        # we do our work after the sleep since deviceStartComm does an initial update
        self._updateAllDevices()

    #---------------------------------------------------------------------------
    def _updateLoopDelay(self):
        # this plugin configures the polling interval in minutes
        interval = self._getCurrentUpdateInterval()

        # iplug loop delay is in seconds...
        self.threadLoopDelay = (60 * interval)

    #---------------------------------------------------------------------------
    def _getCurrentUpdateInterval(self):
        # we allow floats in case users choose less than 1 minute for updates
        critThresh = self.getPrefAsFloat(self.pluginPrefs, 'critThreshold', 20)

        isCritical = False

        # check the level for all configured batteries
        for device in indigo.devices.itervalues('self.Battery'):
            level = float(device.states.get('level'))

            if (level <= critThresh):
                self.logger.warn(u'Critical battery level: %s [%f]', device.name, level)
                isCritical = True

        # assume we use the standard delay interval...
        interval = self.getPrefAsFloat(self.pluginPrefs, 'stdUpdateInt', 5)

        # ...unless we found a battery below the critical threshold
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

            device.updateStateOnServer('batteryLevel', batt.level)
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

