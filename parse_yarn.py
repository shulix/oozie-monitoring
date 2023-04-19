# This is the script to get the list of applications which are running for more than N hours in Tez Hive Yarn as Application
# Import the required packages & Store the ResourceManager Data of the running Apps using the URL as JSON
import json, urllib.request, time
rm=”http://10.XXX.Z.YY:8088/ws/v1/cluster/apps?states=RUNNING"
# Set the threshold as required (1.5h or 2.5h or 5h)
# Setting the threshold. In RM, time duration is measured in milliseconds
threshold=18000000
# Given 5 hour as threshold. You can change it as per requirements.

# Calling the RM api and storing the data in json. Added the decode('utf8') as python requires it for versions below 3.6
# You can check the results by entering the variable data in the python idle.
with urllib.request.urlopen(rm) as response:
data=json.loads(response.read().decode('utf8'))

#print (“Please find the list of long running jobs.”)
# The json has a dictionary key 'apps' which has applications as values (which are again nested key value pairs).
# Now we're iterating through the each app and check whether app's elapsed time is more than our threshold (5 hour).
# If it's running for more than an hour, the app details will be printed.

open('/home/zubair.ahmed/YARN_long_running/check_long_yarn_jobs.txt', “w”).close()

# Check if the file has any data (if yes; proceed; else print “No Job Running”)
# Traverse through all the applications running using the dictionary data; for the condition of elapsed time greater than the threshold, capture the application information (Started time, Application name, Application ID)
# Write the above data in a file for each application satisfying the condition.
# Close the file for writing and print the file (check_long_yarn_jobs.txt) contents on stdout.
res = not bool(data['apps'])

if res == True:
print (“No Jobs Running”)
else:
print (“Jobs Running”)
for running_apps in data['apps']['app']:
if running_apps['elapsedTime']>threshold:
with open('/home/zubair.ahmed/YARN_long_running/check_long_yarn_jobs.txt', 'a') as f:
f.write('\n')
# f.write(“******Long Yarn Jobs Over threshold Hours Please Investigate****** \n”)
print (“\nstartedTime: {}”.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(running_apps['startedTime']/1000))),file=f)
# print (“finishedTime: {}”.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(running_apps['finishedTime']/1000))),file=f)
print (“App Name: {}”.format(running_apps['name']),file=f)
print (“Application id: {}”.format(running_apps['id']),file=f)
# print ('Running Containers: {}'.format(running_apps['runningContainers']),file=f)
# print (“CPU Vcores: {}”.format(running_apps['allocatedVCores']),file=f)
# print (“Allocated MB: {}”.format(running_apps['allocatedMB']),file=f)
# print (“Total elapsed time: {} hours”.format(round(float(running_apps['elapsedTime']/1000/60/60),2)),file=f)
# time_hours=float(round(float(running_apps['elapsedTime']/1000/60/60),2))

file_read = open(“/home/zubair.ahmed/YARN_long_running/check_long_yarn_jobs.txt”, “r”).read()
print(file_read)