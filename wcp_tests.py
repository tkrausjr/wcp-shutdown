#!/usr/bin/env python3

# Borrowed NSX-T Rest Functions with permission from nsx-autoconfig Github project https://github.com/papivot/nsx-autoconfig 
#

import ssl
import requests
from datetime import datetime
from datetime import timedelta
from requests.auth import HTTPBasicAuth 
import sys
import json
import os
import platform
import yaml
import subprocess
import argparse
import pyVmomi
from http import cookies
from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.task import WaitForTask
from pyVim.connect import Disconnect
from pyVmomi import pbm, VmomiSupport
import logging

# Define ANSI Colors
CRED = '\033[91m'
CEND = '\033[0m'
CGRN = '\033[92m'

parser = argparse.ArgumentParser(description='vcenter_checks.py validates environments for succcesful Supervisor Clusters setup in vSphere 7 with Tanzu. Uses YAML configuration files to specify environment information to test. Find additional information at: gitlab.eng.vmware.com:TKGS-TSL/wcp-precheck.git')
parser.add_argument('--version', action='version',version='%(prog)s v0.6')
parser.add_argument('-n','--networking',choices=['nsxt','vsphere'], help='Networking Environment(nsxt, vsphere)', default='nsxt')
parser.add_argument('-v', '--verbosity', nargs="?", choices=['INFO','DEBUG'], default="INFO")
network_type=parser.parse_args().networking
verbosity = parser.parse_args().verbosity

# Setup logging parser
logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(name)s: %(lineno)d: %(message)s', "%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler('wcp_precheck_results.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

stream_handler=logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

if verbosity == 'DEBUG':
    file_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

currentDirectory = os.getcwd()
host_os = platform.system()
homedir = os.getenv('HOME')
logger.info("Looking in {} for test_params.yaml file".format(homedir))
logger.info("Host Operating System is {}.".format(host_os))
cfg_yaml = yaml.load(open(homedir+"/test_params.yaml"), Loader=yaml.Loader)

if (host_os != 'Darwin') and (host_os != 'Linux'):
    logger.info(f"Unfortunately {host_os} is not supported")

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
headers = {'content-type': 'application/json'}

def checkdns(hostname, ip):
    ## Validate Name Resolution for a hostname / IP pair
    try:
        for d in cfg_yaml["DNS_SERVERS"]:
            fwd_lookup = subprocess.check_output(['dig', cfg_yaml["VC_HOST"], '+short', str(d)], universal_newlines=True).strip()
            rev_lookup = subprocess.check_output(['dig', '-x', cfg_yaml["VC_IP"], '+short', str(d)], universal_newlines=True).strip()[:-1]
            logger.info('Checking DNS Server {} for A Record for {}'.format(d, hostname))
            logger.debug("Result of Forward Lookup {}".format(fwd_lookup))
            logger.debug("Result of Reverse Lookup {}".format(rev_lookup))
            if cfg_yaml["VC_IP"] != fwd_lookup:
                logger.error(CRED + "ERROR - Missing A Record. The Hostname, " + hostname + " does not resolve to the IP " + ip + CEND)
            else:
                logger.info(CGRN +"SUCCESS-The Hostname, " + hostname + " resolves to the IP " + ip + CEND)
            
            if cfg_yaml["VC_HOST"] != rev_lookup:
                logger.error(CRED + "ERROR - Missing PTR Record. The IP, " + ip + " does not resolve to the Hostname " + hostname + CEND)
            else:
                logger.info(CGRN +"SUCCESS-The IP, " + ip + " resolves to the Hostname " + hostname + CEND)


    except subprocess.CalledProcessError as err:
        raise ValueError("ERROR - Failure in the NSLookup subprocess call")

def check_active(host):
    if os.system("ping -c 3 " + host.strip(";") + ">/dev/null 2>&1" ) == 0:
        logger.info(CGRN +"SUCCESS - Can ping {}. ".format(host) + CEND)
        #return 0
    
    else:
        logger.error(CRED +"ERROR - Cant ping {}. ".format(host) + CEND)
        #return 1

