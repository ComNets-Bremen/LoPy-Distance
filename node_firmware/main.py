# Use two LoPys with PyTrack shields to collect
# a) The GPS positions
# b) The RSSI values
# and store the values to an SD card
#
# Jens Dede, <jd@comnets.uni-bremen.de>

from network import LoRa
import socket
import machine
import time
from machine import Pin
from machine import SD
import os
import gc
from machine import RTC
from machine import SD
from L76GNSS import L76GNSS
from pytrack import Pytrack
import utime
import struct
import pycom
import ubinascii


time.sleep(2)
gc.enable()

# States
STATE_NORMAL = 0        # wait for packets
STATE_TX_GPS = 1        # Store position and send LoRa package
STATE_CLEAR_SD = 3      # Format the SD card
STATE_TX_DATA = 4       # Send data from SD card to computer via USB

pycom.heartbeat(False)

# GPS module
py = Pytrack()
l76 = L76GNSS(py, timeout=30)

# initialise LoRa in LORA mode
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
# more params can also be given, like frequency, tx power and spreading factor
lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868)

nodeId = ubinascii.hexlify(lora.mac()).upper().decode('utf-8')

# Filenames on sd card

FILENAME_TX = "/sd/tx_" + str(nodeId) + "_gpsdata.csv"
print(FILENAME_TX)

FILENAME_RX = "/sd/rx_" + str(nodeId) + "_gpsdata.csv"
print(FILENAME_RX)

# create a raw LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# How long has the button been pressed?
buttonTimer = None
state = STATE_NORMAL


# Callback for push button. Perform different actions depending on the duration
# the button has been pressed

def pin_handler(arg):
    global buttonTimer
    global state

    if arg() == False:
        if not buttonTimer:
            buttonTimer = utime.ticks_ms()
    else:
        if buttonTimer:
            tickDuration = utime.ticks_ms() - buttonTimer
            buttonTimer = None
            if tickDuration < 50:
                # skip short jitters
                state = STATE_NORMAL        # Do nothing (only receive packets)
            elif tickDuration < 1000:
                state = STATE_TX_GPS        # Store the GNSS position
            elif tickDuration < 5000:
                state = STATE_TX_DATA       # Send data via USB to computer
            elif tickDuration < 15000:
                state = STATE_CLEAR_SD      # Format the SD card
            else:
                state = STATE_NORMAL


pin = Pin('P10', mode=Pin.IN, pull=Pin.PULL_UP)

pin.callback(Pin.IRQ_RISING | Pin.IRQ_FALLING, pin_handler)


# SD card stuff
sd = None

try:
    sd = SD()
    os.mount(sd, '/sd')
except:
    print("No SD card")

if sd != None:
    print("SD mounted")


# The main loop
while True:

    if state == STATE_NORMAL:
        pass
    elif state == STATE_TX_DATA:
        # Send data via USB to computer
        pycom.rgbled(0x7f7f00)
        print("TX DATA")

        try:
            f = open(FILENAME_TX, "r")
            content = f.readlines()

            print("#tx#" + str(nodeId) + "-START##")
            for line in content:
                print("#tx#"+line[:-1]+"##")
            f.close()
            print("#tx#" + str(nodeId) + "-END##")
        except:
            print("Cannot read tx file")

        try:
            f = open(FILENAME_RX, "r")
            content = f.readlines()
            print("#rx#" + str(nodeId) + "-START##")
            for line in content:
                print("#rx#" + line[:-1] + "##")
            f.close()
            print("#rx#" + str(nodeId) + "-END##")
        except:
            print("Cannot read rx file")

        print("##TRANSFER_DONE##")

        pycom.rgbled(0x000000)
        state = STATE_NORMAL

    elif state == STATE_TX_GPS:
        # Store the GPS position to flash
        pycom.rgbled(0x007f00)
        print("TX GPS")

        coord = l76.coordinates()
        txTime = utime.ticks_ms()
        if not coord[0] or not coord[1]:
            pycom.rgbled(0x7f0000)
            print("Invalid GNSS pos")
        print(coord, txTime, nodeId)

        s.setblocking(True)
        s.send(str(txTime)+"+"+nodeId)
        s.setblocking(False)

        f = open(FILENAME_TX, 'a')
        f.write(str(coord[0]) + ";" + str(coord[1]) + ";" + str(txTime) + ";" + str(nodeId) + "\n")
        f.close()
        pycom.rgbled(0x000000)
        state = STATE_NORMAL

    elif state == STATE_CLEAR_SD:
        # Clear the SD card
        pycom.rgbled(0x7f0000)
        print("CLEAR SD")

        os.fsformat("/sd")
        print("done")
        pycom.rgbled(0x000000)
        state = STATE_NORMAL

    # Check for received packets
    s.setblocking(False)
    data = s.recv(64)
    if (len(data) > 0):
        pycom.rgbled(0x7f7f7f)
        try:

            sData = data.decode("utf-8")
            sData = sData.split("+")
            coord = l76.coordinates()
            rxTime = utime.ticks_ms()

            if not coord[0] or not coord[1]:
                pycom.rgbled(0x7f7f00)
                print("Invalid GNSS pos")

            print(coord, rxTime, nodeId)
            txTime = sData[0]
            txNodeId = sData[1]

            rssi = lora.stats().rssi
            snr = lora.stats().snr

            # to SD card
            f = open(FILENAME_RX, 'a')
            f.write(str(coord[0]) + ";" + str(coord[1]) + ";" + str(rxTime) + ";" + str(nodeId) + ";" + str(txTime) +";" + str(txNodeId) + ";" + str(rssi) + ";" + str(snr) + "\n")
            f.close()
        except:
            print("Error parsing packet. Not for us?")
        pycom.rgbled(0x000000)

