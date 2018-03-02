#!/usr/bin/env python

from nvidia import Nvidia
from config import Config
import time
from log import Log
import os
import signal
import sys
from pynvml import *
from version import Version

class GPUStatD:
  def __init__(self):
    Config().load()

    if len(sys.argv) >1 and sys.argv[1] == "--silent":
      Log().silent()

    Log().add('info', 'gpustatd %s starting up' % (Version().get()))

    if self.already_running():
      Log().add('fatal', 'gpustatd is already running')

    self.create_pid_file()
    self.throttled = []

    self.target_temperature = Config().get('target_temperature')
    self.fan_speed_temperature_ratio = Config().get('fan_speed_temperature_ratio')
    os.environ["DISPLAY"] = ":%d" % (Config().get('xorg_display_no'))

    Log().add('info', 'scanning devices')
    self.devices = Nvidia().refresh(True)
    self.speeds = {}

    for device_id in self.devices.keys():
      self.speeds[device_id] = self.devices[device_id]['fan']

    self.self_test()


  def already_running(self):
    if not os.path.exists("/var/run/gpustatd"):
      try:
        ok.mkdir("/var/run/gpustatd", 0755)
      except:
        Log().add('fatal', 'unable to create /var/run/gpustatd')

    if os.path.exists("/var/run/gpustatd/gpustatd.pid"):
      pid = open("/var/run/gpustatd/gpustatd.pid").read().rstrip()

      return pid.isdigit() and os.path.exists("/proc/%s" % (pid))


  def create_pid_file(self):
    if self.already_running():
      Log().add('fatal', 'unable to start, there is another gpustatd process running')

    with open("/var/run/gpustatd/gpustatd.pid", "w") as f:
      f.write("%d" % (os.getpid()))


  def self_test(self):
    self.fan_states = {}

    Log().add('info', 'self-test')

    self.do_self_test()

    Log().add('info', 'looks good, monitoring')

    signal.signal(signal.SIGINT, self.sigint_handler)
    signal.signal(signal.SIGTERM, self.sigint_handler)
    signal.signal(signal.SIGHUP, self.sighup_handler)

    self.start()


  def sighup_handler(self):
    Log().add('info', 'HUP received, reloading config')

    Config().load()


  def sigint_handler(self, a, b):
    Log().add('info', 'interrupt received, setting fans to 85% and cards to default power limit')

    Nvidia().set_all_fans(85)

    for device_id in self.devices.keys():
      if self.devices[device_id]['default_power_limit_f']:
        Nvidia().set_power_limit(device_id, self.devices[device_id]['default_power_limit_f'])

    sys.exit(0)


  def do_self_test(self):
    for device_id in self.devices.keys():
      device = self.devices[device_id]
      if not "ignore_devices" in Config().keys() or not Config().get('ignore_devices') or device['id'] not in Config().get('ignore_devices'):
        if not Nvidia().set_fan_control_state(device['id'], 1):
          Log().add('fatal', 'failed to toggle the fan control state for device: %d' % (device['id']))
        self.fan_states[device['id']] = True
        self.regulate_power_level(device, True)

    return True


  def start(self):
    i = 0

    while True:
      if i % 10 == 0:
        self.devices = Nvidia().refresh(True)
      else:
        self.devices = Nvidia().refresh()

      for device_id in self.devices.keys():
        device = self.devices[device_id]
        if "ignore_devices" in Config().keys() and Config().get('ignore_devices') and device['id'] in Config().get('ignore_devices'):
          continue

        self.speeds[device_id] = self.calculate_fan_speed(device)
        self.regulate_power_level(device)

      self.adjust_fan_speeds()

      if "automatically_reload_config_on_change" in Config().keys() and Config().get("automatically_reload_config_on_change"):
        if Config().reload_if_changed():
          self.target_temperature = Config().get('target_temperature')
          self.fan_speed_temperature_ratio = Config().get('fan_speed_temperature_ratio')
          os.environ["DISPLAY"] = ":%d" % (Config().get('xorg_display_no'))

      time.sleep(1)
      i += 1


  def ensure_control_state(self, device_id, state):
    if self.fan_states[device_id] != state:
      Nvidia().set_fan_control_state(device_id, state)
      self.fan_states[device_id] = state


  def calculate_fan_speed(self, device):
    if device['gpu_t_i'] >= self.target_temperature:
      fan_speed = 100
    else:
      fan_speed = 100 - ((self.target_temperature - device['gpu_t_i']) * self.fan_speed_temperature_ratio)

    if fan_speed <0:
      fan_speed = 20

    return fan_speed


  def adjust_fan_speeds(self):
    fan_speed_changes = {}

    for device_id in self.devices.keys():
      if self.devices[device_id]['fan'] != self.speeds[device_id]:
        if Config().get('informative'):
          Log().add('debug', '%d: device temp: %s  target temperature: %s  target fan speed: %d' % (device_id, self.devices[device_id]['gpu_t_i'], self.target_temperature, self.speeds[device_id]))

        fan_speed_changes[device_id] = self.speeds[device_id]

    if len(fan_speed_changes) >0:
      Nvidia().apply_fan_speed_changes(fan_speed_changes)


  def regulate_power_level(self, device, force=False):
    card_limit = Config().get("temperature_limit")

    if not card_limit:
      card_limit = 80

    if os.path.exists("/var/run/minotaur/%d.powerlimit" % (device['id'])):
      desired_limit = float(open("/var/run/minotaur/%d.powerlimit" % (device['id'])).read())
    else:
      desired_limit = device['default_power_limit_f']

    temp = device['gpu_t_i']
    limit = device['limit_f']

    if temp >= card_limit:
      deduction = 10 * (2 ** (temp - card_limit))

      new_limit = desired_limit - deduction

      if new_limit < device['min_power_limit_f']:
        new_limit = device['min_power_limit_f']

      if new_limit != limit:
        Log().add('warning', 'device %d: temperature is at %dC, throttling power limit to %dW' % (device['id'], temp, new_limit))
        Nvidia().set_power_limit(device['id'], new_limit)

        if not device['id'] in self.throttled:
          self.throttled.append(device['id'])
    else:
      if device['id'] in self.throttled and limit < desired_limit:
        Log().add('info', 'device %d: temperature is at %dC, restoring optimum power limit of %dW' % (device['id'], temp, desired_limit))

        Nvidia().set_power_limit(device['id'], desired_limit)

        self.throttled.remove(device['id'])
      elif force:
        if int(device['limit_f']) != int(desired_limit):
          Log().add('info', 'device %d: setting power limit %dW' % (device['id'], desired_limit))
          Nvidia().set_power_limit(device['id'], desired_limit)

GPUStatD()
