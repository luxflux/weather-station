import math
from gpiozero import Button
from time import sleep

ONE_KM_IN_CM = 1.0 * 100 * 1000
ONE_HOUR_IN_SECS = 1.0 * 60 * 60

RADIUS_CM = 9.0
CIRCUMFERENCE_CM = (2 * math.pi) * RADIUS_CM
MEASURE_INTERVAL = 5
ADJUSTMENT = 1.18

def spin():
    global wind_count
    wind_count = wind_count + 1

def calculate_speed(time_sec):
    global wind_count
    rotations = wind_count / 2.0 # switch is closed twice per rotation

    # Distance of one cup in cm
    dist_cm = CIRCUMFERENCE_CM * rotations
    dist_km = dist_cm / ONE_KM_IN_CM

    km_per_sec = dist_km / time_sec
    km_per_hour = km_per_sec * ONE_HOUR_IN_SECS

    return km_per_hour * 1.18


wind_speed_sensor = Button(5)
wind_speed_sensor.when_pressed = spin

while True:
    wind_count = 0
    sleep(MEASURE_INTERVAL)
    km_per_hour = calculate_speed(MEASURE_INTERVAL)

    print(format(km_per_hour, 'f'), "km/h")