def vc_connect(vchost, vcuser, vcpass):
    si = None
    try:
        logger.info("Trying to connect to VCENTER SERVER . . .")
        si = connect.SmartConnectNoSSL('https', vchost, 443, vcuser, vcpass)
        logger.info(CGRN + "SUCCESS-Connected to vCenter {}".format(si.content.about.name) + CEND)
        return si, si.RetrieveContent()
    except IOError as e:
        logger.error(CRED +"ERROR - connecting to vCenter, {}".format(vchost)  + CEND)
        logger.error(CRED +"Error is: {}".format(e) + CEND)
        logger.error("Exiting program. Please check vCenter connectivity and Name Resolution: ")
        sys.exit(e)

def get_obj(content, vimtype, objectname):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == objectname:
            logger.debug("Item:" + c.name) 
            logger.info(CGRN+"SUCCESS - Managed Object " + objectname + " found."+ CEND)
            obj = c
            break
    if not obj:
        logger.error(CRED +"ERROR - Managed Object " + objectname + " not found."+ CEND)
    return obj
      
def get_cluster(dc, objectname):
    obj = None
    clusters = dc.hostFolder.childEntity
    for cluster in clusters:  # Iterate through the clusters in the DC
        if cluster.name == objectname:
            logger.info(CGRN+"SUCCESS - Cluster Object " + objectname + " found."+ CEND)
            obj = cluster
            break
    if not obj:
        loggger.error(CRED + "ERROR - Cluster " + name + " not found.")
    return obj

def get_hosts_in_cluster(cluster):
    hosts = []
    for host in cluster.host :  # Iterate through the hosts in the cluster
        hosts.append(host)
        logger.info ("Found ESX Host {} incluster {}".format( host.name,cluster.name))
        if host.overallStatus != "green":
            logger.error(CRED+"ERROR - ESXi Host {} overall Status is not Green. Please correct any issues with this host.".format(host.name ) + CEND)
        else:
            logger.info(CGRN+"SUCCESS - ESXi Host {} overall Status is Green. ".format(host.name)+ CEND)      
    return hosts



def get_host_times(esx_hosts, host_times):
    for host in esx_hosts :  # Iterate through the hosts in the cluster
        if host.overallStatus == "green":
            host_time=host.configManager.dateTimeSystem.QueryDateTime()
            logger.debug("ESXi Host {} time is {}.".format(host.name,host_time)+ CEND)
            corrected_time = host_time.strftime('%H:%M:%S')
            host_times[host.name]=corrected_time
            logger.info("ESXi Host {} 24hr time is {}.".format(host.name,corrected_time)+ CEND)
        else:
            logger.error(CRED+"ERROR - Cannot check time on ESXi Host {}. It is not responding.".format(host.name)+ CEND)
    return host_times

def detect_time_drift(host_times):
    # Detect minimum and max time in a range of times in the host_times dict
    min_time = datetime.strptime(min(host_times.values()), '%H:%M:%S')
    logger.info("Lowest Time of all the Nodes is {}.".format(min_time)+ CEND)
    max_time = datetime.strptime(max(host_times.values()), '%H:%M:%S')
    logger.info("Highest Time of all the Nodes is {}.".format(max_time)+ CEND)
    # Define maximum allowable timedrift Min vs Max in Seconds
    max_delta =timedelta(days=0,seconds=30,minutes=0)
    delta = max_time - min_time
    logger.info("Maximum allowable time drift is {}.".format(max_delta))
    logger.info("Largest Time delta between all nodes is {}.".format(delta)+ CEND)
    
    if delta < max_delta:
        logger.info(CGRN+"SUCCESS - Max Time Drift between all nodes is {} which is below Maximum.".format(delta)+ CEND)

    else:
        logger.error(CRED+"ERROR - Max Time Drift between all nodes is {} which is higher than configured Max.".format(delta)+ CEND)
    

# retrieve SPBM API endpoint
def GetPbmConnection(vpxdStub):
    sessionCookie = vpxdStub.cookie.split('"')[1]
    httpContext = VmomiSupport.GetHttpContext()
    cookie = cookies.SimpleCookie()
    cookie["vmware_soap_session"] = sessionCookie
    httpContext["cookies"] = cookie
    VmomiSupport.GetRequestContext()["vcSessionCookie"] = sessionCookie
    hostname = vpxdStub.host.split(":")[0]

    context = ssl._create_unverified_context()
    pbmStub = pyVmomi.SoapStubAdapter(
        host=hostname,
        version="pbm.version.version1",
        path="/pbm/sdk",
        poolSize=0,
        sslContext=context)
    pbmSi = pbm.ServiceInstance("ServiceInstance", pbmStub)
    pbmContent = pbmSi.RetrieveContent()
    logger.debug(pbmContent)
    return (pbmSi, pbmContent)

