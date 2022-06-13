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
   parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on')
   parser.add_argument('-u', '--user', required=True, action='store', help='User name to use when connecting to host')
   parser.add_argument('-p', '--password', required=False, action='store', help='Password to use when connecting to host')
   args = parser.parse_args()
   return args

def stop_vc_svcname(s,vcip,svc_name):
    json_config = {"startup_type": "MANUAL"}
    startup_json_response = s.patch('https://' + vcip + '/api/vcenter/services/' + svc_name, json=json_config)
    if startup_json_response.status_code==204:
        print("-Successfully set WCP Service Startup to MANUAL. Response Code %s " % startup_json_response.status_code )
    else:
        print("-ERROR-Unable to setup Startup for WCP Service to Manual")
        return 0
    
    stop_json_response = s.post('https://' + vcip + '/api/vcenter/services/' + svc_name + '?action=stop')
    print(stop_json_response.status_code)
    if stop_json_response.status_code==204:
        print("-Successfully stopped WCP Service. Response Code %s " % stop_json_response.status_code )
    else:
        print("-ERROR-Unable to stop WCP Service")
        return 0
    
def shutdown_Vm(delay,list_of_vms):
    for vm in list_of_vms:
        try:
            print("-Shutting dow VM %s." % vm.summary.config.name)
            vm.ShutdownGuest()
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
    if args.password:
        password = args.password
    else:
        password = getpass.getpass(prompt='Enter password for host %s and user %s: ' % (args.host,args.user))

    # PyVMomi work to get all VMs on VC
    service_instance = None
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE   

    try:
        print("\nLogging into vCenter API with supplied credentials ")
        service_instance = SmartConnect(host=args.host,
                                                user=args.user,
                                                pwd=args.password,
                                                port=int(args.port),
                                                sslContext=context)
        if not service_instance:
            print("Could not connect to the specified host using specified "
                  "username and password")
            return -1

        atexit.register(Disconnect, service_instance)
        content = service_instance.RetrieveContent()
        search_index=service_instance.content.searchIndex

        # Search for all VM Objects in vSphere API
        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.VirtualMachine],
                                                          True)
        
        vmList = objview.view
        objview.Destroy()
        print("\nSTEP 0 - Getting all VMs from VC API")
        print("-Successfully logged into vCenter")

        print("-Found %s VMS on VC. " % str(len(vmList)))
        
        print("\nSTEP 1 - Getting all Supervisor Control Plane VMs from VC API")
        supervisor_cluster_vms = []
        for vmobject in vmList:
            if "SupervisorControlPlaneVM" in vmobject.summary.config.name:
                print("-Found Supervisor Control Plane VM %s. " % vmobject.summary.config.name)
                supervisor_cluster_vms.append(vmobject)
        
    except vmodl.MethodFault as error:
        print("ERROR-Caught vmodl fault : " + error.msg)
        return -1

    # Set REST VC Variables
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    headers = {'content-type': 'application/json'}
    vcip = args.host
    cluster_id = "domain-c8"
    s = "Global"
    s = requests.Session()
    s.verify = False

    # Connect to VCenter and start a REST session
    vcsession = s.post('https://' + vcip + '/rest/com/vmware/cis/session', auth=(args.user, args.password))
    if not vcsession.ok:
        print("Session creation is failed, please check vcenter connection")
        sys.exit()
    token = json.loads(vcsession.text)["value"]
    token_header = {'vmware-api-session-id': token}

    print("\nSTEP 2 - Getting all Workload Cluster VMs from K8s API Server on Supervisor Cluster")
    ## GET the Supervisor Cluster apiserver Endpoint
    wcp_endpoint = check_wcp_cluster_status(s,vcip,cluster_id)
    print("-WCP Endpoint for SC is ", wcp_endpoint)

    ## Log into the Supervisor Cluster to create kubeconfig contexts
    try:
        subprocess.check_call(['kubectl', 'vsphere', 'login', '--insecure-skip-tls-verify', '--server', wcp_endpoint, '-u', args.user]) 
    except:
        print("Could not login to WCP SC Endpoint.  Is WCP Service running ? ")

    ''' 
    # DEBUG -Test K8s API with a simple Call   
    client1 = client.CoreV1Api(api_client=config.new_client_from_config(context=wcp_endpoint)) 
    for i in client1.list_pod_for_all_namespaces().items:
        print ('Found a POD {0}'.format(i.metadata.name))
    '''
    # Create k8s client for CustomObjects
    client2=client.CustomObjectsApi(api_client=config.new_client_from_config(context=wcp_endpoint))

    # Return Cluster API "Machine" objects
    # This builds a list of every Guest Cluster VM (Not including SC VMs)
    machine_list_dict=client2.list_namespaced_custom_object("cluster.x-k8s.io","v1beta1","","machines",pretty="True")
    print("-Found ", str(len(machine_list_dict)), ' kubernetes Workload Cluster VMs')
    wkld_cluster_vms = []
    for machine in machine_list_dict["items"]:
        print('-Found CAPI Machine Object in SC. VM Name = {0}'.format(machine['metadata']['name']))
        #print(' -Machine Namespace - {0}'.format(machine['metadata']['namespace']))
        #print(' -Machine Cluster - {0}'.format(machine['metadata']['labels']['cluster.x-k8s.io/cluster-name']))
        # Search pyVmomi all VMs by DNSName
        vm=search_index.FindByDnsName(None, machine['metadata']['name'],True)
        
        if vm is None:
            print("ERROR-Could not find specified VM with VC API ")
  
        else:
            print("-Found VM matching CAPI Machine Name in VC API. VM=%s. " % vmobject.summary.config.name)
            #print(' -VM guest OS ID =', vm.summary.config.guestId)
            #print(' -VM guest Name =', vm.summary.config.guestFullName)
            wkld_cluster_vms.append(vm)

    # Shutdown WCP Service on vCenter
    print("\nSTEP 3 - Stopping WCP Service on vCenter")
    input("-Press Enter to confirm/continue...")
    stop_vc_svcname(s,vcip,"wcp")

    # Shutdown SC Cluster VMs
    print("\nSTEP 4 - Shutting down all Supervisor Cluster VMs")
    print("-The following SC Cluster VMs will be shutdown" )
    for svm in supervisor_cluster_vms:
        print("\t",svm.summary.config.name)
    input("-Press Enter to confirm/continue...")
    shutdown_Vm(60,supervisor_cluster_vms)

    # Shutdown WCP Service on vCenter
    print("\nSTEP 5 - Shutting down all Guest Cluster VMs")
    print("-The following Workload Cluster VMs will be shutdown" )
    for wvm in wkld_cluster_vms:
        print("\t",wvm.summary.config.name)
    input("-Press Enter to confirm/continue...")
    shutdown_Vm(10,wkld_cluster_vms)


    # Clean up and exit...
    session_delete = s.delete('https://' + vcip + '/rest/com/vmware/cis/session', auth=(args.user, args.password))
    print("\nPOST - Successfully Completed Script - Cleaning up REST Session to VC.")


# Start program
if __name__ == "__main__":
    main()
