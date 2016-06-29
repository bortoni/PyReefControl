import json
import os
import time
import threading
from datetime import datetime
from pprint import pprint
from flask import Flask, render_template, redirect, url_for
import multiprocessing
from multiprocessing import Value
from copy import deepcopy




############## WEB APP
app = Flask('PyReefControl')


@app.route("/")
def main_page():
	feed_text = "Stop Feeding"
	now = datetime.now()
	timeString = now.strftime("%Y-%m-%d %H:%M")
#	feeding = get_current_feed_state();
	if feeding.value == 0:
		feed_text = "Feed"
	templateData = {
      'title' : 'pyReefControl',
      'time': timeString,
      'temp': temperature.value,
      'feed': feed_text
      }
	return render_template('main.html', **templateData)

@app.route("/feed")
def feed_request():
	if feeding.value == 0:
		feeding.value = 1
		e.set()
	else:
		feeding.value = 0
		e.set()
	return redirect(url_for('main_page'))

def webapp_main(feeding, temperature):
	name = threading.currentThread().getName()
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

	# only send this if running on the pi itself
	if(print(os.path.exists("/home/pi"))):
		os.system(cmd)
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

def find_active_override():
	global overrides_list
	retval = None

	print("In find_active_override.")
	pprint(overrides_list)

	# currently supporting only the first active override
	for i in range(len(overrides_list["overrides"])):
		active = overrides_list["overrides"][i]["event"][0]["active"]
		if active == "YES":
			print("Found active override:", i)
			return i
	return retval

def set_feed_override(state):
	global overrides_list
	# currently supporting only the first active override
	for i in range(len(overrides_list["overrides"])):
		active = overrides_list["overrides"][i]["event"][0]["active"]
		name = overrides_list["overrides"][i]["event"][0]["name"]
		if name == "feed":
			overrides_list["overrides"][i]["event"][0]["active"] = state
			if state == "NO" and t.is_alive() == True:
				print("Canceling Feed Timer")
				t.cancel()
			elif state == "YES" and t.is_alive() == True:
				print("Already FEEDING")

			elif state == "YES" and t.is_alive() == False:
				print("STARTING Feed Timer")
				t.start()
			print("Set feed override to:", state)
	pprint(overrides_list)
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


def implement_event(event):
	global overrides_list

	event_copy = deepcopy(event)
	active_override = find_active_override()
	event_count = len(event_copy["event"][0]["power_control"])

	if active_override != None:
		print("Active override:", overrides_list["overrides"][active_override]["event"][0]["name"])
		count = len(overrides_list["overrides"][0]["event"][active_override]["power_control"])
		print("Overriding", count, "items")
		for i in range(count):
			name = overrides_list["overrides"][0]["event"][0]["power_control"][i]["name"]
			state = overrides_list["overrides"][0]["event"][0]["power_control"][i]["state"]
			print("Overriding", name, "to", state)
			for j in range(event_count):
				if name == event_copy["event"][0]["power_control"][j]["name"]:
					event_copy["event"][0]["power_control"][j]["state"] = state

	pprint(event_copy)

	for k in range(event_count):
		control_power(event_copy["event"][0]["power_control"][k]["name"], event_copy["event"][0]["power_control"][k]["state"])
		time.sleep(2)
	return

def feed_timer():
	print("FEED TIMER EXPIRED")
	e.set()
	return

################## SENSORS ######################
def sensor_main():
	global defaults
	name = threading.currentThread().getName()
	print(name, 'Starting')
	defaults["SENSOR_INTERVAL"]
	while True:
		print(name, 'sleeping', 60*int(defaults["SENSOR_INTERVAL"]))
		time.sleep(60*int(defaults["SENSOR_INTERVAL"]))
	print(name, 'Exiting')



################ MAIN ###################
if __name__ == "__main__":
	e = threading.Event()
	feeding = Value('i', 0) # 0 not feeding 1 feeding
	feed_timer_started = False
	temperature = Value('d', 78.0)
	defaults = {}
	powermap = {}
	schedule = {}
	overrides_list = {}

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

	sensor_thread = threading.Thread(name='sensor_main', target=sensor_main)
	webapp_thread = threading.Thread(name='webapp_main', target=webapp_main, args=(feeding, temperature))
	t = threading.Timer(60*int(defaults["FEED_DURATION"]), feed_timer)
	sensor_thread.start()
	webapp_thread.start()


	# TODO wait for system time!

	while True:
		print("Feeding Value is", feeding.value)

		if feeding.value == 1 and feed_timer_started == False :
			set_feed_override("YES")
			feed_timer_started = True

		active_event = find_active_event(schedule["schedule"])
		if active_event != None:
			print("Index of active event:", active_event)
			implement_event(schedule["schedule"][active_event]);
		else:
			print("NO ACTIVE EVENT!!")
		print("Main thread", 'sleeping', 60*int(defaults["EVENT_CHECK_INTERVAL"]))
		e.wait(timeout=2+60*int(defaults["EVENT_CHECK_INTERVAL"]))
		e.clear()

		#if the timer is off and we were feeding, turn off feeding
		if (feeding.value ==0 and feed_timer_started == True) or (t.is_alive() == False and feed_timer_started == True):
			print("TURNING OFF feeding in MAIN")
			feeding.value = 0
			set_feed_override("NO")
			t = threading.Timer(60*int(defaults["FEED_DURATION"]), feed_timer)
			feed_timer_started = False