def get_storageprofile(sp_name, pbmContent ):
    profiles = []
    pm = pbmContent.profileManager
    # Get all Storage Policies
    profileIds = pm.PbmQueryProfile(resourceType=pbm.profile.ResourceType(
        resourceType="STORAGE"), profileCategory="REQUIREMENT"
    )
    logger.debug(profileIds)
    if len(profileIds) > 0:
        logger.debug("Retrieved Storage Policies.")
        profiles = pm.PbmRetrieveContent(profileIds=profileIds)
        obj = None
        for profile in profiles:
            logger.debug("SP Name: %s " % profile.name)
            if profile.name == sp_name:
                logger.info(CGRN+"SUCCESS - Found Storage Policy {}.".format(sp_name)+ CEND)
                obj = profile
                break
        if not obj:
            logger.error(CRED + "ERROR - Storage Policy {} not found".format(sp_name)+ CEND) 
        return obj        
    else:
        logger.error(CRED + "ERROR - No Storage Policies found or defined "+ CEND)


def check_health_with_auth(verb, endpoint, port, url, username, password):
    s = requests.Session()
    s.verify = False
    if verb=="get":
        logger.debug("Performing Get")
        response=s.get('https://'+endpoint+':'+str(port)+url, auth=(username,password))
    elif verb=="post":
        logger.debug("Performing Post")
        response=s.post('https://'+endpoint+':'+str(port)+url, auth=(username,password))
        
    logger.debug(response)
    if not response.ok:
        logger.error(CRED + "ERROR - Received Status Code {} ".format(response.status_code) + CEND) 
    else:
        logger.info(CGRN + "SUCCESS - Received Status Code {} ".format(response.status_code) + CEND) 
       
def connect_vc_rest(vcip, userid, password):
    s = requests.Session()
    s.verify = False
    # Connect to VCenter and start a session
    session = s.post('https://' + vcip + '/rest/com/vmware/cis/session', auth=(userid, password))
    if not session.ok:
        logger.error(CRED + "ERROR - Could not establish session to VC, status_code ".format(session.status_code) + CEND) 
    else:
        logger.info(CGRN + "SUCCESS - Successfully established session to VC, status_code ".format(session.status_code) + CEND) 

    token = json.loads(session.text)["value"]
    token_header = {'vmware-api-session-id': token}
    return s

def check_cluster_readiness(vc_session, vchost, cluster_id):
    response = vc_session.get('https://'+vchost+'/api/vcenter/namespace-management/cluster-compatibility?')
    if response.ok:
        logger.debug("response text is {}".format(response.text))
        wcp_clusters = json.loads(response.text)
        if len(json.loads(response.text)) == 0:
            logger.error(CRED+"ERROR - No clusters returned from WCP Check"+ CEND)
        else:
            # If we Found clusters that are not compatible with WCP
            logger.debug(type(wcp_clusters))
            reasons = None
            for c in wcp_clusters:
                logger.debug("cluster is {}".format(c['cluster']))
                if c['cluster'] == cluster_id:
                    if c["compatible"]==True:
                        logger.info(CGRN +"SUCCESS - Cluster {} IS compatible with Workload Control Plane.".format(cluster_id) + CEND)
                    else:
                        logger.error(CRED +"ERROR - Cluster {} is NOT compatible for reasons listed below.".format(cluster_id) + CEND)
                        reasons = c["incompatibility_reasons"]
                        logger.debug(reasons)
                        for reason in reasons:
                            logger.error(CRED +"+ Reason-{}".format(reason['default_message'])+ CEND)
                    break
            return reasons   

