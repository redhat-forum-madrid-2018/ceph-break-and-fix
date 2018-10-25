# Ceph challenges

## Rados gateway container not started (fixing)

The file **/etc/systemd/system/ceph-radosgw@.service** will be fixed in **ceph1** server:

```
[Unit]
Description=Ceph RGW
After=docker.service

[Service]
EnvironmentFile=-/etc/environment
ExecStartPre=-/usr/bin/docker stop ceph-rgw-ceph1
ExecStartPre=-/usr/bin/docker rm ceph-rgw-ceph1
ExecStart=/usr/bin/docker run --rm --net=host \
  --memory=1g \
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

The radosgw daemon will be stopped and systemctl will be forced to reload daemon's configuration:

```
[root@ceph1 ~]# systemctl daemon-reload
[root@ceph1 ~]# systemctl stop ceph-radosgw@ceph1
[root@ceph1 ~]#
```

After a while as service was started with **Restart=always** will be restarted using the new unit file:

```
[root@ceph1 ~]# docker ps
CONTAINER ID        IMAGE                                                     COMMAND             CREATED             STATUS              PORTS               NAMES
86450464c505        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-osd-ceph1-vdb
21d75b541bbf        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-osd-ceph1-vdc
8e33594fd399        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-mgr-ceph1
40aea608cfed        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    About an hour ago   Up About an hour                        ceph-mon-ceph1
1f1da1249ea1        registry.access.redhat.com/rhceph/rhceph-3-rhel7:latest   "/entrypoint.sh"    4 minutes ago       Up 4 minutes                            ceph-rgw-ceph1
[root@ceph1 ~]# 
```

## Corrupting data

Cluster is in error state:

```
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph -s
  cluster:
    id:     b77a2eb0-826e-450c-8e6e-ce891dd9478e
    health: HEALTH_ERR
            8 scrub errors
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

But the application is working. Only on copy of the data is in bad shape.

It seems that there is one inconsistent pg, so we have to search for the inconsistent pg:

```
[root@ceph1 ~]# ceph health detail
HEALTH_ERR 2 scrub errors; Possible data damage: 1 pg inconsistent
OSD_SCRUB_ERRORS 2 scrub errors
PG_DAMAGED Possible data damage: 1 pg inconsistent
    pg 7.1 is active+clean+inconsistent, acting [0,2,4]
[root@ceph1 ~]# rados list-inconsistent-pg default.rgw.buckets.data
["7.1"]
[root@ceph1 ~]#
```

So the inconsistent pg is **7.1**, we can get more info, if needed:

```
[root@ceph1 ~]# ceph pg 7.1 query 
{
    "state": "active+clean+inconsistent",
    "snap_trimq": "[]",
    "snap_trimq_len": 0,
    "epoch": 164,
    "up": [
        0,
        2,
        4
    ],
    "acting": [
        0,
        2,
        4
    ],
    "actingbackfill": [
        "0",
        "2",
        "4"
    ],
...
```

So the pg **7.1** is placed in osds **0**, **2** and **4**. So we need to know in which server is each osd and know what device is the osd as well:

```
[root@ceph1 ~]# ceph osd find 0
{
    "osd": 0,
    "ip": "192.168.1.121:6803/7310",
    "crush_location": {
        "host": "ceph1",
        "root": "default"
    }
}
[root@ceph1 ~]# ceph osd metadata 0
{
    "id": 0,
    "arch": "x86_64",
    "back_addr": "192.168.200.121:6802/7310",
    "back_iface": "eth1",
    "backend_filestore_dev_node": "vdb",
    "backend_filestore_partition_path": "/dev/vdb1",
    "ceph_version": "ceph version 12.2.5-42.el7cp (82d52d7efa6edec70f6a0fc306f40b89265535fb) luminous (stable)",
    "cpu": "Intel Core Processor (Skylake, IBRS)",
    "default_device_class": "hdd",
    "distro": "rhel",
    "distro_description": "Red Hat Enterprise Linux Server 7.5 (Maipo)",
    "distro_version": "7.5",
    "filestore_backend": "xfs",
    "filestore_f_type": "0x58465342",
    "front_addr": "192.168.1.121:6803/7310",
    "front_iface": "eth0",
    "hb_back_addr": "192.168.200.121:6803/7310",
    "hb_front_addr": "192.168.1.121:6804/7310",
    "hostname": "ceph1.redhatforummad.com",
    "journal_rotational": "1",
    "kernel_description": "#1 SMP Fri Sep 21 09:07:21 UTC 2018",
    "kernel_version": "3.10.0-862.14.4.el7.x86_64",
    "mem_swap_kb": "1572860",
    "mem_total_kb": "2914748",
    "os": "Linux",
    "osd_data": "/var/lib/ceph/osd/ceph-0",
    "osd_journal": "/var/lib/ceph/osd/ceph-0/journal",
    "osd_objectstore": "filestore",
    "rotational": "1"
}
[root@ceph1 ~]# 
```

