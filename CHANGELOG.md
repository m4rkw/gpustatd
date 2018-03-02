````
29/01/18 - 0.1 - initial release
29/01/18 - 0.2 - minor bugfix
30/01/18 - 0.3 - alert if fan speed == 0
01/02/18 - 0.4 - changes:
- added debug mode
- only allow one instance of fantotaur to be running
03/02/18 - 0.5 - changes:
- added "always monitor" config option
06/02/18 - 0.6 - changes:
- simplified and remove excavator API code
07/02/18 - 0.7 - changes:
- fixed auto config reload
12/02/18 - 0.8 - handle SIGINT/SIGTERM appropriately
12/02/18 - 0.8.1 - added fan speed floor
12/02/18 - 0.8.5 changes:
- replaced nvidia-smi with nvml
- indicate version on startup
15/02/18 - 0.9 changes:
- fanotaur is now gpustatd
18/02/18 - 1.0 changes:
- instead of restoring device fan control on exit, set fans to 85% and
set the default power limit
19/02/18 - 1.1 bugfix for setting appropriate power limits on startup
19/02/18 - 1.1.1: only set the power limit if its wrong
19/02/18 - 1.1.2: safety fix
19/02/18 - 1.1.3: switched to NVML
19/02/18 - 1.1.4: only invoke nvidia-settings once when setting fan speeds
````
