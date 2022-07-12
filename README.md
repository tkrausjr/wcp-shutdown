# WCP-shutdown
WCP-Shutdown is simple Python script that you point to a vCenter and it is able to gracefully shutdown your TKGs or vSphere with Tanzu environment.  The use case for the script is in anticipation for planned maintenance to your vSphere environment such as a planned datacenter outage.

##  Coverage
  - [x] Find and Return 3 Supervisor Control Plane VMs from pyVmomi vSphere API.
  - [x] Find all TKG Workload Cluster Machine objects from K8s API on Supervisor Cluster.
  - [x] Shutdown WCP Service on vCenter and set Startup Type to Manual.
  - [x] Shutdown Supervisor Control Plane VMs - VC API or GOVC
  - [x] Shutdown all Worker & Control Plane Nodes in TKG Clusters - VC API or GOVC
  - [ ] Cordon all Workload Cluster Worker Nodes - K8s API on GC
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

### vCenter Permissions
You must run the script with a User that has permissions to shutdown Virtual Machines (Guest Operations).

## Running the Big Red Button - Option 1 - Run script locally on Linux machine with access to VCenter

To run the shutdown script
``` bash

python3 wcp-shutdown.py -s 192.168.100.50 -u administrator@vsphere.local -p <yourpassword>                                                               

Logging into vCenter API with supplied credentials

STEP 0 - Getting all VMs from VC API
-Successfully logged into vCenter
-Found 14 VMS on VC.

STEP 1 - Getting all Supervisor Control Plane VMs from VC API
-Found Supervisor Control Plane VM SupervisorControlPlaneVM (3).
-Found Supervisor Control Plane VM SupervisorControlPlaneVM (1).
-Found Supervisor Control Plane VM SupervisorControlPlaneVM (2).

STEP 2 - Getting all Workload Cluster VMs from K8s API Server on Supervisor Cluster
-WCP Endpoint for SC is  192.168.104.11

KUBECTL_VSPHERE_PASSWORD environment variable is not set. Please enter the password below
Password:
Logged in successfully.

You have access to the following contexts:
   192.168.104.11
   demo1
   workload-vsphere-tkg5

If the context you wish to use is not in this list, you may need to try
logging in again later, or contact your cluster administrator.

To change context, use `kubectl config use-context <workload name>`
-Found  4  kubernetes Workload Cluster VMs
-Found CAPI Machine Object in SC. VM Name = workload-vsphere-tkg5-control-plane-gq26b
-Found VM matching CAPI Machine Name in VC API. VM=SupervisorControlPlaneVM (2).
-Found CAPI Machine Object in SC. VM Name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-fdxxs
-Found VM matching CAPI Machine Name in VC API. VM=SupervisorControlPlaneVM (2).
-Found CAPI Machine Object in SC. VM Name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-lffd5
-Found VM matching CAPI Machine Name in VC API. VM=SupervisorControlPlaneVM (2).
-Found CAPI Machine Object in SC. VM Name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-zw878
-Found VM matching CAPI Machine Name in VC API. VM=SupervisorControlPlaneVM (2).

STEP 3 - Stopping WCP Service on vCenter
-Press Enter to confirm/continue...
-Successfully set WCP Service Startup to MANUAL. Response Code 204
-Successfully stopped WCP Service. Response Code 204

STEP 4 - Shutting down all Supervisor Cluster VMs
-The following SC Cluster VMs will be shutdown
	 SupervisorControlPlaneVM (3)
	 SupervisorControlPlaneVM (1)
	 SupervisorControlPlaneVM (2)
-Press Enter to confirm/continue...
-Shutting dow VM SupervisorControlPlaneVM (3).
-ERROR-Caught error trying to shutdown VM
-ERROR-Caught vmodl fault : Permission to perform this operation was denied.

STEP 5 - Shutting down all Guest Cluster VMs
-The following Workload Cluster VMs will be shutdown
	 workload-vsphere-tkg5-control-plane-gq26b
	 workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-fdxxs
	 workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-lffd5
	 workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-zw878
-Press Enter to confirm/continue...
-Shutting dow VM workload-vsphere-tkg5-control-plane-gq26b.
-Pausing for 10 seconds...
-Shutting dow VM workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-fdxxs.
-Pausing for 10 seconds...
-Shutting dow VM workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-lffd5.
-Pausing for 10 seconds...
-Shutting dow VM workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-zw878.
-Pausing for 10 seconds...

POST - Successfully Completed Script - Cleaning up REST Session to VC.

```

## Starting up your vSphere with Tanzu environment
After your planned maintenance is completed in order to start vSphere with Tanzu you simply need to start the 'wcp' service on vCenter using either govc or the appliance User Interface 'https://<VC-IP>:5480/#/ui/services'


