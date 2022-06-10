#!/usr/bin/env python3
#


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


def GetArgs():
   """
   Supports the command-line arguments listed below.
   """
   parser = argparse.ArgumentParser(description='Process args for shutting down a Virtual Machine')
   parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on')
   parser.add_argument('-u', '--user', required=True, action='store', help='User name to use when connecting to host')
   parser.add_argument('-p', '--password', required=False, action='store', help='Password to use when connecting to host')
   parser.add_argument('-v', '--vmname', required=False, action='append', help='Names of the Virtual Machines to shutdown')
   args = parser.parse_args()
   return args

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

    # PyVMomi work to shutdown VMs
    service_instance = None
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE   

    try:
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

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + e.msg)
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

    ## RETURN the Supervisor Cluster Endpoint
    wcp_endpoint = check_wcp_cluster_status(s,vcip,cluster_id)
    print("WCP Endpoint for SC is ", wcp_endpoint)

    ## Log into the Supervisor Cluster to create kubeconfig contexts
    subprocess.check_call(['kubectl', 'vsphere', 'login', '--insecure-skip-tls-verify', '--server', wcp_endpoint, '-u', args.user])
    print("")    
    ''' 
    # DEBUG -Test K8s API with a simple Call   
    client1 = client.CoreV1Api(api_client=config.new_client_from_config(context=wcp_endpoint)) 
    for i in client1.list_pod_for_all_namespaces().items:
        print ('Found a POD {0}'.format(i.metadata.name))
    '''
    # Create k8s client for CustomObjects
    client2=client.CustomObjectsApi(api_client=config.new_client_from_config(context=wcp_endpoint))

    # Return Cluster API Machine CRD objects
    machine_list_dict=client2.list_namespaced_custom_object("cluster.x-k8s.io","v1beta1","","machines",pretty="True")
    ''' 
    print("\n PRINTING DICT KEY VALUES  \n")
    for key, value in machine_list_dict.items():
        print('machine_list_dict --> ***KEY', key, '-->', value)
    '''
    print("\n Found ", str(len(machine_list_dict)), ' kubernetes Workload Cluster VMs')

    for machine in machine_list_dict["items"]:
        print('\n Found Machine - {0}'.format(machine['metadata']['name']))
        print(' -Machine Namespace - {0}'.format(machine['metadata']['namespace']))
        print(' -Machine Cluster - {0}'.format(machine['metadata']['labels']['cluster.x-k8s.io/cluster-name']))
        # Search pyVmomi all VMs by DNSName
        vm=search_index.FindByDnsName(None, machine['metadata']['name'],True)
        
        if vm is None:
            print("Could not find specified VM with VC API ")
  
        else:
            print(" -Found VM in VC API ")
            print(' -VM name =', vm.summary.config.name)
            print(' -VM guest OS ID =', vm.summary.config.guestId)
            print(' -VM guest Name =', vm.summary.config.guestFullName)
            print(' --Shutting down Guest OS through VMware Tools ', vm.summary.config.name)
            try:
                vm.ShutdownGuest()
            except Exception:
                print("Caught error trying to shutdown VM  " )
     

    # Clean up and exit...
    session_delete = s.delete('https://' + vcip + '/rest/com/vmware/cis/session', auth=(args.user, args.password))

# Start program
if __name__ == "__main__":
    main()
