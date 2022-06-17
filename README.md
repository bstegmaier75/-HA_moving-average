# Moving Average Filter

This is a Home Assistant custom component implementing a moving window average filter to be used on top of other entities/sensors.

The main difference to the existing Home Assistant (SMA) Filter sensor is that it delivers changes to the computed average value even if the input sensor does not change.

This is especially useful if the value of the input does not change continuously.
For example, if the input sensor drops to zero and stays there, the Home Assistant SMA Filter will stay at some value different from zero. As long as the input sensor does not change, it will never reach zero. 
In contrast, this Moving Average filter will reach zero latest after the tim eperiod of one window has elapsed.


## Installation

In your `custom_components` location clone files of this repository into a folder called `moving-average`.


## Configuration

To enable, add the following to your `configuration.yaml` file:
```
sensor:
  - platform: moving-average
    name: "Filtered xyz"
    unique_id: xyz_filtered
    entity_id: sensor.xyz
    window_size: "00:05:00"
    scan_interval: "00:00:15"
    timeout: "00:02:00"
    precision: 1
```

## Configuration Variables
#### name
*OPTIONAL*
Name of the moving average sensor.

#### unique_id
*OPTIONAL*
Unique ID of the moving average sensor.

#### entity_id
*REQUIRED*
The entity ID of the sensor to be filtered.

#### window_size
*REQUIRED*
Size of the window. 
Requires a time period in hh:mm:ss format and must be quoted.

#### scan_interval
*OPTIONAL, default: Home Assistant sensor polling default value*
Update interval of moving average. 
Note, that the average value is independently updated when an update of the input sensor is received.
Requires a time period in hh:mm:ss format and must be quoted.

#### timeout
*OPTIONAL, default: 00:01:00*
If the input sensor gets unavailable/unknown or delivers an invalid (non-numeric) state, a timeout will be started. When the timeoout is elapsed, the moving average data window will be reset and the sensor will go to unavailable state. It will resume as soon as the input sensor will again deliver valid data.

#### precision
*OPTIONAL, default: 2*
The returned value is rounded to the given number of decimals.