def get_vc_time(vc_session,vc_host):
    host_times = {}
    json_response = vc_session.get('https://'+vc_host+'/rest/appliance/system/time')
    if json_response.ok:
        logger.debug("Response text is {}".format(json_response.text))
        results = json.loads(json_response.text)
        vctime = results["value"]["time"].replace(" ","")
        logger.debug(CGRN +"vCenter time is {}".format(vctime) + CEND )
        corrected_time = datetime.strptime(vctime, '%I:%M:%S%p').strftime('%H:%M:%S')
        logger.info(CGRN +"SUCCESS - vCenter 24hr time is {}".format(corrected_time) + CEND )
        host_times[vc_host]=corrected_time
    else:
        logger.error(CRED + "ERROR - Received Status Code {} ".format(json_response.status_code) + CEND) 
        host_times[vc_host]=None
    return host_times

def get_content_library(vc_session,vc_host):
    json_response = vc_session.get('https://' + vc_host + '/rest/com/vmware/content/library')
    if json_response.ok:
        results = json.loads(json_response.text)["value"]
        if len(results)== 0:
              logger.info(CRED +"ERROR - No content libraries found on vCenter" + CEND )
        else:
            for result in results:
                json_response = vc_session.get('https://' + vc_host + '/rest/com/vmware/content/library/id:' + result)
                if json_response.ok:
                    cl_library = json.loads(json_response.text)["value"]
                    logger.info(CGRN +"SUCCESS - Found Content Library named {}".format(cl_library["name"]) + CEND )
                    return cl_library["id"]
                else:
                    logger.info(CRED +"ERROR - Unable to return info about content library " + CEND )
    else:
        logger.info(CRED +"ERROR - Unable to return info about content libraries. " + CEND )
    return 0  


def get_nsx_cluster_status():    
    try:
        json_response = nsx_session.get('https://'+nsxmgr+'/api/v1/cluster/status',auth=HTTPBasicAuth(nsxuser,nsxpassword))
        logger.debug("json response is {}".format(json_response.status_code) )
        logger.debug("Response text is {}".format(json_response.text))
    except:
        return 0
    else:
        if not json_response.ok:
            logger.error(CRED+"Session creation failed, please check NSXMGR connection"+ CEND)
            return 0
        else:
            results = json.loads(json_response.text)
            if results["detailed_cluster_status"]["overall_status"] == "STABLE":
                logger.info(CGRN +"SUCCESS - NSX Manager Cluster is Healthy." + CEND)
                return 1
            else:
                logger.error(CRED +"ERROR - NSX Manager Cluster is NOT Healthy." + CEND)
                return 0


def get_nsx_cluster_id(cluster):
    json_response = nsx_session.get('https://'+nsxmgr+'/api/v1/fabric/compute-collections',auth=HTTPBasicAuth(nsxuser,nsxpassword))

    if json_response.ok:
        id = None
        results = json.loads(json_response.text)
        logger.debug("Response text is {}".format(results))
        if results["result_count"] > 0:   
            logger.info("Found Compute Clusters in NSX." )
            for result in results["results"]:
                logger.debug("Results display_name is {}".format(result["display_name"] ))
                if result["display_name"] == cluster:
                    logger.debug("cluster result is {}".format(result))
                    id = result["external_id"]
                    logger.debug("external_id is {}".format(id))
                    logger.info(CGRN +"SUCCESS - Found NSX Compute Cluster {} which matches vSphere HA Cluster.".format( result["display_name"] ) + CEND)
                    return id
                    break
            if id == None:
                logger.error(CRED+"ERROR - Compute Cluster {} no present in NSX.".format( result["display_name"] + CEND))
                
        else:
            logger.error(CRED+"ERROR - No Compute Clusters present in NSX. You need to add vCenter as Compute Manager."+ CEND)
    


