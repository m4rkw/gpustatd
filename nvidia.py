#!/usr/bin/env python

import re
import os
import sys
import time
import yaml
import glob
import signal
from version import Version
from config import Config
from log import Log
from singleton import Singleton
from pynvml import *

class Nvidia(object):
  __metaclass__ = Singleton

  def __init__(self):
    os.environ["DISPLAY"] = ":%d" % (Config().get('xorg_display_no'))

    self.data_dir = "/var/run/gpustatd"
    self.devices = {}

    nvmlInit()

    self.handles = {}

    for line in os.popen("/usr/bin/nvidia-smi -L").read().rstrip().split("\n"):
      match = re.match("^GPU ([\d]+): (.*?) \(", line)
      if match:
        device_id = int(match.group(1))

        name = match.group(2)
        name = re.sub("^GeForce GTX ", "", name).replace(" ", "")

        handle = nvmlDeviceGetHandleByIndex(device_id)
        self.handles[device_id] = handle

        power_contraints = nvmlDeviceGetPowerManagementLimitConstraints(handle)

        default_power_limit = nvmlDeviceGetPowerManagementDefaultLimit(handle) / 1000

        self.devices[device_id] = {
          'id': device_id,
          'name': name,
          'has_fan': False,
          'min_power_limit_f': power_contraints[0] / 1000,
          'min_power_limit': '%d W' % (power_contraints[0] / 1000),
          'max_power_limit_f': power_contraints[1] / 1000,
          'max_power_limit': '%d W' % (power_contraints[1] / 1000),
          'default_power_limit_f': default_power_limit,
          'default_power_limit': '%d W' % (default_power_limit),
        }

    device_id = None

    for line in os.popen("/usr/bin/nvidia-settings -q fans 2>/dev/null").read().rstrip().split("\n"):
      match = re.match("^[\t\s]*\[([\d]+)\]", line)
      if match:
        device_id = int(match.group(1))
      if re.match("^[\s\t]*FAN-", line):
        self.devices[device_id]['has_fan'] = True


  def update_yaml(self, devices):
    device_ids = []

    for device_id in devices.keys():
      with open("%s/%d.yml.new" % (self.data_dir, devices[device_id]['id']), "w") as f:
        f.write(yaml.dump(devices[device_id]))
      os.rename("%s/%d.yml.new" % (self.data_dir, devices[device_id]['id']), "%s/%d.yml" % (self.data_dir, devices[device_id]['id']))

      device_ids.append(devices[device_id]['id'])

    for filename in glob.glob("%s/*.yml" % (self.data_dir)):
      device_id = filename.split("/")[-1].split(".")[0]

      if device_id.isdigit() and int(device_id) not in device_ids:
        os.remove(filename)


  def refresh(self, include_fans=False):
    for device_id in sorted(self.devices.keys()):
      util = nvmlDeviceGetUtilizationRates(self.handles[device_id])

      self.devices[device_id]['gpu_t_i'] = nvmlDeviceGetTemperature(self.handles[device_id], 0)
      self.devices[device_id]['gpu_t'] = '%d C' % (self.devices[device_id]['gpu_t_i'])
      self.devices[device_id]['power_f'] = float(nvmlDeviceGetPowerUsage(self.handles[device_id])) / 1000
      self.devices[device_id]['power'] = '%.2f W' % (self.devices[device_id]['power_f'])
      self.devices[device_id]['limit_f'] = nvmlDeviceGetEnforcedPowerLimit(self.handles[device_id]) / 1000
      self.devices[device_id]['limit'] = '%d W' % (self.devices[device_id]['limit_f'])
      self.devices[device_id]['gpu_u_i'] = util.gpu
      self.devices[device_id]['gpu_u'] = '%d %%' % (util.gpu)
      self.devices[device_id]['mem_u_i'] = util.memory
      self.devices[device_id]['mem_u'] = '%d %%' % (util.memory)
      self.devices[device_id]['gpu_f'] = '%d MHz' % (nvmlDeviceGetClockInfo(self.handles[device_id], 0))
      self.devices[device_id]['mem_f'] = '%d MHz' % (nvmlDeviceGetClockInfo(self.handles[device_id], 2))
      self.devices[device_id]['ps'] = 'P%d' % (nvmlDeviceGetPowerState(self.handles[device_id]))

    if include_fans:
      fan_speeds = self.get_all_fan_speeds()

      for device_id in self.devices.keys():
        if device_id in fan_speeds.keys():
          self.devices[device_id]['fan'] = fan_speeds[device_id]
        else:
          self.devices[device_id]['fan'] = None

    self.update_yaml(self.devices)

    return self.devices


  def get_all_fan_speeds(self):
    command = "/usr/bin/nvidia-settings"

    fan_map = {}
    i = 0

    for device_id in self.devices:
      if self.devices[device_id]['has_fan']:
        command += " -q '[fan:%d]/GPUTargetFanSpeed'" % (device_id)
        fan_map[i] = device_id
        i += 1

    if not Config().get('debug'):
      command += " 2>&1"

    resp = os.popen(command).read().rstrip()

    speeds = {}
    i = 0

    match = re.findall("Attribute.*?GPUTargetFanSpeed.*?\(.*?\):[\s\t\r\n]+([\d]+)", resp, re.MULTILINE)

    for m in match:
      speeds[fan_map[i]] = int(m)
      i += 1

    return speeds


  def set_fan_control_state(self, device_id, state):
    state = 1 if state else 0

    if not Config().get('debug'):
      suppress = '1>/dev/null 2>/dev/null'
    else:
      suppress = ''

    return os.system("/usr/bin/nvidia-settings -a '[gpu:%d]/GPUFanControlState=%d' %s" % (device_id, state, suppress)) == 0


  def get_fan_speed(self, device_id):
    return self.devices[device_id]['fan']


  def set_fan_speed(self, device_id, speed):
    if not Config().get('debug'):
      suppress = '1>/dev/null 2>/dev/null'
    else:
      suppress = ''

    if os.system("/usr/bin/nvidia-settings -a '[fan:%d]/GPUTargetFanSpeed=%d' %s" % (device_id, speed, suppress)) == 0:
      self.devices[device_id]['fan'] = speed
      self.update_yaml(self.devices)
      return True

    return False


  def apply_fan_speed_changes(self, speeds):
    cmd = "/usr/bin/nvidia-settings"

    for device_id in speeds.keys():
      cmd += " -a '[fan:%d]/GPUTargetFanSpeed=%d'" % (device_id, speeds[device_id])

    if not Config().get('debug'):
      cmd += " 1>/dev/null 2>/dev/null"

    if os.system(cmd) == 0:
      for device_id in speeds.keys():
        self.devices[device_id]['fan'] = speeds[device_id]
      self.update_yaml(self.devices)
      return True

    return False


  def set_all_fans(self, speed):
    cmd = "/usr/bin/nvidia-settings"

    for device_id in self.devices.keys():
      cmd += " -a '[fan:%d]/GPUTargetFanSpeed=%d'" % (device_id, speed)

    if not Config().get('debug'):
      cmd += " 1>/dev/null 2>/dev/null"

    if os.system(cmd) == 0:
      for device_id in self.devices.keys():
        self.devices[device_id]['fan'] = speed
      self.update_yaml(self.devices)
      return True

    return False



  def set_power_limit(self, device_id, watts):
    return os.system("/usr/bin/nvidia-smi -i %d --power-limit=%d 1>/dev/null 2>/dev/null" % (device_id, watts)) == 0
