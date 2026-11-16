# SPDX-License-Identifier: EUPL-1.2
# MicroPython per a BBC micro:bit receptora: per ràdio a USB/sèrie.
from microbit import *
import radio

radio.on()
radio.config(group=23, power=7)

while True:
    dades = radio.receive()
    if dades:
        print(dades)
        display.show(Image.YES)
    sleep(100)