def get_node_states(cluster_id):
    json_response = nsx_session.get('https://'+nsxmgr+'/api/v1/fabric/discovered-nodes',auth=HTTPBasicAuth(nsxuser,nsxpassword))
    if json_response.ok:
        results = json.loads(json_response.text)
        logger.debug("Discovered-Nodes Response text is {}".format(results))
        if results["result_count"] > 0:
            object = None
            logger.debug("Found Nodes in NSX." )
            nodes_in_cluster = []
            for result in results["results"]:
                if result["parent_compute_collection"] == cluster_id:
                    logger.info("Checking ESX Node with Display Name {} and UUID {} in Cluster {}".format(result["display_name"], result["external_id"], cluster_id))
                    nodes_in_cluster.append(result["external_id"])
                    node_props = result["origin_properties"]
                    for node in node_props:
                        if node['key']== "dasHostState":
                                if "Master" in node['value']:
                                    logger.info(CGRN +"SUCCESS - NSX Installed on ESX Node {}".format( result["display_name"] ) + CEND)
                                else:
                                    logger.error(CRED +"ERROR - NSX not initialized successfully on ESX Node {}".format( result["display_name"] ) + CEND)
                                logger.debug("NSX Install State for ESX Node {} is ={}.".format(result["display_name"], node['value']))
                        if node['key']== "powerState":
                                if "poweredOn" in node['value']:
                                    logger.info(CGRN +"SUCCESS - ESX Node {} is powered on".format( result["display_name"] ) + CEND)
                                else:
                                    logger.error(CRED +"ERROR - ESX Node {} is NOT Powered on".format( result["display_name"] ) + CEND)
                                logger.debug("Power State for ESX Node {} is ={}.".format(result["display_name"], node['value']))
                        if node['key']== "connectionState":
                                if "connected" in node['value']:
                                    logger.info(CGRN +"SUCCESS - ESX Node {} is connected to NSX Manager".format( result["display_name"] ) + CEND)
                                else:
                                    logger.error(CRED +"ERROR - ESX Node {} is NOT connected to NSX Manager".format( result["display_name"] ) + CEND)
                                logger.debug("Connection State for ESX Node {} is ={}.".format(result["display_name"], node['value']))
                        if node['key']== "inMaintenanceMode":
                                if "false" in node['value']:
                                    logger.info(CGRN +"SUCCESS - ESX Node {} is NOT in Maintenance Mode".format( result["display_name"] ) + CEND)
                                else:
                                    logger.error(CRED +"ERROR - ESX Node {} is in Maintenance Mode".format( result["display_name"] ) + CEND)
                                logger.debug("Maint Mode for ESX Node {} status is ={}.".format(result["display_name"], node['value']))
    
            logger.debug("The following nodes were found in the cluster {}".format(nodes_in_cluster))
            return nodes_in_cluster
        else:
            logger.error(CRED+"ERROR - No Compute Clusters present in NSX. You need to add vCenter as Compute Manager."+ CEND)
        return id
    else:
        logger.error(CRED+"ERROR - Session creation failed, please check NSXMGR connection"+ CEND)
        return 0


def get_edge_clusters():
    json_response = nsx_session.get('https://'+nsxmgr+'/api/v1/edge-clusters' ,auth=HTTPBasicAuth(nsxuser,nsxpassword))
    if json_response.ok:
        results = json.loads(json_response.text)
        logger.debug("Response text is {}".format(results))
        if results["result_count"] == 0:
            logger.error(CRED+"ERROR - No Edge Clusters present in NSX. An Edge Cluster is Required for WCP."+ CEND)
            return None
        else:
            logger.info(CGRN +"Assuming there is only ONE Edge Cluster for the POC" + CEND)
            #for result in results["results"]:
            edgecluster_id = results["results"][0]["id"]
            logger.info(CGRN +"SUCCESS - Found Edge Cluster with ID {}.".format(edgecluster_id) + CEND)
            return edgecluster_id

    else:
        return 0

def get_edge_cluster_state(edgecluster_id):
    readystate = ["NODE_READY","TRANSPORT_NODE_READY","success","in_sync"]
    json_response = nsx_session.get('https://'+nsxmgr+'/api/v1/edge-clusters/'+edgecluster_id+'/state' ,auth=HTTPBasicAuth(nsxuser,nsxpassword))
    if json_response.ok:
        results = json.loads(json_response.text)
        state = results["state"]
        if state not in readystate:
            logger.info(CRED +"ERROR - Edge Cluster {} found but not Ready.".format(results[edgecluster_id]) + CEND)
            return 0
        else:
            logger.info(CGRN +"SUCCESS - Edge Cluster {} is Ready.".format(edgecluster_id) + CEND)
    else:
        return 0

