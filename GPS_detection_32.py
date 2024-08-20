import sys
import time
import network
import machine
from machine import UART
from machine import PWM, Pin
import urequests
import ujson

def do_connect(wifi, password): # Connect the ESP32 to wifi
    
    wlan = network.WLAN(network.STA_IF) # Create station surface
    wlan.active(True)
    
    if not wlan.isconnected(): # Check if already connected
        print('connecting to network...')
        wlan.connect(wifi, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

# Inialize the Pin
gps_uart = UART(2, baudrate=9600, tx=17, rx=16)  # Use UART2 as the Output Input pin
debug_uart = sys.stdout  # Use the standard output
url = 'http://*********/gps'
wifi_1 = "******"
pw1 = '******'


def set_up():
    debug_uart.write("Initiating\n")
    debug_uart.write("Waiting...\n")

def loop_data():
    while True:
        if gps_uart.any():
            gps_data = gps_uart.read()
            if gps_data:
                debug_uart.write(gps_data) #.decode('utf-8'))
                loc_data = gps_data.decode('utf-8')
                loc_check(loc_data)
        time.sleep(1) # 1 second interval between receiving signal
        
# If the signal received has correct format, LED will light on for 1 second
def loc_check(data):
    
    # Initialize the LED pin
    led = Pin(2, Pin.OUT)
    data_lines = data.strip().splitlines()
    subprotocal_1 = 'GPGSA' # GPGSA is the key signal that indicates wether we have established connection with the satellites
    for lines in data_lines:
        if subprotocal_1 in lines:
            data_parts = lines.split(',')
            if (data_parts[2] == "3" or data_parts[2] == "2"):
                print('GPS signal detected')
                led.value(1)
                time.sleep(1)
                led.value(0)
                coordinate_signal = ana_data(data)
                print('coordinate detected is:', coordinate_signal)
                send_gps(url, coordinate_signal)
            elif data_parts[2] == "1":
                print('GPS signal still not detected')
                
def ana_data(data):
    
    data_lines = data.strip().splitlines() # Split the received signal line by line for iteration
    
    for lines in data_lines:
        if 'GNGGA' in lines:
            data_parts = lines.split(',')
            latitude_signal = float(data_parts[2])
            longitude_signal = float(data_parts[4])
            
            if data_parts[3] == 'N':
                lat_indi = 'N'
                latloc = convert_to_readable_format(latitude_signal, lat_indi)
            elif data_parts[3] == 'S':
                lat_indi = 'S'
                latloc = convert_to_readable_format(latitude_signal, lat_indi)
            if data_parts[5] == 'E':
                long_indi = 'E'
                longloc = convert_to_readable_format(longitude_signal, long_indi)
            elif data_parts[5] == 'W':
                long_indi = 'W'
                longloc = convert_to_readable_format(longitude_signal, long_indi)
            
            loc_dict = {
                "lattitude": latloc,
                "longitude": longloc
            }
            
            # signal =  latloc + ", " + longloc
        
    
    return loc_dict

def convert_to_readable_format(coordinate, indi): # Convert the string data to string that has indicators for location
    
    degrees = int(coordinate // 100)
    minutes = int(coordinate % 100)
    seconds = (coordinate % 1) * 60
    readable_format = f"{degrees}{indi}. {minutes}' {seconds:.3f}''"
    
    return readable_format

def send_gps(url, data):
    
    # payload = ujson.dumps(data)
    response = urequests.post(url, json=data)

    # Check if the response is not empty
    if response:
        print("Response received from the server:")
        s = response.text
        result = unicode_escape_decode(s)
        print(result)
        # print(response.json())
    else:
        print("No response received from the server.")
        
    response.close()

def unicode_escape_decode(s):
    result = ''
    i = 0
    while i < len(s):
        if s[i:i+2] == '\\u':
            hex_value = s[i+2:i+6]
            result += chr(int(hex_value, 16))
            i += 6
        else:
            result += s[i]
            i += 1
    return result

do_connect(wifi_1, pw1)

# Initialize the set_up for receiving data
set_up()

# Enter the main loop
loop_data()