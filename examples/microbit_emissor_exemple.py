# SPDX-License-Identifier: EUPL-1.2
# MicroPython per a BBC micro:bit emissora (temperatura, llum, P0).
from microbit import *
import radio

radio.on()
radio.config(group=23, power=7)

while True:
    temperatura = temperature()
    llum = display.read_light_level()
    sensor = pin0.read_analog()
    radio.send("{},{},{}".format(temperatura, llum, sensor))
    display.show(Image.ARROW_E)
    sleep(5000)
