# Oozie-monitoring
Python script to pull Oozie metrics from Instrumentation output on Oozie server and insert into Ambari metrics server

Example:
```
*/opt/scripts/oozie-monitoring/oozie_metrics.py
```
OR
```
*/opt/scripts/oozie-monitoring/oozie_metrics.py oozie_config.ini
```

If successful, this will publish the metrics data into ambari metrics database (AMS HBase). Once the publishing is successful, the metrics can be viewed in Grafana as explained later.

# What you need to do with the scripts

The `oozie_config.ini` file contains the configuration for the Oozie server to connect to, and the AMS collector node details.

The `instrumentation.json` lists the parameters that are to be picked up from the instrumentation output in Oozie. For now, it supports only the gauges and counters sets of metrics.

For continous monitoring of the oozie metrics, edit the above config files as needed and place the script and the config file on any node in the cluster (prefereably the Ambari metrics collector host itself, and add a crontab entry (crontab –e) to schedule it run. 

Example: 
```
*/5 * * * * * /opt/scripts/oozie-monitoring/oozie_metrics.py
```

The above crontab will execute the script every 5 minutes and publish the metrics to AMS collector.

# Steps to create the Grafana dashboard to retrieve the custom metrics we collected.

Login to Grafana as admin.

Click on top Dashboard drop down menu -> +New

Place your cursor on Green hidden tab -> Add Panel -> Graph alt text

Fill the Metrics details

Component Name : Oozie

Metrics Name: select one from the metrics drop down menu. Eg. "jobstatus.SUCCEEDED" or "jpa.GET_PENDING_ACTIONS"

Select Aggregator as none

You can select Transform as diff or none, depending on requirement. 

You can rename the panel.

Follow the same to add more panels/graphs for each metric name.
