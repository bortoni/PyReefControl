import json
import os
import time
from datetime import datetime
from pprint import pprint
from flask import Flask, render_template
import multiprocessing



########### GLOBALS #########
defaults = {}
powermap = {}
schedule = {}
overrides_list = {}
temperature = 78.0

############## WEB APP
app = Flask('PyReefControl')


@app.route("/")
def main_page():
	feed_text = "Stop Feeding"
	now = datetime.now()
	timeString = now.strftime("%Y-%m-%d %H:%M")
	feeding = get_current_feed_state();
	if feeding == "NO":
		feed_text = "Feed"
	templateData = {
      'title' : 'pyReefControl',
      'time': timeString,
      'temp': temperature,
      'feed': feed_text
      }
	return render_template('main.html', **templateData)

@app.route("/feed")
def feed_request():
	feeding = get_current_feed_state();
	if feeding == "NO":
		set_feed_override("YES")
	else:
		set_feed_override("NO")
	return main_page()

def webapp_main():
	name = multiprocessing.current_process().name
	print(name, 'Starting')
	app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)
	print(name, 'Exiting')


########################### EVENT & POWER

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

def set_feed_override(state):
	# currently supporting only the first active override
	for i in range(len(overrides_list["overrides"])):
		active = overrides_list["overrides"][i]["event"][0]["active"]
		name = overrides_list["overrides"][i]["event"][0]["name"]
		if name == "feed":
			overrides_list["overrides"][i]["event"][0]["active"] = state
			print("Set feed override to:", state)
	return

def get_current_feed_state():
	# currently supporting only the first active override
	for i in range(len(overrides_list["overrides"])):
		active = overrides_list["overrides"][i]["event"][0]["active"]
		name = overrides_list["overrides"][i]["event"][0]["name"]
		if name == "feed":
			print("Current Feed State is:", active)
			return active
	return "NO"


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

	print("range is:", range(event_count))
	for k in range(event_count):
		control_power(event_copy["event"][0]["power_control"][k]["name"], event_copy["event"][0]["power_control"][k]["state"])
		time.sleep(2)
	return

################## SENSORS ######################
def sensor_main():
    name = multiprocessing.current_process().name
    print(name, 'Starting')
    defaults["SENSOR_INTERVAL"]
    while True:
    	print(name, 'sleeping', 60*int(defaults["SENSOR_INTERVAL"]))
    	time.sleep(60*int(defaults["SENSOR_INTERVAL"]))
    print(name, 'Exiting')




################ MAIN ###################

if __name__ == "__main__":
	# read defaults config

	with open("./cfg/defaults.cfg") as f:
		for line in f:
			(key, val) = line.split()
			defaults[key] = val

	# initialize the powermap
	with open("./cfg/powermap.cfg") as f:
		for line in f:
			(key, val) = line.split()
			powermap[key] = val

	# read the daily schedule
	with open('./cfg/daily_schedule.json') as data_file:
		schedule = json.load(data_file)

	with open('./cfg/overrides.json') as data_file:
		overrides_list = json.load(data_file)

	sensor_thread = multiprocessing.Process(name='sensor_main', target=sensor_main)
	webapp_thread = multiprocessing.Process(name='webapp_main', target=webapp_main)
	sensor_thread.start()
	webapp_thread.start()


	# TODO wait for time!

	while True:
		active_event = find_active_event(schedule["schedule"])
		if active_event != None:
			print("Index of active event:", active_event)
			implement_event(schedule["schedule"][active_event], overrides_list);
		else:
			print("NO ACTIVE EVENT!!")
		print("Main thread", 'sleeping', 60*int(defaults["EVENT_CHECK_INTERVAL"])+7)
		time.sleep(60*int(defaults["EVENT_CHECK_INTERVAL"]))
