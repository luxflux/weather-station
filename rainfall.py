import time
from gpiozero import Button

MM_PER_TIP = 0.2794

tip_count = 0

def bucket_tipped():
    global tip_count
    tip_count = tip_count + 1

def reset_rainfall():
    global rainfall
    rainfall = 0

wind_speed_sensor = Button(6)
wind_speed_sensor.when_pressed = bucket_tipped

while True:
    print(tip_count * MM_PER_TIP, 'mm')
    time.sleep(5)
