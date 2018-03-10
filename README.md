# indigo-pmset

This Indigo plugin provides a basic interface to pmset for monitoring power settings,
battery levels and supply status.  The devices allow a user to trigger on power failures /
restoration, battery levels, etc.

You can run the command `pmset -g batt` to see the data used by this plugin.

## Configuration

Update intervals in the plugin config are used to define how frequently power information
should be collected.

The plugin will update device states depending on the current power status.  If any
batteries are below the critical threshold, the plugin will use the "critical update
interval" to refresh device states.  Otherwise, the "standard update interval" will be
used.

## Devices

This plugin does not automatically create devices.  Instead, create the devices for any
of the batteries or power supplies you wish to monitor.  These device types are explained
below.

In the future, I'll add a menu option to generate devices.

### Power Supply

Represents the main power supply for the computer.

### Battery

Represents a battery known to the computer.  The plugin will automatically detect the
available batteries and present them to the user.

## Triggers & Actions

This plugin does not provide any triggers or actions.  Instead, by creating devices to
represent batteries and power supplies, you can use any trigger or action in Indigo with
the Power Source device states.
