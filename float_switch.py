
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

GPIO.setup(18, GPIO.IN)

while True:
    if(False == GPIO.input(18)):
        print("Flooding!")
        
    time.sleep(5)    
    print("awake")
