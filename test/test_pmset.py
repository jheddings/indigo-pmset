#!/usr/bin/env python2.7

import logging
import unittest

import pmset

# keep logging output to a minumim for testing
logging.basicConfig(level=logging.ERROR)

################################################################################
class PowerInfoTestCase(unittest.TestCase):

    #---------------------------------------------------------------------------
    def _assertPowerInfo(self, raw, isExternal):
        power = pmset._parsePowerInfo(raw.strip())

        self.assertIsNotNone(power.source)
        self.assertEqual(power.isExternal, isExternal)

    #---------------------------------------------------------------------------
    def _assertBatteryInfo(self, raw, battName, battLevel):
        batts = pmset._parseBatteryInfo(raw.strip())
        self.assertEqual(len(batts), 1)

        batt = batts[0]
        self.assertEqual(batt.name, battName)
        self.assertEqual(batt.level, battLevel)
        self.assertIsNotNone(batt.status)

################################################################################
class InternalBatteryParsing(PowerInfoTestCase):

    #---------------------------------------------------------------------------
    def test_ConnectedToPowerFullyCharged(self):
        raw = '''
Now drawing from 'AC Power'
 -InternalBattery-0	100%; charged; 0:00 remaining present: true
'''
        self._assertPowerInfo(raw, True)
        self._assertBatteryInfo(raw, 'InternalBattery-0', 100)

    #---------------------------------------------------------------------------
    def test_DisconnectedFromPower(self):
        raw = '''
Now drawing from 'Battery Power'
 -InternalBattery-0	93%; discharging; (no estimate) present: true
'''
        self._assertPowerInfo(raw, False)
        self._assertBatteryInfo(raw, 'InternalBattery-0', 93)

    #---------------------------------------------------------------------------
    def test_ConnectedToPowerNotCharging(self):
        raw = '''
Now drawing from 'Battery Power'
 -InternalBattery-0	91%; AC attached; not charging present: true
'''
        self._assertPowerInfo(raw, False)
        self._assertBatteryInfo(raw, 'InternalBattery-0', 91)

    #---------------------------------------------------------------------------
    def test_DischargingWithID(self):
        raw = '''
Now drawing from 'Battery Power'
 -InternalBattery-0 (id=4587619)  40%; discharging; 3:03 remaining present: true
'''
        self._assertPowerInfo(raw, False)
        self._assertBatteryInfo(raw, 'InternalBattery-0', 40)

    #---------------------------------------------------------------------------
    def test_ChargingWithID(self):
        raw = '''
Now drawing from 'AC Power'
 -InternalBattery-0 (id=4587619)  39%; AC attached; not charging present: true
'''
        self._assertPowerInfo(raw, True)
        self._assertBatteryInfo(raw, 'InternalBattery-0', 39)

################################################################################
class ExternalBatteryParsing(PowerInfoTestCase):

    #---------------------------------------------------------------------------
    def test_ConnectedAndCharging(self):
        raw = '''
Now drawing from 'AC Power'
 -Back-UPS RS1000G FW:868.L5 -P.D USB FW:L5 -P  (id=15400960)	85%; charging present: true
'''
        self._assertPowerInfo(raw, True)
        self._assertBatteryInfo(raw, 'Back-UPS', 85)

    #---------------------------------------------------------------------------
    def test_ConnectedAndFullyCharged(self):
        raw = '''
Now drawing from 'AC Power'
 -UPS CP600	100%; charging present: true
'''
        self._assertPowerInfo(raw, True)
        self._assertBatteryInfo(raw, 'UPS', 100)

    #---------------------------------------------------------------------------
    def test_Discharging(self):
        raw = '''
Currently drawing from 'UPS Power'
 -UPS CP600	100%; discharging; 0:37 remaining
'''
        self._assertPowerInfo(raw, False)
        self._assertBatteryInfo(raw, 'UPS', 100)

    #---------------------------------------------------------------------------
    def test_Charging(self):
        raw = '''
Currently drawing from 'AC Power'
 -UPS CP600	48%; charging
'''
        self._assertPowerInfo(raw, True)
        self._assertBatteryInfo(raw, 'UPS', 48)

