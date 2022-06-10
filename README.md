# WCP-shutdown
WCP-Shutdown is simple Python script that you point to a vCenter and it is able to gracefully shutdown your TKGs environment.

##  Coverage
  - [x] Return Supervisor Cluster Object - VC API
  - [x] Login to Supervisor Cluster  and enumerate all Workload Cluster Machine objects - K8s API on SC
  - [ ] Cordon all Workload Cluster Worker Nodes - K8s API on GC
  - [x] Power Down all Worker Nodes in Worker Cluster - VC API or GOVC
  - [ ] Power Down the Control Plane for each Guest Cluster -VC API or GOVC
  - [ ] Validate all Guest Clusters are powere down on Supervisor Cluster - K8s API
  ---

## Setting up the Big Red Button
You have two options for running the environment shutdown. 

On Ubuntu 18.04 with Python3 already installed.
```
pip3 install --force pyvmomi
pip3 install --force pyvim
pip3 install kubernetes
git clone https://github.com/tkrausjr/wcp-shutdown.git
```

## Running the Big Red Button
You have two options for running the environment shutdown. 

### Option 1 - Run script locally on Linux machine with access to VCenter

To run the shutdown script
``` bash

wcp-shutdown.py -s 192.168.100.50 -u administrator@vsphere.local -p VMware1!                                                                                                           ─╯
  WCP Endpoint for SC is  192.168.104.11

  Logged in successfully.

  You have access to the following contexts:
     192.168.104.11
     demo1
     workload-vsphere-tkg5

  If the context you wish to use is not in this list, you may need to try
  logging in again later, or contact your cluster administrator.

  To change context, use `kubectl config use-context <workload name>`


   Found  4  kubernetes Workload Cluster VMs

   Found Machine - workload-vsphere-tkg5-control-plane-gq26b
   -Machine Namespace - demo1
   -Machine Cluster - workload-vsphere-tkg5
   -Found VM in VC API
   -VM name = workload-vsphere-tkg5-control-plane-gq26b
   -VM guest OS ID = vmwarePhoton64Guest
   -VM guest Name = VMware Photon OS (64-bit)
   --Shutting down Guest OS through VMware Tools  workload-vsphere-tkg5-control-plane-gq26b

   Found Machine - workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-dgkzw
   -Machine Namespace - demo1
   -Machine Cluster - workload-vsphere-tkg5
   -Found VM in VC API
   -VM name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-dgkzw
   -VM guest OS ID = vmwarePhoton64Guest
   -VM guest Name = VMware Photon OS (64-bit)
   --Shutting down Guest OS through VMware Tools  workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-dgkzw
  Caught error trying to shutdown VM

   Found Machine - workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-tt9rk
   -Machine Namespace - demo1
   -Machine Cluster - workload-vsphere-tkg5
   -Found VM in VC API
   -VM name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-tt9rk
   -VM guest OS ID = vmwarePhoton64Guest
   -VM guest Name = VMware Photon OS (64-bit)
   --Shutting down Guest OS through VMware Tools  workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-tt9rk
  Caught error trying to shutdown VM

   Found Machine - workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-wgw95
   -Machine Namespace - demo1
   -Machine Cluster - workload-vsphere-tkg5
   -Found VM in VC API
   -VM name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-wgw95
   -VM guest OS ID = vmwarePhoton64Guest
   -VM guest Name = VMware Photon OS (64-bit)
   --Shutting down Guest OS through VMware Tools  workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-wgw95
  Caught error trying to shutdown V


```

### Option 2(COMING SOON) - Run from a Docker Container on a host with Docker and access to VM Management Network

On any nix machine with Docker already installed.
```
docker run -it --rm -v $HOME:/root -w /usr/src/app mytkrausjr/py3-wcp-precheck:v7 python wcp_tests.py -n vsphere
```
**NOTE:** On systems with SELinux enabled you need to pass an extra mount option "z" to the end of the volume definition in docker run. Without this option you will get a permission error when you run the container.


