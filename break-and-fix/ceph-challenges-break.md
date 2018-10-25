# Ceph challenges (breaking)

## Rados gateway container not started

The file **/etc/systemd/system/ceph-radosgw@.service** will be modified in **ceph1** server:

```
[Unit]
Description=Ceph RGW
After=docker.service

[Service]
EnvironmentFile=-/etc/environment
ExecStartPre=-/usr/bin/docker stop ceph-rgw-ceph1
ExecStartPre=-/usr/bin/docker rm ceph-rgw-ceph1
ExecStart=/usr/bin/docker run --rm --net=host \
  --memoyr=1g \
  --cpu-quota=100000 \
  -v /var/lib/ceph:/var/lib/ceph:z \
  -v /etc/ceph:/etc/ceph:z \
  -v /var/run/ceph:/var/run/ceph:z \
  -v /etc/localtime:/etc/localtime:ro \
  -e CEPH_DAEMON=RGW \
  -e CLUSTER=ceph \
  --name=ceph-rgw-ceph1 \
   \
  registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest
ExecStopPost=-/usr/bin/docker stop ceph-rgw-ceph1
Restart=always
RestartSec=10s
TimeoutStartSec=120
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
```

The radosgw daemon will be restarted:

```
[root@ceph1 ~]# systemctl daemon-reload
[root@ceph1 ~]# systemctl restart ceph-radosgw@ceph1
[root@ceph1 ~]# docker ps
CONTAINER ID        IMAGE                                                     COMMAND             CREATED             STATUS              PORTS               NAMES
86450464c505        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-osd-ceph1-vdb
21d75b541bbf        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-osd-ceph1-vdc
8e33594fd399        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-mgr-ceph1
40aea608cfed        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-mon-ceph1
[root@ceph1 ~]#
```

This part is automated in the [ansible role break-rados](ansible/roles/break-rados).

## Corrupting data 

We are going to corrupt one of the three copies of data.

The pool where data is stored is **default.rgw.buckets.data**:

```
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph osd lspools
1 .rgw.root,2 default.rgw.control,3 default.rgw.meta,4 default.rgw.log,6 default.rgw.buckets.index,7 default.rgw.buckets.data,
[root@ceph1 ~]# 
```

In the first server we will locate the copy of a file:

```
[root@ceph1 ~]# docker exec ceph-osd-ceph1-vdb find /var/lib/ceph/osd/ | grep txt
/var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7
/var/lib/ceph/osd/ceph-0/current/7.6_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uocp.txt.gz__head_F8C08A0E__7
/var/lib/ceph/osd/ceph-0/current/7.5_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uceph.txt.gz__head_7B50CC95__7
/var/lib/ceph/osd/ceph-0/current/7.5_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\urhv.txt.gz__head_F6C44A05__7
[root@ceph1 ~]# 
```

We will add some extra data to this copy:

```
[root@ceph1 ~]# echo "corrupting a file" > corruption
[root@ceph1 ~]# docker exec ceph-osd-ceph1-vdb md5sum "/var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7"
\a276f1b4acc656e400c798e5213cde39  /var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\\uosp.txt.gz__head_B9A97AB1__7
[root@ceph1 ~]# docker exec ceph-osd-ceph1-vdb tee "/var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7" < corruption 
^C
[root@ceph1 ~]# docker exec ceph-osd-ceph1-vdb md5sum "/var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7"
\d41d8cd98f00b204e9800998ecf8427e  /var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\\uosp.txt.gz__head_B9A97AB1__7
[root@ceph1 ~]#
```

We will launch scrubbing on the pg to detect the corruption:

```
[root@ceph1 ~]# ceph pg scrub 7.1
instructing pg 7.1 on osd.0 to scrub
[root@ceph1 ~]# 
```

After a while:

```
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph -s
  cluster:
    id:     b77a2eb0-826e-450c-8e6e-ce891dd9478e
    health: HEALTH_ERR
            2 scrub errors
            Possible data damage: 1 pg inconsistent
 
  services:
    mon: 3 daemons, quorum ceph1,ceph2,ceph3
    mgr: ceph3(active), standbys: ceph2, ceph1
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active
 
  data:
    pools:   6 pools, 272 pgs
    objects: 197 objects, 546 kB
    usage:   698 MB used, 91394 MB / 92093 MB avail
    pgs:     271 active+clean
             1   active+clean+inconsistent
 
[root@ceph1 ~]# 
``` 

This part is automated in the [ansible role break-rados](ansible/roles/break-rados). To corrupt data [one script](data-corruption) is used. This script is placed in **/root/data-corruption** in **ceph1** server.
