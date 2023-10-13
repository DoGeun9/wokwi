from machine import Pin, RTC, SoftI2C, Timer
import ds1307
import ssd1306
import dht
import base64
import framebuf
import time
from tm1637 import TM1637
from i2c_lcd import I2cLcd

ci2c = SoftI2C(sda=Pin(13), scl=Pin(12))
rtc = ds1307.DS1307(ci2c)
tm_display = TM1637(clk=Pin(27), dio=Pin(14))
i2c = SoftI2C(sda=Pin(19), scl=Pin(18), freq=100000)
oi2c = SoftI2C(sda=Pin(4), scl=Pin(2))
dht_sensor = dht.DHT22(Pin(15))

# Get I2C address
print(i2c.scan())
address = i2c.scan()[0]

# Defining I2C LCD Objects
i2c_lcd = I2cLcd(i2c, address, 2, 16)

oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, oi2c)

button_up = Pin(23, Pin.IN, Pin.PULL_UP)
button_down = Pin(22, Pin.IN, Pin.PULL_UP)
btn = Pin(21, Pin.IN, Pin.PULL_UP)

state_of_btn = 0
def btn_click(btn_on):
    global state_of_btn
    state_of_btn = not state_of_btn

btn.irq(btn_click, Pin.IRQ_FALLING)

menu_items = ['RTC Timer', 'DHT22']

# img resizer: https://imageresizer.com/
# img to base64: https://gurgleapps.com/tools/image-to-code
wokwi_base64 = """gCYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADwAAAAAAAAAAAAAYAAAAwB+AAAAAAAAAAAAAPAAYA/Af
wH/ADgDDgAwAPH4AfAPwOcH/4A4B48AOAHxnAP4HOB3D//AOA8PAHgB45wDuBzgfh+B4DgfBwB8AcH8A5gPwHwe
AOA4PgeA/APB+AP4D8B4PADwOHwHgPwDwHAB+AfAcHgAcDj4A4D8A4AAAPABwHB4AHA48AOB/AeA4AB4AcDgcABwOeAD
wfwHAOAAOADg4PAAcD/AA8HcBwHAADgA4MDgAHB/gAHD3g8BwAAYAOHA4ABwdwABw84OAcAAHAHxwOAAcGcAAeOODgHAAB
wD84DgAHB3AADnjhwBwAAOB/OA4ABwfwAA544cAcAADg87gOAAcH+AAOcPPAPAAA4ePwDgAPB/wADvBzgDwAAHOD8A8ADge+AA/
gc4A8AAB/g/APAB4HnwAH4HcAPAAAfwPwB4A8B4/AB+B/ADwAAP4HOAfAfAeH4AfAfwA8AAD+BzgD+fgHgfgHwH4APAAA7gPwAf
/wB4D4A8A+ADwAAP4D8AB/4AeAeAPAPAA8AAD8AcAAHwADAAABgDwAPAAAeAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="""

def custom_to_buff(data):
    data = bytearray(base64.b64decode(data))
    width = data[0]
    height = data[1]
    fbuff = framebuf.FrameBuffer(data[2:],width,height, framebuf.MONO_HLSB)
    return fbuff

def show_image(image):
    oled.blit(image, 0, 20)
    oled.show()

wokwi_img = custom_to_buff(wokwi_base64)

def display_menu(index):
    oled.fill(0)
    oled.text('Menu', 0, 0)
    oled.text('-' * 20, 0, 10)
    for i in range(len(menu_items)):
        if i == index:
            oled.text('> ' + menu_items[i], 0, 20 + i * 10)
        else:
            oled.text(menu_items[i], 0, 20 + i * 10)
    oled.show()

weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def RTC_run(timer):
    print(rtc.datetime())
    date_time = rtc.datetime()
    oled.fill(0)
    formatted_date = "{:04d}-{:02d}-{:02d}".format(date_time[0], date_time[1], date_time[2])
    formatted_time = "{:02d}:{:02d}:{:02d}".format(date_time[4], date_time[5], date_time[6])
    day_of_week = weekday[date_time[3] - 1]
    oled.text(formatted_date + '   ' + day_of_week, 0, 0)
    oled.text(formatted_time, 0, 10)
    tm_display.numbers(date_time[5], date_time[6])

def main():
    current_item = 0
    display_menu(current_item)
    count = 0
    while True:
        if state_of_btn == True:
            time.sleep(0.1)
            dht_sensor.measure()
            # Get Celsius Temperature
            temp_c = dht_sensor.temperature()
            # Get Fahrenheit temperature
            temp_f = temp_c * (9/5) + 32.0
            hum = dht_sensor.humidity()
            if current_item == 0:
                count = 1
                timer = Timer(0)
                timer.init(period=500, mode=Timer.PERIODIC, callback=RTC_run)
                show_image(wokwi_img)
                i2c_lcd.clear()
            elif current_item == 1:
                count = 2
                tm_display.show('0000')
                oled.fill(0)
                oled.text('Temp: ' + str(temp_c) + ' C  ', 0, 0)
                oled.text('Hum: ' + str(hum) + ' %  ', 0, 10)
                oled.show()
                i2c_lcd.putstr('Temp: ' + str(temp_c) + ' C  \n')
                i2c_lcd.putstr('Hum: ' + str(hum) + ' %  \n')
        elif (button_up.value() == 0 or count == 1):
            if count == 1:
                timer.deinit()
            count = 0
            current_item = 0
            display_menu(current_item)
            tm_display.show('    ')
            i2c_lcd.clear()
            time.sleep(0.1)
        elif (button_down.value() == 0 or count == 2):
            count = 0
            current_item = 1
            display_menu(current_item)
            tm_display.show('    ')
            i2c_lcd.clear()
            time.sleep(0.1)

if __name__ == '__main__':
    main()
