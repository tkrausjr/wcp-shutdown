# WCP-precheck
WCP-Precheck project aims to make POC's and vSphere with Tanzu installations less painful for customers and overall more successful by quickly indentifying common misconfigurations and errors that would prevent a successful installation of WCP .  The pre-checks can be run by VMware Tanzu SE's or Customers to quickly validate a vSphere environment is ready for a successful vSphere with Tanzu Supervisor Cluster creation.  The project has options for testing both NSX-T based and vSphere based networking for vSphere with Tanzu and can be run as a standalone script or via Docker.

## Test Coverage
  ### General
  - [x] The Tag-based storage policy specified exists the vCenter.
  - [x] DNS forward and reverse resolution should work for vCenter and NSX Manager.
  - [x] Ping/curl various network end points that they are reachable (DNS, NTP, VCenter, NSX Manager, )
  - [x] Validate vSphere API is accessible and provided credentials are valid.
  - [x] Validate existence of vSphere cluster specified in configuration YAML is valid.
  - [x] Validate existence of VDS specified in configuration YAML is valid.
  - [x] Validate existence of Datacenter specified in configuration YAML is valid.
  - [x] Validate existence of Cluster specified in configuration YAML is valid.
  - [x] Validate that vLCM (Personality Manager) is not enabled on the specified cluster if vSphere <= 7.0 U1.
  - [x] Validate that HA is enabled on the specified cluster.
  - [x] Validate that DRS is enabled and set to Fully Automated Mode on the specified cluster.
  - [x] Validate that a compatible NSX-T VDS exists.
  - [x] Validate that at leaset one content library is created on the vCenter.
  - [x] NTP driff between vCenter and ESXi hosts in Cluster
  ---
  ### NSX based networking
  - [x] Validate required VDS Port Groups(Management, Edge TEP, Uplink) specified in configuration YAML is valid.
  - [x] DNS forward and reverse resolution should work for NSX Manager.
  - [x] Validate we can communicate with NSX Manager on network and NSX Management Node and Cluster is Healthy.
  - [x] Validate NSX-T API is accessible and provided credentials are valid.
  - [x] Validate Health of ESXi Transport Nodes(NSX-T Agent Install and Status) in vSphere Cluster.
  - [x] Validate Health of Edge Transport Nodes(Status) in vSphere Cluster.
  - [ ] Ingress and Egress network is routed
  - [ ] Heartbeat ping to the uplink IP (T0 interface) is working. 
  - [ ] 1600 byte ping with no fragmentation between ESXi TEPs
  - [ ] 1600 byte ping with no fragmentation between ESXi TEPs to Edge TEPs.   
  - [x] Validate EDGE VMs are deployed as at least large.
  - [x] NTP driff between EDGE, vCenter and ESXi
  - [ ] Depending on NSX version, EDGE vTEP and ESX vTEP are on different VLANs
  - [x] Validate existence of a T0 router.
  - [ ] T0 router can access DNS and NTP
  ---
  ### (COMING SOON) VDS based AVI Lite config
  - [ ] AVI Controller liveness probes that check each network connectivity and the frontend VIP IP's
  - [ ] AVI Service Engine Health.

  ---
  ### VDS based HAProxy config
  - [x] HA proxy liveness probes that check each network connectivity and the frontend VIP IP's
  - [ ] The HA Proxy Load-Balancer IP Range and WCP Workload Network Range must not include the Gateway address for the overall Workload Network.
  - [ ] The HA Proxy Workload IP should be in the overall Workload network, but outside of the Load-Balancer IP Range and the WCP Workload Network Range.
  - [ ] The IP ranges for the OVA and the WCP enablement should be checked to be the same
  - [ ] The WCP Range for Virtual Servers must be exactly the range defined by the Load-Balancer IP Range in HA Proxy.  
  - [x] Validate successful login access to HAProxy VM's API endpoint.


