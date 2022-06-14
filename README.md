# WCP-shutdown
WCP-Shutdown is simple Python script that you point to a vCenter and it is able to gracefully shutdown your TKGs environment.

##  Coverage

  - [x] Find and Return 3 Supervisor Control Plane VMs from pyVmomi vSphere API.
  - [x] Find all TKG Workload Cluster Machine objects from K8s API on Supervisor Cluster.
  - [x] Shutdown WCP Service on vCenter and set Startup Type to Manual.
  - [ ] Shutdown Supervisor Control Plane VMs - VC API or GOVC
  - [x] Shutdown all Worker & Control Plane Nodes in TKG Clusters - VC API or GOVC
  - [ ] Cordon all Workload Cluster Worker Nodes - K8s API on GC
  - [ ] Validate all Guest Clusters are powere down on Supervisor Cluster - K8s API
  - [ ] Stop CAPI CAPW Controllers
  - [ ] 
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

### vCenter Permissions
You must run the script with a User that is a member of the "ServiceProviderUsers" Group in vCenter.

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



