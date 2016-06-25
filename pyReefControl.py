import json
import os
import time
from datetime import datetime
from pprint import pprint


def control_power(name, state):
	print("Controlling power for", name, "setting to", state)
	cmd = "curl http://" + power_switch_auth["user"] +':'+ power_switch_auth["password"] + '@' + power_switch_auth["ip"] + "/outlet?" + powermap[name]+'='+state
	print(cmd)
	os.system(cmd)
#	curl http://admin:admin01@10.10.10.10/outlet?1=OFF
	return


def find_active_event(event_list):
	retval = 255
	ctime = datetime.now().time()
	now = datetime.now().time()
	for i in range(len(schedule["schedule"])):
		start = event_list[i]["event"][0]["start"]
		end = event_list[i]["event"][0]["end"]
		start_time = now.replace(hour=int(start[0:2]), minute=int(start[3:5]), second=int(start[6:]), microsecond=0)
		end_time = now.replace(hour=int(end[0:2]), minute=int(end[3:5]), second=int(end[6:]), microsecond=0)
		print("Considering start:", start, "end:", end)
		if start_time <= ctime < end_time:
			print("Found something!", i, start, end)
			retval = i
	return retval


def implement_event(event):
	pprint(event)
	count = len(event["event"][0]["power_control"])
	for i in range(count):
		control_power(event["event"][0]["power_control"][i]["name"], event["event"][0]["power_control"][i]["state"])
		time.sleep(2)
	return


# initialize the powermap
power_switch_auth = {"user":"admin", "password":"admin01", "ip":"10.10.10.10"}
print(power_switch_auth)
powermap = {}
with open("./cfg/powermap.cfg") as f:
	for line in f:
		(key, val) = line.split()
		powermap[key] = val


# read the daily schedule
with open('./cfg/daily_schedule.json') as data_file:
    schedule = json.load(data_file)

# wait for time!

active_event = find_active_event(schedule["schedule"])
print("Index of active event:", active_event)
implement_event(schedule["schedule"][active_event]);
