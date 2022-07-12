#!/usr/bin/env python3

from unicodedata import name
import requests
import json
import sys
import argparse
import getpass
import subprocess
from kubernetes import client
from kubernetes import config
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim, vmodl
import ssl
import atexit
import time

def GetArgs():
   # Supports the command-line arguments listed below.
   parser = argparse.ArgumentParser(description='Process args for shutting down a Virtual Machine')
   parser.add_argument('-v', '--vc_host', required=True, action='store', help='Remote VC host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on')
   parser.add_argument('-u', '--vc_user', required=True, action='store', help='User name to use when connecting to VC host')
   parser.add_argument('-p', '--vc_password', required=False, action='store', help='Password to use when connecting to VC host')
   parser.add_argument('-e', '--esx_user', required=False, action='store', default="root", help='User name to use when connecting to ESXi host')
   parser.add_argument('-f', '--esx_password', required=False, action='store', help='Password to use when connecting to ESXi host')
   parser.add_argument('-c', '--cluster', required=False, action='store', help='vSphere Cluster that vSphere with Tanzu is configured on.')
   args = parser.parse_args()
   return args

def get_si(host,user,password,args):
    # PyVMomi work to get all VMs on VC
    service_instance = None
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE   
    service_instance = SmartConnect(host=host,
                                            user=user,
                                            pwd=password,
                                            port=int(args.port),
                                            sslContext=context)
    print("--Successfully logged in to VIM API")
    return service_instance

    if not service_instance:
        print("--Could not connect to the specified host using specified username and password")
        return -1

def stop_vc_svcname(s,vcip,svc_name):
    json_config = {"startup_type": "MANUAL"}
    startup_json_response = s.patch('https://' + vcip + '/api/vcenter/services/' + svc_name, json=json_config)
    if startup_json_response.status_code==204:
        print("--Successfully set WCP Service Startup to MANUAL. Response Code %s " % startup_json_response.status_code )
    else:
        print("--ERROR-Unable to setup Startup for WCP Service to Manual")
        return 0
    
    stop_json_response = s.post('https://' + vcip + '/api/vcenter/services/' + svc_name + '?action=stop')
    if stop_json_response.status_code==204:
        print("--Successfully stopped WCP Service. Response Code %s " % stop_json_response.status_code )
    else:
        print("--ERROR-Unable to stop WCP Service")
        return 0
    
def shutdown_Vm(delay,list_of_vms):
    for vm in list_of_vms:
        try:
            print("--Shutting down VM %s." % vm.summary.config.name)
            vm.ShutdownGuest()
            print("--Pausing for %s seconds..." % delay)
            time.sleep(delay)
        
        except vmodl.MethodFault as error:
            print("--ERROR-Caught error trying to shutdown VM  " )
            print("--ERROR-Caught vmodl fault : " + error.msg)
            return -1

def shutdown_sc_vm(delay,vm_name,vm_uuid,vm_host_ip,esx_user,esx_password,args):
    try:
        print("\n--Shutting down VM " + vm_name + " on host "+ vm_host_ip )
        esx_service_instance = get_si(vm_host_ip, esx_user, esx_password, args)
        content = esx_service_instance.RetrieveContent()
        atexit.register(Disconnect, esx_service_instance)
        search_index=esx_service_instance.content.searchIndex
        scvm=search_index.FindByUuid(None, vm_uuid,True)

        if scvm is None:
            print("--Could not find virtual machine '{0}'".format(args.uuid))
            sys.exit(1)

        print("--Found SC Virtual Machine on ESX")
        details = {'--name': scvm.summary.config.name,
                '--instance UUID': scvm.summary.config.instanceUuid,
                '--bios UUID': scvm.summary.config.uuid,
                '--path to VM': scvm.summary.config.vmPathName,
                '--host name': scvm.runtime.host.name,
                '--last booted timestamp': scvm.runtime.bootTime,
                }
        
        for name, value in details.items():
            print("{0:{width}{base}}: {1}".format(name, value, width=25, base='s'))
        
        print("-Shutting dow VM %s" % scvm.summary.config.name)
        scvm.ShutdownGuest()
        print("-Pausing for %s seconds..." % delay)
        time.sleep(delay)
    
    except vmodl.MethodFault as error:
        print("-ERROR-Caught error trying to shutdown VM  " )
        print("-ERROR-Caught vmodl fault : " + error.msg)
        return -1

def check_wcp_cluster_status(s,vcip,cluster):
    json_response = s.get('https://' + vcip + '/api/vcenter/namespace-management/clusters/' + cluster)
    if json_response.ok:
        result = json.loads(json_response.text)
        if result["config_status"] == "RUNNING":
            if result["kubernetes_status"] == "READY":
                return result["api_server_cluster_endpoint"]
        else:
            return 0
    else:
        return 0