> **IMPORTANT**
>
> You can repair only certain inconsistencies. Do not repair the placement groups if the Ceph logs include the following errors: 
> ```
> <pg.id> shard <osd>: soid <object> digest <digest> != known digest <digest>
> <pg.id> shard <osd>: soid <object> omap_digest <digest> != known omap_digest <digest>
> ```
>
> For more information check [this](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/3/html/troubleshooting_guide/troubleshooting-placement-groups#repairing-inconsistent-pgs)

Check osd logs:

```
[root@ceph1 ~]# journalctl -l -u ceph-osd@vdb | grep digest
oct 25 18:29:18 ceph1.redhatforummad.com ceph-osd-run.sh[1643]: 2018-10-25 18:29:18.653762 7f2d07a88700 -1 log_channel(cluster) log [ERR] : 7.1 shard 0: soid 7:8d5e959d:::15bae509-9897-4a93-856f-77966838aac6.174106.2_osp.txt.gz:head data_digest 0xffffffff != data_digest 0xe6eb6eb0 from shard 2, data_digest 0xffffffff != data_digest 0xe6eb6eb0 from auth oi 7:8d5e959d:::15bae509-9897-4a93-856f-77966838aac6.174106.2_osp.txt.gz:head(164'3 client.604110.0:6539 dirty|data_digest|omap_digest s 53239 uv 3 dd e6eb6eb0 od ffffffff alloc_hint [0 0 0]), size 0 != size 53239 from auth oi 7:8d5e959d:::15bae509-9897-4a93-856f-77966838aac6.174106.2_osp.txt.gz:head(164'3 client.604110.0:6539 dirty|data_digest|omap_digest s 53239 uv 3 dd e6eb6eb0 od ffffffff alloc_hint [0 0 0]), size 0 != size 53239 from shard 2
[root@ceph1 ~]# journalctl -l -u ceph-osd@vdb | grep digest | grep known
[root@ceph1 ~]# 
```

To repair it:

```
[root@ceph1 ~]# ceph pg repair 7.1
instructing pg 7.1 on osd.0 to repair
[root@ceph1 ~]# 
```

Two possible scenarios here:

* **HEALTH_OK**, you finished!!! Congratulations!!!

```
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph -s
  cluster:
    id:     b77a2eb0-826e-450c-8e6e-ce891dd9478e
    health: HEALTH_OK
 
  services:
    mon: 3 daemons, quorum ceph1,ceph2,ceph3
    mgr: ceph3(active), standbys: ceph2, ceph1
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active
 
  data:
    pools:   6 pools, 272 pgs
    objects: 197 objects, 546 kB
    usage:   699 MB used, 91394 MB / 92093 MB avail
    pgs:     272 active+clean
 
[root@ceph1 ~]# docker exec ceph-osd-ceph1-vdb find /var/lib/ceph/osd/ | grep txt
/var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7
/var/lib/ceph/osd/ceph-0/current/7.6_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uocp.txt.gz__head_F8C08A0E__7
/var/lib/ceph/osd/ceph-0/current/7.5_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uceph.txt.gz__head_7B50CC95__7
/var/lib/ceph/osd/ceph-0/current/7.5_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\urhv.txt.gz__head_F6C44A05__7
[root@ceph1 ~]# docker exec ceph-osd-ceph1-vdb md5sum "/var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7"
\a276f1b4acc656e400c798e5213cde39  /var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\\uosp.txt.gz__head_B9A97AB1__7
[root@ceph1 ~]# 
```

* **HEALTH_ERR** go on investigating.

In this case we will check object's md5 and compare it with the other two copies:

```
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph -s
  cluster:
    id:     b77a2eb0-826e-450c-8e6e-ce891dd9478e
    health: HEALTH_ERR
            5 scrub errors
            Possible data damage: 1 pg inconsistent
 
  services:
    mon: 3 daemons, quorum ceph1,ceph2,ceph3
    mgr: ceph1(active), standbys: ceph3, ceph2
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active
 
  data:
    pools:   6 pools, 272 pgs
    objects: 198 objects, 546 kB
    usage:   706 MB used, 91386 MB / 92093 MB avail
    pgs:     271 active+clean
             1   active+clean+inconsistent
 
[root@ceph1 ~]# docker exec ceph-osd-ceph1-vdb md5sum "/var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7"
\a276f1b4acc656e400c798e5213cde39  /var/lib/ceph/osd/ceph-0/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\\uosp.txt.gz__head_B9A97AB1__7
[root@ceph1 ~]# 
```

We have to locate where the pg is placed, which osds:

```
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph pg map 7.1
osdmap e222 pg 7.1 (7.1) -> up [0,2,4] acting [0,2,4]
[root@ceph1 ~]# 
```

So the other osds are **osd 2** and **osd 4**:

```
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph osd find 2
{
    "osd": 2,
    "ip": "192.168.1.123:6803/3044",
    "crush_location": {
        "host": "ceph3",
        "root": "default"
    }
}
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph osd find 4
{
    "osd": 4,
    "ip": "192.168.1.122:6800/2802",
    "crush_location": {
        "host": "ceph2",
        "root": "default"
    }
}
[root@ceph1 ~]#
```

```
[root@ceph2 ~]# docker exec ceph-osd-ceph2-vdc ls -lh /var/lib/ceph/osd/ceph-4/current/7.1_head/
total 52K
-rw-r--r--. 1 ceph disk 52K Oct 25 15:04 15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7
-rw-r--r--. 1 ceph disk   0 Oct 24 12:29 __head_00000001__7
[root@ceph2 ~]# docker exec ceph-osd-ceph2-vdc md5sum "/var/lib/ceph/osd/ceph-4/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7"
\a276f1b4acc656e400c798e5213cde39  /var/lib/ceph/osd/ceph-4/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\\uosp.txt.gz__head_B9A97AB1__7
[root@ceph2 ~]# 
```

```
[root@ceph3 ~]# docker exec ceph-osd-ceph3-vdb ls -lh /var/lib/ceph/osd/ceph-2/current/7.1_head/
total 52K
-rw-r--r--. 1 ceph disk 52K Oct 25 15:04 15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7
-rw-r--r--. 1 ceph disk   0 Oct 24 12:29 __head_00000001__7
[root@ceph3 ~]# docker exec ceph-osd-ceph3-vdb md5sum "/var/lib/ceph/osd/ceph-2/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\uosp.txt.gz__head_B9A97AB1__7"
\a276f1b4acc656e400c798e5213cde39  /var/lib/ceph/osd/ceph-2/current/7.1_head/15bae509-9897-4a93-856f-77966838aac6.174106.2\\uosp.txt.gz__head_B9A97AB1__7
[root@ceph3 ~]# 
```

So the md5's are the same, it seems that the object is ok.

So we can restart the osd container to solve it:

```
[root@ceph1 ~]# systemctl restart ceph-osd@vdb
[root@ceph1 ~]# docker exec ceph-mon-ceph1 ceph -s
  cluster:
    id:     b77a2eb0-826e-450c-8e6e-ce891dd9478e
    health: HEALTH_OK
 
  services:
    mon: 3 daemons, quorum ceph1,ceph2,ceph3
    mgr: ceph1(active), standbys: ceph3, ceph2
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active
 
  data:
    pools:   6 pools, 272 pgs
    objects: 197 objects, 546 kB
    usage:   708 MB used, 91385 MB / 92093 MB avail
    pgs:     272 active+clean
 
[root@ceph1 ~]#
```

> **IMPORTANT**
>
> This is a lab so no much IO on the OSD. In production restating an OSD could impact clients.
>
> If you are uncertain when repairing a pg do not hesitate to open a case!!!!
