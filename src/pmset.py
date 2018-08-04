#!/usr/bin/env python2.5

import re
import subprocess

from xml.dom import minidom
from collections import namedtuple

PowerInfo = namedtuple('PowerInfo', ['source', 'isExternal'])
BatteryInfo = namedtuple('BatteryInfo', ['name', 'level', 'status'])

################################################################################
def getCurrentPowerInfo():
    rawOutput = _pmset('batt')
    return _parsePowerInfo(rawOutput)

################################################################################
def getBatteryInfo(name=None):
    rawOutput = _pmset('batt')

    batts = _parseBatteryInfo(rawOutput)
    if name is None: return batts

    for batt in batts:
        if batt.name == name:
            return batt

    return None

################################################################################
def _pmset(cmd):
    proc = subprocess.Popen(['pmset', '-g', cmd], stdout=subprocess.PIPE)
    out, err = proc.communicate()
    return out.strip()

################################################################################
def _parsePowerInfo(rawOutput):
    if rawOutput is None: return None

    match = re.search('drawing\s*from\s*["\'](.+)["\']', rawOutput)
    if not match: return None

    power = PowerInfo(
        source = match.group(1),
        isExternal = 'AC' in match.group(1)
    )

    return power

################################################################################
def _parseBatteryLine(line):
    match = re.search(r'-([^\s]+).*\b(\d+)%;\s*([^;]+)', line.strip())
    if not match: return None

    return BatteryInfo(
        name = match.group(1),
        level = int(match.group(2)),
        status = match.group(3)
    )

################################################################################
def _parseBatteryInfo(rawOutput):
    if rawOutput is None: return None
    batts = map(_parseBatteryLine, rawOutput.splitlines())
    return [batt for batt in batts if batt is not None]

################################################################################
def _printPowerInfo(power):
    if power:
        print('Power source: %s [%s]' % (
            power.source, 'external' if power.isExternal else 'internal'
        ))
    else:
        print('None')

################################################################################
def _printBatteries(batts):
    if batts and len(batts) > 0:
        for batt in batts:
            _printBatteryInfo(batt)
    else:
        print('None')

################################################################################
def _printBatteryInfo(batt):
    if batt:
        print(' -%s [%s%%] %s' % (batt.name, batt.level, batt.status))
    else:
        print('None')

################################################################################
def _runTestCase(tc):
    id = tc.attributes['id'].value
    name = tc.attributes['name'].value
    rawOutput = tc.firstChild.nodeValue.strip()

    print('--BEGIN TEST [%s]: %s--' % (id, name))

    power = _parsePowerInfo(rawOutput)
    _printPowerInfo(power)

    batts = _parseBatteryInfo(rawOutput)
    _printBatteries(batts)

################################################################################
## TEST ENTRY
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='pmset test interface.')
    parser.add_argument('-c', '--current', action='store_true')
    parser.add_argument('-a', '--all', action='store_true')
    parser.add_argument('tests', metavar='id', type=str, nargs='*', help='test case id')
    args = parser.parse_args()

    doc = minidom.parse('test_cases.xml')
    tests = doc.getElementsByTagName('TestCase')

    if args.current:
        print('--CURRENT POWER INFO--')
        _printPowerInfo(getCurrentPowerInfo())
        _printBatteries(getBatteryInfo())

    for tc in tests:
        id = tc.attributes['id'].value
        if args.all or id in args.tests:
            _runTestCase(tc)

