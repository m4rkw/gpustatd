# gpustatd by m4rkw

gpustatd is a fan control daemon intended for use with Excavator by Nicehash. It
serves as a lightweight and decoupled mechanism for regulating fan speeds on
Nvidia cards when running intensive processes such as mining.


## Disclaimer

Please see the terms of the MIT LICENSE file included in this repo. gpustatd
does not guarantee that your card will stay cool under any conditions. If you
are using this tool to regulate temperatures under high load conditions you
should ensure that you have adequate monitoring

Although it is highly unlikely the author assumes no responsibility for any
damage whatsoever that may occur to your equipment when using this tool.

In testing with the default settings gpustatd consistently ran the fans
faster than the native Nvidia fan regulation.


## Usage

gpustatd monitors your Nvidia devices and regulates the fan speed according to
the card's temperature.


## Configuration

The configuration file should be installed to: /etc/gpustatd.conf

The config options are:

````
target_temperature: 75
fan_speed_temperature_ratio: 3
````

target_temperature is the temperature you want to keep the card at. At this
temperature the fan will run at 100%. The fan_speed_temperature_ratio option
controls how much gpustatd will decrease the fan speed by as the temperature
decreases. A ratio of 3 will drop the fan speed by 3% for every 1C below the
target_temperature.

````
temperature_limit: 80
````

If the card gets to this temperature, gpustatd will begin to throttle the
power limit to get the temperature down.

````
xorg_display_no: 0
````

Xorg is required to use nvidia-settings, so we need to know the display no.

````
automatically_reload_config_on_change: true
````

If this is enabled gpustatd will automatically reload its config when the
configuration file changes.

````
log_file: /var/log/gpustatd/gpustatd.log
logfile_max_size_mb: 100
logfile_max_count: 10
````

Logfile location and rotation config.


## Installation

Just install the RPM, or run through the following steps:

1. install PyYAML

````
sudo pip install PyYAML
````

2. edit gpustatd.conf.example as -> /etc/gpustatd.conf

3. ensure nvidia-settings has +s and that the user that gpustatd will run as has
permissions to use it

4. create /var/log/gpustatd and ensure the gpustatd user can write to it

5. simply run it:

````
./gpustatd.py
````

If you want to suppress the output to stdout, you can run gpustatd with:

````
$ ./gpustatd.py --silent
````

There is also a bash wrapper script to ensure that gpustatd is restarted if it
dies for any reason and a systemd unit so that gpustatd can be installed as a
system service.

If you notice any issues or crashes please file a bug on github.


## Related projects

- Minotaur - https://github.com/m4rkw/minotaur
- Excavataur - https://github.com/m4rkw/excavataur


## Donate

- XMR: 47zb4siDAi691nPW714et9gfgtoHMFnsqh3tKoaW7sKSbNPbv4wBkP11FT7bz5CwSSP1kmVPABNrsMe4Ci1F7Y2qLqT5ozd
- BTC: 1Bs4mCcyDcDCHfEisJqstEsmV5yzYcenJM


## Credits

- Much thanks to @gordan.bobic for packaging and invaluable input into the
  development of this tool
