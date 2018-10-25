# Installation

## The environment

```
                                .-~~~-.
                        .- ~ ~-(       )_ _
                       /                     ~ -.
                      |      OUTSIDE WORLD        \
                      \                         .'
                        ~- . _____________ . -~
                                  |
                                  |
                                  |
  ()=========================================================() (192.168.1.0/24) Public Network
    |                 |                 |                   |
+-------+         +-------+         +-------+         +-----------+
|       |         |       |         |       |         |           |
| ceph1 |         | ceph2 |         | ceph3 |         | cephinfra |
|       |         |       |         |       |         |           |
+-------+         +-------+         +-------+         +-----------+
    |                 |                 |                   |
  ()=========================================================() (192.168.200.0/24) Cluster Network
```

Server IPs:

Server | Public Network | Cluster Network
-------|----------------|----------------
ceph1 | 192.168.1.121 | 192.168.200.121 
ceph2 | 192.168.1.122 | 192.168.200.122 
ceph3 | 192.168.1.123 | 192.168.200.123 
cephinfra | 192.168.1.120 | 192.168.200.120

DNS and endpoint information:

FQDN  | IP | DNS Record | Role | Port
------|----|----------- |------|-----
ceph1.redhatforummad.com | 192.168.1.121 | A | ceph-mon & rados | 8080/tcp rados
ceph2.redhatforummad.com | 192.168.1.122 | A | ceph-mon | 
ceph3.redhatforummad.com | 192.168.1.123 | A | ceph-mon |
cephinfra.redhatforummad.com | 192.168.1.120 | A | not defined |
rhproducts.redhatforummad.com | cephinfra | CNAME | web application | 3838/tcp
cephmetrics.redhatforummad.com | cephinfra | CNAME | cephmetrics | 8080/tcp