def main():

    args = GetArgs()
    if args.vc_password:
        vc_password = args.vc_password
    else:
        vc_password = getpass.getpass(prompt='Enter password for VC host %s and user %s: ' % (args.vc_host,args.vc_user))
    if args.esx_password:
        esx_password = args.esx_password
    else:
        esx_password = getpass.getpass(prompt='Enter root password for ESXi hosts: ' )
    if args.cluster:
        cluster_id = args.cluster
    else:
        cluster_id = "domain-c8"

    try:
        print("\nSTEP 0 - Logging into vCenter API with supplied credentials ")
        vc_service_instance = get_si(args.vc_host,args.vc_user, vc_password,args)
        atexit.register(Disconnect, vc_service_instance)
        content = vc_service_instance.RetrieveContent()
        search_index=vc_service_instance.content.searchIndex

        # Search for all VM Objects in vSphere API
        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.VirtualMachine],
                                                          True)
        
        vmList = objview.view
        objview.Destroy()
        print("-Found a total of %s VMS on VC. " % str(len(vmList)))
        
    except vmodl.MethodFault as error:
        print("-ERROR-Caught vmodl fault : " + error.msg)
        return -1

    # Set REST VC Variables
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    headers = {'content-type': 'application/json'}
    s = "Global"
    s = requests.Session()
    s.verify = False

    # Connect to VCenter and start a REST session
    vcsession = s.post('https://' + args.vc_host + '/rest/com/vmware/cis/session', auth=(args.vc_user, vc_password))
    if not vcsession.ok:
        print("-Session creation is failed, please check vcenter connection")
        sys.exit()
    token = json.loads(vcsession.text)["value"]
    token_header = {'vmware-api-session-id': token}

    print("\nSTEP 1 - Getting all Workload Cluster VMs from K8s API Server on Supervisor Cluster")
    ## GET the Supervisor Cluster apiserver Endpoint
    wcp_endpoint = check_wcp_cluster_status(s,args.vc_host,cluster_id)
    print("-WCP Endpoint for SC is ", wcp_endpoint)

    ## Log into the Supervisor Cluster to create kubeconfig contexts
    try:
        subprocess.check_call(['kubectl', 'vsphere', 'login', '--insecure-skip-tls-verify', '--server', wcp_endpoint, '-u', args.vc_user]) 
    except:
        print("-Could not login to WCP SC Endpoint.  Is WCP Service running ? ")

    # Create k8s client for CustomObjects
    client2=client.CustomObjectsApi(api_client=config.new_client_from_config(context=wcp_endpoint))

    # Return Cluster API "Machine" objects
    # This builds a list of every Guest Cluster VM (Not including SC VMs)
    machine_list_dict=client2.list_namespaced_custom_object("cluster.x-k8s.io","v1beta1","","machines",pretty="True")
    print("\n-Found ", str(len(machine_list_dict)), ' kubernetes Workload Cluster VMs')
    wkld_cluster_vms = []
    for machine in machine_list_dict["items"]:
        print('-Found CAPI Machine Object in SC. VM Name = {0}'.format(machine['metadata']['name']))
        #print(' -Machine Namespace - {0}'.format(machine['metadata']['namespace']))
        #print(' -Machine Cluster - {0}'.format(machine['metadata']['labels']['cluster.x-k8s.io/cluster-name']))
        # Search pyVmomi all VMs by DNSName
        vm=search_index.FindByDnsName(None, machine['metadata']['name'],True)
        
        if vm is None:
            print("-ERROR-Could not find specified VM with VC API ")
  
        else:
            print("-Found VM matching CAPI Machine Name in VC API. VM=%s. " % vm.summary.config.name)
            wkld_cluster_vms.append(vm)

    # Shutdown WCP Service on vCenter
    print("\nSTEP 2 - Stopping WCP Service on vCenter")
    input("-Press Enter to confirm/continue...")
    #stop_vc_svcname(s,vcip,"wcp")

    ## Find 3 SC CP VMs and shutdown from the ESXi hosts they are running on.
    print("\nSTEP 3 - Shutting Down all Supervisor Control Plane VMs ")
    for vmobject in vmList:
        if "SupervisorControlPlaneVM" in vmobject.summary.config.name:
            print("-Found Supervisor Control Plane VM %s. " % vmobject.summary.config.name)
            print("-VM",vmobject.summary.config.name, " is running on ESX host", vmobject.runtime.host.name)
            vnicManager = vmobject.runtime.host.configManager.virtualNicManager
            netConfig = vnicManager.QueryNetConfig("management")
            for vNic in netConfig.candidateVnic:
                if (netConfig.selectedVnic.index( vNic.key ) != -1):
                    # Below will return the Management IP (SC Address) for the ESxi host where SC VP VM is running.
                    print("-ESX host",vmobject.runtime.host.name," has Management IP", vNic.spec.ip.ipAddress)
                    # Due to permissions limitations we need to log into each ESXi host where the SC CP VM is running
                    # To perform the shutdown operation.
                    shutdown_sc_vm(25, vmobject.summary.config.name,vmobject.summary.config.uuid ,vNic.spec.ip.ipAddress,args.esx_user,esx_password,args)
                else:
                    print("\tvNic[ " + vNic.key + " ] is not selected; skipping it")

    input("-Press Enter to confirm/continue...or Control-C or Control-X to stop program")

    # Shutdown Guest Cluster Machines Virtual Machines
    print("\nSTEP 4 - Shutting down all Guest Cluster VMs")
    print("-The following Workload Cluster VMs will be shutdown" )
    for wvm in wkld_cluster_vms:
        print("-",wvm.summary.config.name)
    input("-Press Enter to confirm/continue...")
    shutdown_Vm(20,wkld_cluster_vms)

    # Clean up and exit...
    session_delete = s.delete('https://' + args.vc_host + '/rest/com/vmware/cis/session', auth=(args.vc_user, vc_password))
    print("\nPOST - Successfully Completed Script - Cleaning up REST Session to VC.")

# Start program
if __name__ == "__main__":
    main()
