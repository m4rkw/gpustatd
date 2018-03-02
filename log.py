
import os
import datetime
import sys
from singleton import Singleton
from config import Config

class Log:
  __metaclass__ = Singleton

  def __init__(self):
    if "log_file" in Config().keys():
      self.log_file = Config().get('log_file')
    else:
      self.log_file = "/var/log/gpustatd/gpustatd.log"

    self.silent = False


  def silent(self):
    self.silent = True


  def add(self, level, message):
    if not os.path.exists(os.path.dirname(self.log_file)):
      os.mkdir(os.path.dirname(self.log_file))

    now = datetime.datetime.now()

    with open(self.log_file, "a+") as f:
      f.write("%s: [%s] %s\n" % (now.strftime("%Y-%m-%d %H:%M:%S"), level, message))

      if not self.silent:
        sys.stdout.write("%s: %s\n" % (level, message))
        sys.stdout.flush()

    if "logfile_max_size_mb" in Config().keys():
      max_size = Config().get('logfile_max_size_mb')
    else:
      max_size = 100

    if os.path.getsize(self.log_file) >= (max_size * 1024 * 1024):
      self.rotate_logs()

    if level == "fatal":
      sys.exit(1)


  def rotate_logs(self):
    logfile = self.log_file

    if "logfile_max_count" in Config().keys():
      max_count = Config().get('logfile_max_count')
    else:
      max_count = 10

    for i in reversed(range(1, max_count - 1)):
      os.rename(logfile + ".%d" % (i), logfile + ".%d" % (i+1))

    os.rename(logfile, logfile + ".1")
