# glance-sync
Utility to sync images between OpenStack Glance endpoints

This utility uses the Python OpenStack SDK from https://docs.openstack.org/openstacksdk/latest/.

The following steps will get this up and running on RHEL 7:

First, create a cloud config file at ~/.config/openstack/clouds.yaml similar to this one:

```
clouds:
  rdu:
    region_name: regionOne
    identity_api_version: 2
    auth:
      username: 'admin'
      password: 'secret'
      project_name: 'admin'
      auth_url: 'http://10.11.95.20:5000/v2.0'
  phx:
    region_name: RegionOne
    identity_api_version: 2
    auth:
      username: 'openstackadmin'
      password: 'secret'
      project_name: 'admin'
      auth_url: 'http://10.3.71.47:5000/v2.0'
```

Then, create a virtualenv for openstacksdk and activate it:

```
subscription-manager repos --enable rhel-7-server-rpms --enable rhel-server-rhscl-7-rpms
yum update -y
yum install python-virtualenv python27-python-pip -y
scl enable python27 bash
virtualenv openstacksdk
. ./openstacksdk/bin/activate
pip install openstacksdk
```

Run the script, giving the source and destination clouds defined in clouds.yaml:

```
python sync.py --src=phx --dest=rdu
```

