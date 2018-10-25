# -*- coding: utf-8 -*-
#!/usr/bin/python

# (c) 2018 Jose Angel de Bustos Perez <jadebustos@redhat.com>
# Distributed under GPLv3 License (https://www.gnu.org/licenses/gpl-3.0.en.html)

# script to corrupt data in a ceph cluster
# this script is been developed to fit a specific cluster so could not work on yours

import sys

from execs import *

def main():
  # looking for data
  try:
    cmd = 'docker exec ceph-osd-ceph1-vdb find /var/lib/ceph/osd/ | grep txt'
    myExec1 = Command(cmd)
  except:
    sys.exit(1)

  #  we will corrupt the first file
  file = myExec1.getStdout().split('\n')[0]

  pt = open("/tmp/corruption", 'w')
  pt.write('corrupting a file')
  pt.close()

  # corrupting data
  try:
    cmd = 'docker exec ceph-osd-ceph1-vdb sed -i "\$aCorruption" "' + file + '"'
    print "corrupting data"
    myExec2 = Command(cmd)
  except:
    pass

  # pg number
  pg = file.split('/')[7].split('_')[0]

  # launching scrubbing to detect data corruption
  try:
    cmd = "docker exec ceph-mon-ceph1 ceph pg scrub " + pg
    print "launching scrub on pg " + pg
    myExec2 = Command(cmd)
  except:
    pass

if __name__ == "__main__":
  main()
