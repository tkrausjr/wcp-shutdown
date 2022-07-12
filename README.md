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

STEP 0 - Logging into vCenter API with supplied credentials
/home/nverma/workspace/wcp-shutdown/wcp-shutdown.py:32: DeprecationWarning: ssl.PROTOCOL_TLSv1_2 is deprecated
  context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
--Successfully logged in to VIM API
-Found a total of 11 VMS on VC.

STEP 1 - Getting all Workload Cluster VMs from K8s API Server on Supervisor Cluster
-WCP Endpoint for SC is  192.168.104.11

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
-Found VM matching CAPI Machine Name in VC API. VM=workload-vsphere-tkg5-control-plane-gq26b.
-Found CAPI Machine Object in SC. VM Name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-85b58
-ERROR-Could not find specified VM with VC API
-Found CAPI Machine Object in SC. VM Name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-9b8l2
-ERROR-Could not find specified VM with VC API
-Found CAPI Machine Object in SC. VM Name = workload-vsphere-tkg5-default-nodepool-kph4q-64877fc9f4-ttn7s
-ERROR-Could not find specified VM with VC API

STEP 2 - Stopping WCP Service on vCenter
-Press Enter to confirm/continue...

STEP 3 - Shutting Down all Supervisor Control Plane VMs
-Found Supervisor Control Plane VM SupervisorControlPlaneVM (3).
-VM SupervisorControlPlaneVM (3)  is running on ESX host pacific-esxi-52.env1.lab.test
-ESX host pacific-esxi-52.env1.lab.test  has Management IP 192.168.100.52

--Shutting down VM SupervisorControlPlaneVM (3) on host 192.168.100.52
/home/nverma/workspace/wcp-shutdown/wcp-shutdown.py:32: DeprecationWarning: ssl.PROTOCOL_TLSv1_2 is deprecated
  context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
--Successfully logged in to VIM API
--Found SC Virtual Machine on ESX
--name                   : SupervisorControlPlaneVM (3)
--instance UUID          : 500a4998-1cd2-8278-1743-4e103279c45f
--bios UUID              : 420a82f3-6bbd-8472-4376-143930145b56
--path to VM             : [vsanDatastore] a96b8562-d468-54a8-191d-00505686dede/SupervisorControlPlaneVM (3).vmx
--host name              : pacific-esxi-52.env1.lab.test
--last booted timestamp  : 2022-07-11 23:58:56+00:00
-Shutting dow VM SupervisorControlPlaneVM (3)
-Pausing for 75 seconds...
-Found Supervisor Control Plane VM SupervisorControlPlaneVM (2).
-VM SupervisorControlPlaneVM (2)  is running on ESX host pacific-esxi-51.env1.lab.test
-ESX host pacific-esxi-51.env1.lab.test  has Management IP 192.168.100.51

--Shutting down VM SupervisorControlPlaneVM (2) on host 192.168.100.51
--Successfully logged in to VIM API
--Found SC Virtual Machine on ESX
--name                   : SupervisorControlPlaneVM (2)
--instance UUID          : 500a1e2c-ed13-b5bd-9cdb-6b00b80ac551
--bios UUID              : 420a4f0e-2eb7-28a2-0ca8-f13c790a926d
--path to VM             : [vsanDatastore] a96b8562-ac9f-3fda-5020-0050568663db/SupervisorControlPlaneVM (2).vmx
--host name              : pacific-esxi-51.env1.lab.test
--last booted timestamp  : 2022-07-12 00:00:08+00:00
-Shutting dow VM SupervisorControlPlaneVM (2)
-Pausing for 75 seconds...
-Found Supervisor Control Plane VM SupervisorControlPlaneVM (1).
-VM SupervisorControlPlaneVM (1)  is running on ESX host pacific-esxi-53.env1.lab.test
-ESX host pacific-esxi-53.env1.lab.test  has Management IP 192.168.100.53

--Shutting down VM SupervisorControlPlaneVM (1) on host 192.168.100.53
--Successfully logged in to VIM API
--Found SC Virtual Machine on ESX
--name                   : SupervisorControlPlaneVM (1)
--instance UUID          : 500accbe-e45a-2a17-8d7c-54ce22e77d82
--bios UUID              : 420aafd3-ba73-2454-cbba-1eefd435c892
--path to VM             : [vsanDatastore] a96b8562-b6ac-d6f7-bf21-005056863b0f/SupervisorControlPlaneVM (1).vmx
--host name              : pacific-esxi-53.env1.lab.test
--last booted timestamp  : 2022-07-11 23:50:54+00:00
-Shutting dow VM SupervisorControlPlaneVM (1)
-Pausing for 75 seconds...
-Press Enter to confirm/continue...or Control-C or Control-X to stop program

STEP 4 - Shutting down all Guest Cluster VMs
-The following Workload Cluster VMs will be shutdown
	 workload-vsphere-tkg5-control-plane-gq26b
-Press Enter to confirm/continue...
--Shutting dow VM workload-vsphere-tkg5-control-plane-gq26b.
--Pausing for 45 seconds...

POST STEPS - Successfully Completed Script - Cleaning up REST Session to VC.

```

## Starting up your vSphere with Tanzu environment
After your planned maintenance is completed in order to start vSphere with Tanzu you simply need to start the 'wcp' service on vCenter using either govc or the appliance User Interface 'https://<VC-IP>:5480/#/ui/services'


