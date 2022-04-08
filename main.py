import math
import statistics
import time
import glob
import bme280
import smbus2
from gpiozero import Button

ONE_KM_IN_CM = 1.0 * 100 * 1000
ONE_HOUR_IN_SECS = 1.0 * 60 * 60

MAIN_MEASURE_INTERVAL = 5 * 60


### Wind Speed
WIND_MEASURE_INTERVAL = 5
RADIUS_CM = 9.0
CIRCUMFERENCE_CM = (2 * math.pi) * RADIUS_CM
ADJUSTMENT = 1.18

wind_speeds = []
wind_count = 0

def wind_speed_spin():
    global wind_count
    wind_count = wind_count + 1

def wind_speed_count_reset():
    global wind_count
    wind_count = 0

def wind_speed_speeds_reset():
    global wind_speeds
    wind_speeds = []

def wind_speed_gust():
    global wind_speeds
    return max(wind_speeds)

def wind_speed_mean():
    global wind_speeds
    return statistics.mean(wind_speeds)

def wind_speed_measure():
    global wind_speeds
    final_speed = wind_speed_calculate_speed(WIND_MEASURE_INTERVAL)
    wind_speeds.append(final_speed)

def wind_speed_calculate_speed(time_sec):
    global wind_count
    rotations = wind_count / 2.0 # switch is closed twice per rotation

    # Distance of one cup in cm
    dist_cm = CIRCUMFERENCE_CM * rotations
    dist_km = dist_cm / ONE_KM_IN_CM

    km_per_sec = dist_km / time_sec
    km_per_hour = km_per_sec * ONE_HOUR_IN_SECS

    return km_per_hour * 1.18

Button(5).when_pressed = wind_speed_spin


### Wind Direction
VOLT_DEGREE_MAPPING = {
        0.4: 0.0,
        1.4: 22.5,
        1.2: 45.0,
        2.8: 67.5,
        2.7: 90.0,
        2.9: 112.5,
        2.2: 135.0,
        2.5: 157.5,
        1.8: 180.0,
        2.0: 202.5,
        0.7: 225.0,
        0.8: 247.5,
        0.1: 270.0,
        0.3: 292.5,
        0.2: 315.0,
        0.6: 337.5,
        }

wind_directions = []
adc = MCP3008(channel=0)

def wind_direction_get_average(angles):
    sin_sum = 0.0
    cos_sum = 0.0

    for angle in angles:
        r = math.radians(angle)
        sin_sum += math.sin(r)
        cos_sum += math.cos(r)

    flen = float(len(angles))
    s = sin_sum / flen
    c = cos_sum / flen
    arc = math.degrees(math.atan(s / c))
    average = 0.0

    if s > 0 and c > 0:
        average = arc
    elif c < 0:
        average = arc + 180
    elif s < 0 and c > 0:
        average = arc + 360

    return 0.0 if average == 360 else average

def wind_direction_measure():
    adc_value = round(adc.value * 3.3, 1)
    if adc_value in VOLT_DEGREE_MAPPING:
        wind_directions.append(VOLT_DEGREE_MAPPING[adc_value])
    else:
        print("Could not determine wind direction for ADC reading: %s" % adc_value)

def wind_direction_reset():
    global wind_directions
    wind_directions = []

def wind_direction():
    global wind_directions
    return wind_direction_get_average(wind_directions)


### Wind Direction
RAINFALL_BUCKET_SIZE = 0.2794
rainfall_tip_count = 0

def rainfall_bucket_tipped():
    global rainfall_tip_count
    rainfall_tip_count = rainfall_tip_count + 1

def rainfall_reset():
    global rainfall_tip_count
    rainfall_tip_count = 0

def rainfall():
    global rainfall_tip_count
    global RAINFALL_BUCKET_SIZE
    return rainfall_tip_count * RAINFALL_BUCKET_SIZE

Button(6).when_pressed = rainfall_bucket_tipped


### Humidity, Air Pressure
HAP_PORT = 1
HAP_ADDRESS = 0x77
HAP_BUS = smbus2.SMBus(HAP_PORT)
bme280.load_calibration_params(HAP_BUS, HAP_ADDRESS)

def hap_measure():
    bme280_data = bme280.sample(HAP_BUS, HAP_ADDRESS)
    humidity  = bme280_data.humidity
    pressure  = bme280_data.pressure
    temperature = bme280_data.temperature
    return humidity, pressure, temperature


### Ground Temperature
GT_DEVICE_FILE = glob.glob("/sys/bus/w1/devices/28*")[0] + "/w1_slave"
def gt_read_temp_raw():
    global GT_DEVICE_FILE
    f = open(GT_DEVICE_FILE, "r")
    lines = f.readlines()
    f.close()
    return lines

def gt_crc_check(lines):
    return lines[0].strip()[-3:] == "YES"

def gt_measure():
    temp = -255
    attempts = 0
    success = False

    while not success and attempts < 4:
        lines = gt_read_temp_raw()
        success = gt_crc_check(lines)
        attempts += 1
        time.sleep(.2)

    if success:
        temp_line = lines[1]
        equal_pos = temp_line.find("t=")
        if equal_pos != -1:
            temp_string = temp_line[equal_pos+2:]
            temp = float(temp_string)/1000.0

    return temp


### Main Loop
while True:
    start_time = time.time()
    while time.time() - start_time <= MAIN_MEASURE_INTERVAL:
        wind_start_time = time.time()
        wind_speed_count_reset()

        while time.time() - wind_start_time <= WIND_MEASURE_INTERVAL:
            wind_direction_measure()

        wind_speed_measure(WIND_MEASURE_INTERVAL)

    humidity, pressure, ambient_temperature = hap_measure()
    ground_temperature = gt_measure()

    print("Speed: ", wind_speed_mean(), "km/h")
    print("Gust: ", wind_speed_gust(), "km/h")
    print("Direction: ", wind_direction(), "km/h")
    print("Rainfall: ", rainfall(), "mm")
    print("Humidity: ", humidity, '%')
    print("Pressure: ", pressure)
    print("Ambient Temperature: ", ambient_temperature, '℃')
    print("Ground Temperature: ", ground_temperature, '℃')

    wind_speed_count_reset()
    wind_speed_speeds_reset()
    wind_direction_reset()
    rainfall_reset()