## Create & Populate the Parameters file used for input values 
Download the sample parameters file from this repo or copy and paste below to a parameters file named **test_params.yaml** in the $HOME folder on the system where you will run the validation script.
``` yaml
### COMMON SETTINGS
DOMAIN: 'tpmlab.vmware.com'
NTP_SERVER: 'time.vmware.com'
DNS_SERVERS:
  - '10.173.13.90'
VC_HOST: 'vcsa.tpmlab.vmware.com'    # VCSA FQDN or IP MUST ADD A Rec to DNS
VC_IP: '10.173.13.81'                      # VCSA IP
VC_SSO_USER: 'administrator@vsphere.local'
VC_SSO_PWD:  '***********'
VC_DATACENTER: 'Datacenter'
VC_CLUSTER:  'Nested-TKG-Cluster'
VC_STORAGEPOLICIES:          # Storage Policies to use 
  - 'thin'  
  - 'thinner'      

### Section for vSphere Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'
VDS_PRIMARY_WKLD_PG: 'not_there'
HAPROXY_IP: '192.168.100.163'
HAPROXY_PORT: 5556      # HAProxy Dataplane API Mgmt Port chosen during OVA Deployment
HAPROXY_IP_RANGE_START: '10.173.13.38' # HAProxy LB IP Range chosen during OVA Deployment
HAPROXY_IP_RANGE_SIZE: 29
HAPROXY_USER: 'admin'
HAPROXY_PW: '***********'

### Section for NSX-T Networking Deployments
VDS_NAME: 'vds-1'
VDS_MGMT_PG: 'management-vm'
VDS_UPLINK_PG: 'ext-uplink-edge'
VDS_EDGE_TEP_PG: 'tep-edge'
HOST_TEP_VLAN: 102
NSX_MGR_HOST: 'nsxmgr.tpmlab.vmware.com'   # FQDN of NSX-T Manager Appliance
NSX_MGR_IP: '10.173.13.82'    # IP Addr of NSX-T Manager Appliance
NSX_USER: 'admin'   # API Username for NSX-T Manager Appliance
NSX_PASSWORD: '***********'    # API Password for NSX-T Manager Appliance

### Section for WCP Supervisor Cluster Deployment
WCP_MGMT_STARTINGIP: '192.168.100.141'
WCP_MGMT_MASK: '255.255.255.0'
WCP_MGMT_GATEWAY: '192.168.100.1'


``` 

## Running the Pre-checks
You have two options for running the environment prechecks. Both options require you to create the **test_params.yaml** file in the $HOME directory of the linux machine where you will either run the script (locally or via Docker container). You should copy paste the sample **test_params.yaml** file from this repo into your $HOME directory as a starting point and update the values for the environment being tested.

### Option 1(Preferred) - Run from a Docker Container on a host with Docker and access to VM Management Network

On any nix machine with Docker already installed.
```
docker run -it --rm -v $HOME:/root -w /usr/src/app mytkrausjr/py3-wcp-precheck:v7 python wcp_tests.py -n vsphere
```
**NOTE:** On systems with SELinux enabled you need to pass an extra mount option "z" to the end of the volume definition in docker run. Without this option you will get a permission error when you run the container.
```
docker run -it --rm -v $HOME:/root:z -w /usr/src/app mytkrausjr/py3-wcp-precheck:v7 python wcp_tests.py -n vsphere
```

### Option 2 - Run script locally on Linux machine with access to VM Management Network

On Ubuntu 18.04 with Python3 already installed.
```
git clone https://gitlab.eng.vmware.com/TKGS-TSL/wcp-precheck.git              
Cloning into 'wcp-precheck'...
Username for 'https://gitlab.eng.vmware.com':   <VMware User ID IE njones>
Password for 'https://kraust@gitlab.eng.vmware.com':  <VMware Password>
cd wcp-precheck/pyvim
chmod +x ./wcp_tests.py 
cp ./test_params.yaml ~/test_params.yaml
vi ~/test_params.yaml    ### See Below of explanation
pip3 install pyVmomi
pip3 install pyaml
pip3 install requests
pip3 install pyVim
```


