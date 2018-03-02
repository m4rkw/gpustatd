
from singleton import Singleton
import os
import yaml
import sys

class Config(object):
  __metaclass__ = Singleton

  def load(self):
    self.config_file = "/etc/gpustatd.conf"

    if not os.path.exists(self.config_file):
      print "%s does not exist" % (self.config_file)
      sys.exit(1)

    self.config = yaml.load(open(self.config_file).read())
    self.config_mtime = os.stat(self.config_file).st_mtime
    self.ex_config_mtime = None

    for required in ["target_temperature", "fan_speed_temperature_ratio", "xorg_display_no"]:
      if not required in self.config.keys():
        print "required config key missing: %s" % (required)
        sys.exit(1)

  def reload(self):
    self.load()

  def reload_if_changed(self):
    if os.stat(self.config_file).st_mtime != self.config_mtime:
      print "info: config file change detected, reloading"
      self.reload()
      return True

    return False

  def get(self, key, data=None):
    if data == None:
      data = self.config

    if "." in key:
      segment = key.split('.')[0]

      if segment in data.keys():
        return self.get(key[len(segment)+1:], data[segment])

    if key not in data.keys():
      return None

    return data[key]

  def keys(self):
    return self.config.keys()
