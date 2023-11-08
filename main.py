##SALVAR O ARQUIVO COMO 'main.py' PARA SE INICIAR SOZINHO

##libraries
import network
import time
import os
import machine
from machine import Pin
from machine import I2C, Pin
import time
from bmp280 import *
from mpu9250 import MPU9250
from bmp180 import BMP180
import CCS811
from machine import RTC
from machine import ADC
import math
import urequests
from machine import UART
import gc
import ujson
# Enable the garbage collector
gc.enable()


##Inicia UART
uart1 = UART(1, 9600)
uart1 = UART(1, baudrate=9600, tx=17, rx=16)



rede_wifi = "REDE"
senha_wifi = "senha"
servidor_url = "url"

##Define variaveis
log_number = None
atm_pressure = None
temperature_reading = None
co2 = None
gyro_data = None
aceleration_data = None
battery = None
uv = None
altitude = None
cam = None
cam_status = None
battery_percentage = None
http_data = None
HTTP_request = None
file_data = None
file_name = None
arquivo = None

##Inicia sensores
def sht20_temperature():
	i2c.writeto(0x40,b'\xf3')
	time.sleep_ms(70)
	t=i2c.readfrom(0x40, 2)
	return -46.86+175.72*(t[0]*256+t[1])/65535

def sht20_humidity():
	i2c.writeto(0x40,b'\xf5')
	time.sleep_ms(70)
	t=i2c.readfrom(0x40, 2)
	return -6+125*(t[0]*256+t[1])/65535

sta_if = network.WLAN(network.STA_IF)

sta_if.active(True)


adc35=ADC(Pin(35))
adc35.atten(ADC.ATTN_11DB)
adc35.width(ADC.WIDTH_12BIT)


##Inicia setup (wifi, SD e sensores)
print('hello world, starting setup')
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.scan()
#mudar antes de rodar
sta_if.connect(rede_wifi,senha_wifi)
print("Waiting for Wifi connection")
while not sta_if.isconnected(): time.sleep(1)
print("Connected")
sdcard=machine.SDCard(slot=2, width=1, cd=None, wp=None, sck=Pin(18), miso=Pin(19), mosi=Pin(23), cs=Pin(15), freq=20000000)
os.mount(sdcard, '/sd')
time.sleep(1)
i2c=I2C(scl=Pin(22), sda=Pin(21))
bus=I2C(scl=Pin(22), sda=Pin(21))
bmp280 = BMP280(bus)
bmp280.use_case(BMP280_CASE_WEATHER)
bmp280.oversample(BMP280_OS_HIGH)
i2c=I2C(scl=Pin(22), sda=Pin(21))
mpu9250s = MPU9250(i2c)
bus=I2C(scl=Pin(5), sda=Pin(4), freq=100000)
bmp180 = BMP180(bus)
bmp180.oversample_sett = 2
bmp180.baseline = 101325

bus=I2C(scl=Pin(22), sda=Pin(21))
sCCS811 = CCS811.CCS811(i2c=bus, addr=90)

print('end of setup')
print(sta_if.ifconfig())
log_number = 1

def send_data_in_chunks(url, data):
    chunk_size = 1024  # Adjust the chunk size based on available memory
    data_str = ujson.dumps(data)
    try:
        i = 0
        while i < len(data_str):
            chunk = data_str[i:i + chunk_size]
            HTTP_request = urequests.post(url, data=chunk)
            i += len(chunk)
    except MemoryError:
        print("Error: Not enough memory")
    except OSError as e:
        print("Unexpected OSError:", e)

# Main loop
while True:
    print('log number' + str(log_number))

    ##medidas dos sensores
    bmp280.normal_measure()
    atm_pressure = (bmp280.pressure) / 101325
    temperature_reading = bmp280.temperature
    co2 = sCCS811.eCO2
    gyro_data = 'gyro rate:' + str(mpu9250s.gyro)
    aceleration_data = 'accerelation rate:' + str(mpu9250s.acceleration)
    battery = adc35.read()
    altitude = bmp180.altitude

    ##le os dados da camera
    cam = uart1.read(3200)
    if cam == None:
      cam_status = 0
    else:
      cam_status = 1

    #converte bateria pra %
    battery_percentage = round((battery * 100) / 2600)
    # Construct JSON data
    http_data = {
        "equipe": 123,
        "bateria": battery_percentage,
        "temperatura": temperature_reading,
        "pressao": atm_pressure,
        "giroscopio": gyro_data,
        "acelerometro": aceleration_data,
        "payload": {
            "dados climatologicos": {
                "altitude": altitude,
                "co2": co2
            },
            "cam_status": cam_status
        }
    }
    time.sleep(1)

   # Try to send data via POST request, handle memory errors
    send_data_in_chunks(servidor_url, http_data)

    # Combine data for the SD card and write to a file
    file_data = '{{"http_data":{}, "cam_data":{}}}'.format(http_data, cam)
    file_name = '/sd/log_vac_test{}.csv'.format(log_number)
    with open(file_name, 'bw') as arquivo:
        arquivo.write(file_data)
    arquivo.close()
    print('Recorder on SD')
    print(http_data)

    # Send data via UART
    uart1.write(str(http_data))
    log_number += 1
    print('End of transmission\n')

    # Wait for the specified time
    time.sleep(180)