To run the validation script
``` bash

❯ cd github/wcp-precheck/pyvim
❯ ./wcp_tests.py -h                              
usage: wcp_tests.py [-h] [--version] [-n {nsxt,vsphere}] [-v [{INFO,DEBUG}]]

vcenter_checks.py validates environments for succcesful Supervisor Clusters
setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify
environment information to test. Find additional information at:
gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git

optional arguments:
  -h, --help            show this help message and exit
  --version             show programs version number and exit
  -n {nsxt,vsphere}, --networking {nsxt,vsphere}
                        Networking Environment(nsxt, vsphere)
  -v [{INFO,DEBUG}], --verbosity [{INFO,DEBUG}]

❯ wcp_tests.py -n nsxt 

docker run -it --rm -v $HOME:/root -w /usr/src/app mytkrausjr/py3-wcp-precheck:v7 python wcp_tests.py -n nsxt
INFO: 2021-03-26 16:39:57: __main__: 62: Looking in /root for test_params.yaml file
INFO: 2021-03-26 16:39:57: __main__: 63: Host Operating System is Linux.
INFO: 2021-03-26 16:39:57: __main__: 500: Workload Control Plane Network Type is  nsxt
INFO: 2021-03-26 16:39:57: __main__: 501: Begin Testing . . .
INFO: 2021-03-26 16:39:57: __main__: 506: TEST 1 - Checking Required YAML inputs for program:
ERROR: 2021-03-26 16:39:57: __main__: 509: ERROR - Missing required value for WCP_MGMT_STARTINGIP
ERROR: 2021-03-26 16:39:57: __main__: 509: ERROR - Missing required value for WCP_MGMT_MASK
ERROR: 2021-03-26 16:39:57: __main__: 509: ERROR - Missing required value for WCP_MGMT_GATEWAY
INFO: 2021-03-26 16:39:57: __main__: 513: TEST 2 - Checking Network Communication for vCenter
INFO: 2021-03-26 16:39:57: __main__: 515: TEST 2a - Checking IP is Active for vCenter
INFO: 2021-03-26 16:39:59: __main__: 98: SUCCESS - Can ping 10.173.13.81.
INFO: 2021-03-26 16:39:59: __main__: 517: TEST 2b - Checking DNS Servers are reachable on network
INFO: 2021-03-26 16:40:01: __main__: 98: SUCCESS - Can ping 10.173.13.90.
INFO: 2021-03-26 16:40:01: __main__: 520: TEST 2c - Checking Name Resolution for vCenter
INFO: 2021-03-26 16:40:02: __main__: 79: Checking DNS Server 10.173.13.90 for A Record for vcsa.tpmlab.vmware.com
INFO: 2021-03-26 16:40:02: __main__: 85: SUCCESS-The Hostname, vcsa.tpmlab.vmware.com resolves to the IP 10.173.13.81
ERROR: 2021-03-26 16:40:02: __main__: 88: ERROR - Missing PTR Record. The IP, 10.173.13.81 does not resolve to the Hostname vcsa.tpmlab.vmware.com
INFO: 2021-03-26 16:40:02: __main__: 523: TEST 3 - Checking VC is reachable via API using provided credentials
INFO: 2021-03-26 16:40:02: __main__: 108: Trying to connect to VCENTER SERVER . . .
INFO: 2021-03-26 16:40:03: __main__: 110: SUCCESS-Connected to vCenter VMware vCenter Server
INFO: 2021-03-26 16:40:03: __main__: 528: TEST4 - Checking for the  Datacenter
INFO: 2021-03-26 16:40:03: __main__: 125: SUCCESS - Managed Object Datacenter found.
INFO: 2021-03-26 16:40:03: __main__: 532: TEST 5 - Checking for the Cluster
INFO: 2021-03-26 16:40:04: __main__: 137: SUCCESS - Cluster Object One-Node-66 found.
INFO: 2021-03-26 16:40:04: __main__: 538: TEST 5a - Checking Hosts in the Cluster
INFO: 2021-03-26 16:40:04: __main__: 148: Found ESX Host 10.172.209.66 incluster One-Node-66
INFO: 2021-03-26 16:40:04: __main__: 152: SUCCESS - ESXi Host 10.172.209.66 overall Status is Green.
INFO: 2021-03-26 16:40:04: __main__: 543: TEST 6 - Checking Existence of Storage Profiles
INFO: 2021-03-26 16:40:04: __main__: 544: TEST 6a - Checking Connecting to SPBM
INFO: 2021-03-26 16:40:05: __main__: 546: TEST 6b - Getting Storage Profiles from SPBM
INFO: 2021-03-26 16:40:06: __main__: 228: SUCCESS - Found Storage Profile thin.
ERROR: 2021-03-26 16:40:07: __main__: 232: ERROR - Storage Profile thinner not found
INFO: 2021-03-26 16:40:07: __main__: 552: TEST 7 - Not required - Checking Existence of the Datastores
INFO: 2021-03-26 16:40:08: __main__: 125: SUCCESS - Managed Object 66-datastore3 found.
INFO: 2021-03-26 16:40:08: __main__: 556: TEST 8 - Checking for the vds
INFO: 2021-03-26 16:40:08: __main__: 125: SUCCESS - Managed Object vds-1 found.
INFO: 2021-03-26 16:40:08: __main__: 560: TEST 9 - Establishing REST session to VC API
INFO: 2021-03-26 16:40:09: __main__: 262: SUCCESS - Successfully established session to VC, status_code
ERROR: 2021-03-26 16:40:09: __main__: 569: Datacenter ID is datacenter-2
INFO: 2021-03-26 16:40:10: __main__: 572: TEST 10 - Checking if cluster One-Node-66 is WCP Compatible
ERROR: 2021-03-26 16:40:10: __main__: 285: ERROR - Cluster domain-c40895 is NOT compatible for reasons listed below.
ERROR: 2021-03-26 16:40:10: __main__: 289: + Reason-Failed to list all distributed switches in vCenter 6bd73038-66cb-4f40-a165-591a35f217e6.
ERROR: 2021-03-26 16:40:10: __main__: 289: + Reason-Cluster domain-c40895 does not have HA enabled.
ERROR: 2021-03-26 16:40:10: __main__: 289: + Reason-Cluster domain-c40895 must have DRS enabled and set to fully automated to enable vSphere namespaces.
ERROR: 2021-03-26 16:40:10: __main__: 289: + Reason-Cluster domain-c40895 has hosts that are not licensed for vSphere Namespaces.
ERROR: 2021-03-26 16:40:10: __main__: 289: + Reason-Cluster domain-c40895 has hosts with unsupported ESX version.
ERROR: 2021-03-26 16:40:10: __main__: 289: + Reason-Cluster domain-c40895 is missing compatible NSX-T VDS.
INFO: 2021-03-26 16:40:10: __main__: 576: TEST 11 - Checking time accuracy/synchronization in environment
INFO: 2021-03-26 16:40:10: __main__: 579: TEST 11a - Checking time on vCenter Appliance
INFO: 2021-03-26 16:40:10: __main__: 302: SUCCESS - vCenter 24hr time is 16:40:10
INFO: 2021-03-26 16:40:10: __main__: 583: TEST 11b - Checking time on ESXi hosts
INFO: 2021-03-26 16:40:11: __main__: 148: Found ESX Host 10.172.209.66 incluster One-Node-66
INFO: 2021-03-26 16:40:11: __main__: 152: SUCCESS - ESXi Host 10.172.209.66 overall Status is Green.
INFO: 2021-03-26 16:40:11: __main__: 164: ESXi Host 10.172.209.66 24hr time is 16:40:11.
INFO: 2021-03-26 16:40:11: __main__: 589: TEST 11c - Checking max time deltas on ESXi and vCenter hosts is less than 30
INFO: 2021-03-26 16:40:11: __main__: 172: Lowest Time of all the Nodes is 1900-01-01 16:40:10.
INFO: 2021-03-26 16:40:11: __main__: 174: Highest Time of all the Nodes is 1900-01-01 16:40:11.
INFO: 2021-03-26 16:40:11: __main__: 178: Maximum allowable time drift is 0:00:30.
INFO: 2021-03-26 16:40:11: __main__: 179: Largest Time delta between all nodes is 0:00:01.
INFO: 2021-03-26 16:40:11: __main__: 182: SUCCESS - Max Time Drift between all nodes is 0:00:01 which is below Maximum.
INFO: 2021-03-26 16:40:11: __main__: 593: TEST 12 - Checking for existence and configuration of Content Library
INFO: 2021-03-26 16:40:12: __main__: 314: ERROR - No content libraries found on vCenter
INFO: 2021-03-26 16:40:12: __main__: 637: Begin NSX-T Networking checks
INFO: 2021-03-26 16:40:12: __main__: 640: TEST 13 - Checking for the Management VDS PortGroup
ERROR: 2021-03-26 16:40:14: __main__: 129: ERROR - Managed Object management-vm not found.
INFO: 2021-03-26 16:40:14: __main__: 644: TEST 14 - Checking for the Uplink VDS PortGroup
ERROR: 2021-03-26 16:40:16: __main__: 129: ERROR - Managed Object ext-uplink-edge not found.
INFO: 2021-03-26 16:40:16: __main__: 648: TEST 15 - Checking for the Edge TEP VDS PortGroup
ERROR: 2021-03-26 16:40:18: __main__: 129: ERROR - Managed Object tep-edge not found.
INFO: 2021-03-26 16:40:18: __main__: 651: TEST 16 - Checking Network Communication for NSX-T Manager Unified Appliance
INFO: 2021-03-26 16:40:18: __main__: 653: TEST 16a - Checking IP is Active for NSX Manager
INFO: 2021-03-26 16:40:20: __main__: 98: SUCCESS - Can ping 10.173.13.82.
INFO: 2021-03-26 16:40:20: __main__: 655: TEST 16b - Checking Name Resolution for NSX Manager
INFO: 2021-03-26 16:40:20: __main__: 79: Checking DNS Server 10.173.13.90 for A Record for nsxmgr.tpmlab.vmware.com
INFO: 2021-03-26 16:40:20: __main__: 85: SUCCESS-The Hostname, nsxmgr.tpmlab.vmware.com resolves to the IP 10.173.13.82
ERROR: 2021-03-26 16:40:20: __main__: 88: ERROR - Missing PTR Record. The IP, 10.173.13.82 does not resolve to the Hostname nsxmgr.tpmlab.vmware.com
INFO: 2021-03-26 16:40:20: __main__: 666: TEST 17 - Checking on NSX API, credentials, and Cluster Status
INFO: 2021-03-26 16:40:21: __main__: 343: SUCCESS - NSX Manager Cluster is Healthy.
INFO: 2021-03-26 16:40:21: __main__: 669: TEST 18 - Checking on NSX State for all Nodes in vSphere cluster One-Node-66
INFO: 2021-03-26 16:40:21: __main__: 358: Found Compute Clusters in NSX.
INFO: 2021-03-26 16:40:21: __main__: 365: SUCCESS - Found NSX Compute Cluster One-Node-66 which matches vSphere HA Cluster.
INFO: 2021-03-26 16:40:21: __main__: 387: Checking ESX Node with Display Name 10.172.209.66 and UUID 8be80863-a62a-4496-9622-6f05dd504d03:host-39053 in Cluster 8be80863-a62a-4496-9622-6f05dd504d03:domain-c40895
ERROR: 2021-03-26 16:40:21: __main__: 395: ERROR - NSX not initialized successfully on ESX Node 10.172.209.66
INFO: 2021-03-26 16:40:21: __main__: 405: SUCCESS - ESX Node 10.172.209.66 is connected to NSX Manager
INFO: 2021-03-26 16:40:21: __main__: 411: SUCCESS - ESX Node 10.172.209.66 is NOT in Maintenance Mode
INFO: 2021-03-26 16:40:21: __main__: 399: SUCCESS - ESX Node 10.172.209.66 is powered on
INFO: 2021-03-26 16:40:21: __main__: 675: TEST 19 - Checking on NSX Edge Cluster Health
INFO: 2021-03-26 16:40:21: __main__: 435: Assuming there is only ONE Edge Cluster for the POC
INFO: 2021-03-26 16:40:21: __main__: 438: SUCCESS - Found Edge Cluster with ID 02b98b5f-de95-4d19-a2be-50b07162a899.
INFO: 2021-03-26 16:40:21: __main__: 454: SUCCESS - Edge Cluster 02b98b5f-de95-4d19-a2be-50b07162a899 is Ready.
INFO: 2021-03-26 16:40:21: __main__: 679: TEST 19a - Checking Edge Node Size is Large
INFO: 2021-03-26 16:40:21: __main__: 467: ERROR - Edge Cluster 02b98b5f-de95-4d19-a2be-50b07162a899 has no members.
INFO: 2021-03-26 16:40:21: __main__: 683: TEST 20 - Checking on existence of NSX T0 Router
INFO: 2021-03-26 16:40:21: __main__: 488: ERROR - No T0 routers found. Create a T0 router per documentation
INFO: 2021-03-26 16:40:21: __main__: 694: ************************************************
INFO: 2021-03-26 16:40:21: __main__: 695: ** All checks were run. Validation Complete.  **
INFO: 2021-03-26 16:40:21: __main__: 696: ************************************************
**OR**

❯ wcp_tests.py -n vsphere

INFO: 2021-03-26 16:56:35: __main__: 62: Looking in /root for test_params.yaml file
INFO: 2021-03-26 16:56:35: __main__: 63: Host Operating System is Linux.
INFO: 2021-03-26 16:56:35: __main__: 500: Workload Control Plane Network Type is  vsphere
INFO: 2021-03-26 16:56:35: __main__: 501: Begin Testing . . .
INFO: 2021-03-26 16:56:35: __main__: 506: TEST 1 - Checking Required YAML inputs for program:
ERROR: 2021-03-26 16:56:35: __main__: 509: ERROR - Missing required value for WCP_MGMT_STARTINGIP
ERROR: 2021-03-26 16:56:35: __main__: 509: ERROR - Missing required value for WCP_MGMT_MASK
ERROR: 2021-03-26 16:56:35: __main__: 509: ERROR - Missing required value for WCP_MGMT_GATEWAY
INFO: 2021-03-26 16:56:35: __main__: 513: TEST 2 - Checking Network Communication for vCenter
INFO: 2021-03-26 16:56:35: __main__: 515: TEST 2a - Checking IP is Active for vCenter
INFO: 2021-03-26 16:56:37: __main__: 98: SUCCESS - Can ping 10.173.13.81.
INFO: 2021-03-26 16:56:37: __main__: 517: TEST 2b - Checking DNS Servers are reachable on network
INFO: 2021-03-26 16:56:39: __main__: 98: SUCCESS - Can ping 10.173.13.90.
INFO: 2021-03-26 16:56:39: __main__: 520: TEST 2c - Checking Name Resolution for vCenter
INFO: 2021-03-26 16:56:39: __main__: 79: Checking DNS Server 10.173.13.90 for A Record for vcsa.tpmlab.vmware.com
INFO: 2021-03-26 16:56:39: __main__: 85: SUCCESS-The Hostname, vcsa.tpmlab.vmware.com resolves to the IP 10.173.13.81
ERROR: 2021-03-26 16:56:39: __main__: 88: ERROR - Missing PTR Record. The IP, 10.173.13.81 does not resolve to the Hostname vcsa.tpmlab.vmware.com
INFO: 2021-03-26 16:56:39: __main__: 523: TEST 3 - Checking VC is reachable via API using provided credentials
INFO: 2021-03-26 16:56:39: __main__: 108: Trying to connect to VCENTER SERVER . . .
INFO: 2021-03-26 16:56:40: __main__: 110: SUCCESS-Connected to vCenter VMware vCenter Server
INFO: 2021-03-26 16:56:40: __main__: 528: TEST4 - Checking for the  Datacenter
INFO: 2021-03-26 16:56:41: __main__: 125: SUCCESS - Managed Object Datacenter found.
INFO: 2021-03-26 16:56:41: __main__: 532: TEST 5 - Checking for the Cluster
INFO: 2021-03-26 16:56:41: __main__: 137: SUCCESS - Cluster Object One-Node-66 found.
INFO: 2021-03-26 16:56:41: __main__: 538: TEST 5a - Checking Hosts in the Cluster
INFO: 2021-03-26 16:56:41: __main__: 148: Found ESX Host 10.172.209.66 incluster One-Node-66
INFO: 2021-03-26 16:56:42: __main__: 152: SUCCESS - ESXi Host 10.172.209.66 overall Status is Green.
INFO: 2021-03-26 16:56:42: __main__: 543: TEST 6 - Checking Existence of Storage Profiles
INFO: 2021-03-26 16:56:42: __main__: 544: TEST 6a - Checking Connecting to SPBM
INFO: 2021-03-26 16:56:42: __main__: 546: TEST 6b - Getting Storage Profiles from SPBM
INFO: 2021-03-26 16:56:43: __main__: 228: SUCCESS - Found Storage Profile thin.
ERROR: 2021-03-26 16:56:44: __main__: 232: ERROR - Storage Profile thinner not found
INFO: 2021-03-26 16:56:44: __main__: 552: TEST 7 - Not required - Checking Existence of the Datastores
INFO: 2021-03-26 16:56:45: __main__: 125: SUCCESS - Managed Object 66-datastore3 found.
INFO: 2021-03-26 16:56:45: __main__: 556: TEST 8 - Checking for the vds
INFO: 2021-03-26 16:56:46: __main__: 125: SUCCESS - Managed Object vds-1 found.
INFO: 2021-03-26 16:56:46: __main__: 560: TEST 9 - Establishing REST session to VC API
INFO: 2021-03-26 16:56:46: __main__: 262: SUCCESS - Successfully established session to VC, status_code
ERROR: 2021-03-26 16:56:47: __main__: 569: Datacenter ID is datacenter-2
INFO: 2021-03-26 16:56:47: __main__: 572: TEST 10 - Checking if cluster One-Node-66 is WCP Compatible
ERROR: 2021-03-26 16:56:49: __main__: 285: ERROR - Cluster domain-c40895 is NOT compatible for reasons listed below.
ERROR: 2021-03-26 16:56:49: __main__: 289: + Reason-Failed to list all distributed switches in vCenter 6bd73038-66cb-4f40-a165-591a35f217e6.
ERROR: 2021-03-26 16:56:49: __main__: 289: + Reason-Cluster domain-c40895 does not have HA enabled.
ERROR: 2021-03-26 16:56:49: __main__: 289: + Reason-Cluster domain-c40895 must have DRS enabled and set to fully automated to enable vSphere namespaces.
ERROR: 2021-03-26 16:56:49: __main__: 289: + Reason-Cluster domain-c40895 has hosts that are not licensed for vSphere Namespaces.
ERROR: 2021-03-26 16:56:49: __main__: 289: + Reason-Cluster domain-c40895 has hosts with unsupported ESX version.
ERROR: 2021-03-26 16:56:49: __main__: 289: + Reason-Cluster domain-c40895 is missing compatible NSX-T VDS.
INFO: 2021-03-26 16:56:49: __main__: 576: TEST 11 - Checking time accuracy/synchronization in environment
INFO: 2021-03-26 16:56:49: __main__: 579: TEST 11a - Checking time on vCenter Appliance
INFO: 2021-03-26 16:56:49: __main__: 302: SUCCESS - vCenter 24hr time is 16:56:49
INFO: 2021-03-26 16:56:49: __main__: 583: TEST 11b - Checking time on ESXi hosts
INFO: 2021-03-26 16:56:49: __main__: 148: Found ESX Host 10.172.209.66 incluster One-Node-66
INFO: 2021-03-26 16:56:49: __main__: 152: SUCCESS - ESXi Host 10.172.209.66 overall Status is Green.
INFO: 2021-03-26 16:56:50: __main__: 164: ESXi Host 10.172.209.66 24hr time is 16:56:50.
INFO: 2021-03-26 16:56:50: __main__: 589: TEST 11c - Checking max time deltas on ESXi and vCenter hosts is less than 30
INFO: 2021-03-26 16:56:50: __main__: 172: Lowest Time of all the Nodes is 1900-01-01 16:56:49.
INFO: 2021-03-26 16:56:50: __main__: 174: Highest Time of all the Nodes is 1900-01-01 16:56:50.
INFO: 2021-03-26 16:56:50: __main__: 178: Maximum allowable time drift is 0:00:30.
INFO: 2021-03-26 16:56:50: __main__: 179: Largest Time delta between all nodes is 0:00:01.
INFO: 2021-03-26 16:56:50: __main__: 182: SUCCESS - Max Time Drift between all nodes is 0:00:01 which is below Maximum.
INFO: 2021-03-26 16:56:50: __main__: 593: TEST 12 - Checking for existence and configuration of Content Library
INFO: 2021-03-26 16:56:50: __main__: 314: ERROR - No content libraries found on vCenter
INFO: 2021-03-26 16:56:50: __main__: 602: Begin vSphere Networking checks
INFO: 2021-03-26 16:56:50: __main__: 605: TEST 13 - Checking for the Primary Workload Network PortGroup
ERROR: 2021-03-26 16:56:53: __main__: 129: ERROR - Managed Object not_there not found.
INFO: 2021-03-26 16:56:53: __main__: 609: TEST 14 - Checking for the Workload Network PortGroup
ERROR: 2021-03-26 16:56:55: __main__: 129: ERROR - Managed Object ext-uplink-edge not found.
INFO: 2021-03-26 16:56:55: __main__: 613: TEST 15 - Checking HAProxy Health
INFO: 2021-03-26 16:56:55: __main__: 614: TEST 15a - Checking reachability of HAProxy Frontend IP
ERROR: 2021-03-26 16:57:07: __main__: 102: ERROR - Cant ping 192.168.100.163.
INFO: 2021-03-26 16:57:07: __main__: 619: TEST 15b - Checking login to HAPROXY DataPlane API
ERROR: 2021-03-26 16:57:39: __main__: 629: Caught exception: HTTPSConnectionPool(host='192.168.100.163', port=5556): Max retries exceeded with url: /v2/services/haproxy/configuration/backends (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7f58ccf9cc70>: Failed to establish a new connection: [Errno 110] Connection timed out'))
INFO: 2021-03-26 16:57:39: __main__: 694: ************************************************
INFO: 2021-03-26 16:57:39: __main__: 695: ** All checks were run. Validation Complete.  **
INFO: 2021-03-26 16:57:39: __main__: 696: ************************************************


