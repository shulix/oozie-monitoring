#!/usr/bin/python

import subprocess
import sys
import os
import urllib2
from urllib2 import URLError
import socket
import re
import json
import time
import ConfigParser
from ConfigParser import SafeConfigParser
from pprint import pprint

def get_config_params(config_file):
  try:
    with open(config_file) as f:
      try:
        parser = SafeConfigParser()
        parser.readfp(f)
      except ConfigParser.Error, err:
        print 'Could not parse: %s Exiting', err
        sys.exit(1)
  except IOError as e:
    print "Unable to access %s. Error %s \nExiting" % (config_file, e)
    sys.exit(1)

  ams_collector_host = parser.get('ams_config', 'ams_collector_host')
  ams_collector_port = parser.get('ams_config', 'ams_collector_port')
  ams_collector_timeout = parser.get('ams_config', 'ams_collector_timeout')

  if not ams_collector_port.isdigit():
    print "Invalid port specified for AMS Collector. Exiting"
    sys.exit(1)
  if not is_valid_hostname(ams_collector_host):
    print "Invalid hostname provided for AMS collector. Exiting"
    sys.exit(1)
  if not ams_collector_timeout.isdigit():
    print "Invalid timeout value specified for AMS Collector. Using default of 3 seconds"
    ams_collector_timeout = 3

  oozie_server = parser.get('oozie_config', 'oozie_server')
  oozie_port = parser.get('oozie_config', 'oozie_port')
  oozie_server_timeout = parser.get('oozie_config', 'oozie_server_timeout')

  if not oozie_port.isdigit():
    print "Invalid port specified for Oozie Server. Exiting"
    sys.exit(1)
  if not is_valid_hostname(oozie_server):
    print "Invalid hostname provided for Oozie Server. Exiting"
    sys.exit(1)
  if not oozie_server_timeout.isdigit():
    print "Invalid timeout value specified for Oozie server. Using default of 3 seconds"
    oozie_server_timeout = 3

  # Prepare dictionary object with config variables populated
  config_dict = {}
  config_dict["ams_collector_host"] = ams_collector_host
  config_dict["ams_collector_port"] = ams_collector_port
  config_dict["ams_collector_timeout"] = ams_collector_timeout
  config_dict["oozie_server"] = oozie_server
  config_dict["oozie_port"] = oozie_port
  config_dict["oozie_server_timeout"] = oozie_server_timeout
  return config_dict

# Prepare json object for each of the Oozie metrics in format recognized by Ambari metrics
def construct_metric(key,value,hostname,timestamp):
    metrics = {}
    vals = {}
    metric_dict = {}
    metrics["hostname"] = hostname
    metrics["appid"] = "oozie"
    metrics["type"]="COUNTER"
    metrics["starttime"] = timestamp
    metrics["timestamp"] = timestamp
    metrics["metricname"] = key
    vals[timestamp] = value
    metrics["metrics"] = vals
    # Construct ambari metrics style json object to insert into AMS Collector
    metric_dict ["metrics"] = [metrics]
    metric_json=json.dumps(metric_dict, indent=4, sort_keys=True)
    return metric_json

def is_valid_hostname(hostname):
    if hostname == "":
        return False
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def test_socket(socket_host,socket_port,service_name):
  # Test socket connectivity to requested service port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      s.connect((socket_host,int(socket_port)))
    except Exception as e:
      print("Unable to connect to %s host %s:%d. Exception is %s\nExiting!" % (service_name, socket_host,int(socket_port),e))
      sys.exit(1)
    finally:
      s.close()

# Gather metrics from Oozie server
def collect_oozie_metrics(oozie_server_host,oozie_server_port,timeout):
    # Test socket connectivity to Oozie server port
    test_socket(oozie_server_host,oozie_server_port,"Oozie server")

    # Construct URL request for metrics data. This needs to be changed when moving to JMX
    url = "http://"+ str(oozie_server_host) +":" + str(int(oozie_server_port)) + "/oozie/v2/admin/metrics"
    req = urllib2.Request(url)
    data = ''
    try:
          response = urllib2.urlopen(req,timeout=timeout)
          data = json.loads(response.read())
          return data
    except (urllib2.URLError, urllib2.HTTPError) as e:
      print 'Oozie metric gathering failed with error:', e.errno

# Publishing the Metrics to Collector
def publish_metrics(metric_data,ams_collector_host,ams_collector_port,timeout):
    test_socket(ams_collector_host,ams_collector_port,"AMS Collector")

    # Submit metrics to AMS Collector
    url = "http://"+ str(ams_collector_host) +":" + str(int(ams_collector_port)) + "/ws/v1/timeline/metrics"
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    req = urllib2.Request(url, metric_data, headers)
    #print metric_data
    try:
      response = urllib2.urlopen(req,timeout=timeout)
      print "Response code was: %d" %response.getcode()
    except (urllib2.URLError, urllib2.HTTPError) as e:
      print 'Metrics submission failed with error:', e.errno

def main():

  # If config file explicitly passed, use it. Else fall back to zk_config.ini as default filename
  config_file = sys.argv[1] if len(sys.argv) >= 2 else os.path.join(os.path.dirname(__file__),"oozie_config.ini")
  config_dict = {}
  config_dict = get_config_params(config_file)
  ams_collector_timeout = float(config_dict["ams_collector_timeout"])
  oozie_server_timeout = float(config_dict["oozie_server_timeout"])
  oozie_metrics_data = collect_oozie_metrics(config_dict["oozie_server"],config_dict["oozie_port"],oozie_server_timeout)
  # Set a timestamp per iteration as time when we gather the metrics
  timestamp = int(time.time()*1000)


  for key,value in json.load(open(os.path.join(os.path.dirname(__file__),"instrumentation.json"))).items():
    i = 0
    for counter_types in value:
      if ( key == 'counters' ):
        metric_data_json = construct_metric(str(counter_types),oozie_metrics_data[key][counter_types]['count'],config_dict["oozie_server"],timestamp)
        #print "Publishing metric data for metric: ", str(counter_types)
        #print str(counter_types),oozie_metrics_data[key][counter_types]['count']
        print metric_data_json
        publish_metrics(metric_data_json,config_dict["ams_collector_host"],config_dict["ams_collector_port"],ams_collector_timeout)
      else :
        metric_data_json = construct_metric(str(counter_types),oozie_metrics_data[key][counter_types]['value'],config_dict["oozie_server"],timestamp)
        #print str(counter_types),oozie_metrics_data[key][counter_types]
        #print "Publishing metric data for metric: ", str(counter_types)
        print metric_data_json
        publish_metrics(metric_data_json,config_dict["ams_collector_host"],config_dict["ams_collector_port"],ams_collector_timeout)
    i += 1

if __name__ == "__main__":
  main()
