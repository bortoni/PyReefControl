import json
import os
import time
from datetime import datetime
from pprint import pprint
import multiprocessing


def control_power(name, state):
	print("Controlling power for", name, "setting to", state)
	user = defaults["SWITCH_USER"]
	password = defaults["SWITCH_PASS"]
	ip = defaults["SWITCH_IP"]
	cmd = "curl http://" + user +':'+ password + '@' + ip + "/outlet?" + powermap[name]+'='+state
	print(cmd)
#	os.system(cmd)
#	curl http://admin:admin01@10.10.10.10/outlet?1=OFF
	return


def find_active_event(event_list):
	retval = None
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

def find_active_override(overrides):
	retval = None

	# currently supporting only the first active override
	for i in range(len(overrides["overrides"])):
		active = overrides["overrides"][i]["event"][0]["active"]
		if active == "YES":
			print("Found active override:", i)
			return i
	return retval


def implement_event(event, overrides):
	event_copy = event
	active_override = find_active_override(overrides)
	event_count = len(event["event"][0]["power_control"])

	pprint(event)
	if active_override != None:
		print("Active override:",overrides["overrides"][active_override]["event"][0]["name"])
		count = len(overrides["overrides"][0]["event"][active_override]["power_control"])
		print("Overriding", count, "items")
		for i in range(count):
			name = overrides["overrides"][0]["event"][0]["power_control"][i]["name"]
			state = overrides["overrides"][0]["event"][0]["power_control"][i]["state"]
			print("Overriding", name, "to", state)
			for j in range(event_count):
				if name == event_copy["event"][0]["power_control"][j]["name"]:
					event_copy["event"][0]["power_control"][j]["state"] = state

	pprint(event_copy)

	for i in range(event_count):
		control_power(event_copy["event"][0]["power_control"][i]["name"], event_copy["event"][0]["power_control"][i]["state"])
		time.sleep(2)
	return

def sensor_main():
    name = multiprocessing.current_process().name
    print(name, 'Starting')
    time.sleep(2)
    print(name, 'Exiting')

if __name__ == "__main__":
	# read defaults config
	defaults = {}
	with open("./cfg/defaults.cfg") as f:
		for line in f:
			(key, val) = line.split()
			defaults[key] = val

	# initialize the powermap
	powermap = {}
	with open("./cfg/powermap.cfg") as f:
		for line in f:
			(key, val) = line.split()
			powermap[key] = val

	sensor_thread = multiprocessing.Process(name='sensor_main', target=sensor_main)
	sensor_thread.start()

	# read the daily schedule
	with open('./cfg/daily_schedule.json') as data_file:
		schedule = json.load(data_file)

	with open('./cfg/overrides.json') as data_file:
		overrides = json.load(data_file)

	# TODO wait for time!

	active_event = find_active_event(schedule["schedule"])
	if active_event != None:
		print("Index of active event:", active_event)
		implement_event(schedule["schedule"][active_event], overrides);
	else:
		print("NO ACTIVE EVENT!!")