def get_edge_cluster_nodes(edgecluster_id):
    #logger.info(CRED +"NOTE - INSIDE THE get_edge_cluster_nodes FUNCTION." + CEND)
    edge_nodes = []
    json_response = nsx_session.get('https://'+nsxmgr+'/api/v1/edge-clusters/'+edgecluster_id ,auth=HTTPBasicAuth(nsxuser,nsxpassword))
    if json_response.ok:
        results = json.loads(json_response.text)
        members = results["members"]
        logger.debug("Edge cluster Node json_response is OK." + CEND)
        if len(members) == 0:
            logger.info(CRED +"ERROR - Edge Cluster {} has no members.".format(edgecluster_id) + CEND)
        else: 
            for member in members:
                logger.info("Found Edge Node {} in Edge Cluster {}.".format(member["transport_node_id"] ,edgecluster_id) + CEND)
                tn_node_id = member["transport_node_id"]  
                edge_nodes.append(member["transport_node_id"])   
        logger.info(CGRN + "SUCCES - Found {} edges, {} on Edge Cluster {}.".format(str(len(members)),*edge_nodes,edgecluster_id) + CEND)
        return edge_nodes
    else:
        logger.error(CRED + "ERROR - Could not establish session to NSX-T, status_code ".format(json_response.status_code) + CEND) 
        return edge_nodes

def get_edge_node_state(edge_nodes):
    logger.debug("Inside get_edge_node_state function" + CEND)
    if len(edge_nodes) == 0:
        logger.error(CRED +"ERROR - No Edges found in Edge Cluster" + CEND)
    else:
        for edge_node in edge_nodes:
            logger.info("Working on edge {}".format(edge_node) + CEND)
            json_response = nsx_session.get('https://'+nsxmgr+'/api/v1/transport-nodes/'+edge_node ,auth=HTTPBasicAuth(nsxuser,nsxpassword))
            if json_response.ok:
                results = json.loads(json_response.text)
                deployment_size = results["node_deployment_info"]["deployment_config"]["form_factor"]
                logger.debug("Edge Node json_response is {}.".format(results) + CEND)
                logger.debug("Edge Node form_factor size is \n {}".format(deployment_size) + CEND)
                if deployment_size != "LARGE":
                    logger.error(CRED +"ERROR - Edge {} is NOT Large but is currently".format(edge_node, deployment_size) + CEND)
                else: 
                    logger.info(CGRN + "SUCCESS - Edge {} size is Large. ".format(edge_node) + CEND)
            else:
                logger.error(CRED + "ERROR - Could not establish session to NSX-T, status_code ".format(json_response.status_code) + CEND) 
                return 0

def get_tier0():
    json_response = nsx_session.get('https://'+nsxmgr+'/policy/api/v1/infra/tier-0s', auth=HTTPBasicAuth(nsxuser,nsxpassword))
    if not json_response.ok:
        logger.info(CRED +"Session creation is failed, please check nsxmgr connection" + CEND)
        return 0
    else:
        results = json.loads(json_response.text)
        if results["result_count"] == 0:
            logger.info(CRED +"ERROR - No T0 routers found. Create a T0 router per documentation" + CEND)
            logger.debug (json.dumps(results,indent=2,sort_keys=True))
            return 0
        else:
            logger.info(CGRN +"SUCCESS - Found T0 Routers" + CEND)
            for result in results["results"]:
                logger.info(CGRN +"T0 router found. Name is {} ".format(result['display_name']) + CEND)
            return 1


