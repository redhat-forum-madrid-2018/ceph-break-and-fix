# -*- coding: utf-8 -*-
#!/usr/bin/python

# (c) 2018 Jose Angel de Bustos Perez <jadebustos@redhat.com>
# Distributed under GPLv3 License (https://www.gnu.org/licenses/gpl-3.0.en.html)

import boto
import boto.s3.connection

# this script list a bucket content's

def main():
  # put here your access_key and secret_key to access s3 bucket
  access_key = '9D0Y7J44G5Q9B8H491GA'
  secret_key = 'lm1g1LrLKUDjKojBQjNfg9iyAU5P68muP0QF70lX'

  # your rados host
  radoshost = 'ceph1.redhatforummad.com'

  # your rados port
  radosport = 8080

  boto.config.add_section('s3')

  conn = boto.connect_s3(
    aws_access_key_id = access_key,
    aws_secret_access_key = secret_key,
    host = radoshost,
    port = radosport,
    is_secure=False,
    calling_format = boto.s3.connection.OrdinaryCallingFormat(),
    )

  bucket = conn.get_bucket('redhatforum')

  for key in bucket.list():
    print "{name}\t{size}\t{modified}".format(
      name = key.name,
      size = key.size,
      modified = key.last_modified,
      )

if __name__ == "__main__":
  main()