#################################   MAIN   ################################
def main():
    logger.info("Workload Control Plane Network Type is  {} ".format(network_type))
    logger.info("Begin Testing . . . ")
    
     # Common tests to be run regardless of Networking choice
    
    # Check YAML file for missing paramters 
    logger.info("TEST 1 - Checking Required YAML inputs for program: ")
    for k, v in cfg_yaml.items():
        if v == None:
            logger.error(CRED +"ERROR - Missing required value for {}".format(k) + CEND) 
        else:
            logger.debug(CGRN +"SUCCESS - Found value, {} for key, {}".format(v,k)+ CEND) 
    
    logger.info("TEST 2 - Checking Network Communication for vCenter")
    # Check if VC is resolvable and responding
    logger.info("TEST 2a - Checking IP is Active for vCenter")
    vc_status = check_active(cfg_yaml["VC_IP"])
    logger.info("TEST 2b - Checking DNS Servers are reachable on network")
    for dns_svr in cfg_yaml["DNS_SERVERS"]:
        check_active(dns_svr)
    logger.info("TEST 2c - Checking Name Resolution for vCenter")
    checkdns(cfg_yaml["VC_HOST"], cfg_yaml["VC_IP"] )
    
    logger.info("TEST 3 - Checking VC is reachable via API using provided credentials")
    # Connect to vCenter and return VAPI content objects
    si, vc_content = vc_connect(cfg_yaml['VC_HOST'],cfg_yaml['VC_SSO_USER'],cfg_yaml['VC_SSO_PWD'] )
    
    # Check for THE DATACENTER
    logger.info("TEST4 - Checking for the  Datacenter")
    dc = get_obj(vc_content, [vim.Datacenter], cfg_yaml['VC_DATACENTER'])

    # Check for the CLUSTER
    logger.info("TEST 5 - Checking for the Cluster")
    cluster = get_cluster(dc, cfg_yaml['VC_CLUSTER'])
    cluster_id = str(cluster).split(':')[1][:-1]
    logger.debug(cluster_id)
    
    # Check Hosts in the Cluster 
    logger.info("TEST 5a - Checking Hosts in the Cluster")
    get_hosts_in_cluster(cluster)

    
    # Connect to SPBM Endpoint and existence of Storage Policies
    logger.info("TEST 6 - Checking Existence of Storage Policies")
    logger.info("TEST 6a - Checking Connection to SPBM")
    pbmSi, pbmContent = GetPbmConnection(si._stub)
    logger.info("TEST 6b - Getting Storage Policies from SPBM")
    storagepolicies = cfg_yaml['VC_STORAGEPOLICIES']
    for policy in storagepolicies:
        storage_profile= get_storageprofile(policy, pbmContent )

    # EXTRA TEST Not Necessary - Check for a Datastore 
    logger.info("TEST 7 - Not required - Checking Existence of the Datastores")
    ds = get_obj(vc_content, [vim.Datastore], cfg_yaml['VC_DATASTORE'])

    # Check for the vds 
    logger.info("TEST 8 - Checking for the vds")
    vds = get_obj(vc_content, [vim.DistributedVirtualSwitch], cfg_yaml['VDS_NAME'])

    # Create VC REST Session
    logger.info("TEST 9 - Establishing REST session to VC API")
    vc_session = connect_vc_rest(cfg_yaml['VC_HOST'],cfg_yaml['VC_SSO_USER'],cfg_yaml['VC_SSO_PWD'] )

    ## DEBUG AND TEST BELOW
    datacenter_object = vc_session.get('https://' + cfg_yaml['VC_HOST'] + '/rest/vcenter/datacenter?filter.names=' + cfg_yaml['VC_DATACENTER'])
    if len(json.loads(datacenter_object.text)["value"]) == 0:
        logger.error("ERROR - No datacenter found, please enter valid datacenter name")
    else:
        datacenter_id = json.loads(datacenter_object.text)["value"][0].get("datacenter")
        logger.error("Datacenter ID is {}".format(datacenter_id))

    # Check if Cluster is Compatible with WCP
    logger.info("TEST 10 - Checking if cluster {} is WCP Compatible".format(cluster.name))
    compatability = check_cluster_readiness(vc_session, cfg_yaml['VC_HOST'], cluster_id)
    
    # Check NTP Time settings on vCenter
    logger.info("TEST 11 - Checking time accuracy/synchronization in environment")

    # Check NTP Time settings on vCenter
    logger.info("TEST 11a - Checking time on vCenter Appliance")
    host_times = get_vc_time( vc_session, cfg_yaml['VC_HOST'])

    # Check Time settings on ESXi hosts
    logger.info("TEST 11b - Checking time on ESXi hosts")
    # First return all the ESXi hosts in the cluster
    esx_hosts = get_hosts_in_cluster(cluster)
    host_times = get_host_times(esx_hosts,host_times)

    # Detect variances in the times among all the objects ESXi and vCenter
    logger.info("TEST 11c - Checking max time deltas on ESXi and vCenter hosts is less than 30")
    detect_time_drift(host_times)
   
    # Check existent of a Content Library
    logger.info("TEST 12 - Checking for existence and configuration of Content Library")
    content_library_id = get_content_library(vc_session,cfg_yaml['VC_HOST'])

     

    ###### If networking type is vSphere  ######
    if network_type=='vsphere':
        try:
            
            logger.info("Begin vSphere Networking checks")

            # Check for the Primary Workload Network 
            logger.info("TEST 13 - Checking for the Primary Workload Network PortGroup")
            prim_wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_PRIMARY_WKLD_PG'])

            # Check for the Workload Network 
            logger.info("TEST 14 - Checking for the Workload Network PortGroup")
            wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_WKLD_PG'])
            
            # Check for the HAProxy Management IP 
            logger.info("TEST 15 - Checking HAProxy Health")
            logger.info("TEST 15a - Checking reachability of HAProxy Frontend IP")
            haproxy_status = check_active(cfg_yaml["HAPROXY_IP"])

            if haproxy_status != 1:
                # Check for the HAProxy Health
                logger.info("TEST 15b - Checking login to HAPROXY DataPlane API")
                check_health_with_auth("get",cfg_yaml["HAPROXY_IP"], str(cfg_yaml["HAPROXY_PORT"]), '/v2/services/haproxy/configuration/backends', 
                cfg_yaml["HAPROXY_USER"], cfg_yaml["HAPROXY_PW"])
            else:
                logger.info("TEST 15b - Skipping HAPROXY DataPlane API Login until IP is Active")
            
        except vmodl.MethodFault as e:
            logger.error(CRED +"Caught vmodl fault: %s" % e.msg+ CEND)
            pass
        except Exception as e:
            logger.error(CRED +"Caught exception: %s" % str(e)+ CEND)
            pass


    # If networking type is NSX-T
    if network_type == 'nsxt':
        try:
            
            logger.info("Begin NSX-T Networking checks")

            # Check for the Management VDS Port Group
            logger.info("TEST 13 - Checking for the Management VDS PortGroup")
            prim_wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_MGMT_PG'])

            # Check for the Uplink VDS PG
            logger.info("TEST 14 - Checking for the Uplink VDS PortGroup")
            wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_UPLINK_PG'])

            # Check for the Edge TEP PG
            logger.info("TEST 15 - Checking for the Edge TEP VDS PortGroup")
            wkld_pg = get_obj(vc_content, [vim.Network], cfg_yaml['VDS_EDGE_TEP_PG'])

            logger.info("TEST 16 - Checking Network Communication for NSX-T Manager Unified Appliance")
            # Check if NSX Manager is resolvable and responding
            logger.info("TEST 16a - Checking IP is Active for NSX Manager")
            nsx_status = check_active(cfg_yaml["NSX_MGR_IP"])
            logger.info("TEST 16b - Checking Name Resolution for NSX Manager")
            checkdns(cfg_yaml["NSX_MGR_HOST"], cfg_yaml["NSX_MGR_IP"] )

            # Setup NSX Manager Session Information
            global nsx_session, nsxmgr, nsxuser,nsxpassword
            nsx_session=requests.Session()
            nsx_session.verify=False
            nsxmgr=cfg_yaml["NSX_MGR_IP"]
            nsxuser=cfg_yaml["NSX_USER"]
            nsxpassword=cfg_yaml["NSX_PASSWORD"]
            
            logger.info("TEST 17 - Checking on NSX API, credentials, and Cluster Status")
            get_nsx_cluster_status()

            logger.info("TEST 18 - Checking on NSX State for all Nodes in vSphere cluster {}".format(cfg_yaml['VC_CLUSTER']))
            nsx_cluster_id = get_nsx_cluster_id(cfg_yaml['VC_CLUSTER'])
            logger.debug("nsx_cluster_id Outside of the Function is {}".format(nsx_cluster_id))
            nsx_nodes = get_node_states(nsx_cluster_id)

            logger.info("TEST 19 - Checking on NSX Edge Health")
            edgecluster_id = get_edge_clusters()
            if edgecluster_id != None:
                get_edge_cluster_state(edgecluster_id)
                logger.info("TEST 19a - Checking Edge Node Size is Large")
                edges = []
                edges = get_edge_cluster_nodes(edgecluster_id)
                logger.debug("Edges =".format( *edges))
            
            get_edge_node_state(edges) 
            
            get_tier0()


        except vmodl.MethodFault as e:
            logger.info(CRED +"\tCaught vmodl fault: %s" % e.msg+ CEND)
            pass
        except Exception as e:
            logger.info(CRED +"\tCaught exception: %s" % str(e)+ CEND)
            pass

    logger.info("************************************************")
    logger.info("** All checks were run. Validation Complete.  **")
    logger.info("************************************************")

# Start program
if __name__ == '__main__':
    main()
