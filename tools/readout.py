#!/usr/bin/env python3

# Read data via the serial terminal from a PyCom
#
# Jens Dede <jd@comnets.uni-bremen.de>
#

import argparse
import serial
import time

# Row headings
RX_FORMAT = ["lat", "lon", "rx_time", "rx_node_id", "tx_time", "tx_node_id", "rssi", "snr"]
TX_FORMAT = ["lat", "lon", "tx_time", "tx_node_id"]

TIMEOUT = 10.0 # secs

# Get the serial line as a command line parameter
parser = argparse.ArgumentParser(description='Read data from pycom')
parser.add_argument("port", type=str, help="The serial port")

args = parser.parse_args()

# collect the lines
rxLines = []
txLines = []

# Check for complete datasets
rxStarted = False
txStarted = False
nodeIdRx = None
nodeIdTx = None

with serial.Serial(args.port, 115200, timeout=TIMEOUT) as ser:
    while(True):
        line = ser.readline().decode("utf-8")[:-2]
        if line[:4] == "#tx#" and line.endswith("##"):
            # Handle tx data
            procline = line[4:-2]
            if procline.endswith("START"):
                nodeIdRx = procline.split("-")[0]
                txStarted = True
            elif procline.endswith("END"):
                txStarted = False
            else:
                txLines.append(procline)

        elif line[:4] == "#rx#" and line.endswith("##"):
            # Handle rx data
            procline = line[4:-2]
            if procline.endswith("START"):
                nodeIdTx = procline.split("-")[0]
                rxStarted = True
            elif procline.endswith("END"):
                rxStarted = False
            else:
                rxLines.append(procline)
        elif line.endswith("##TRANSFER_DONE##"):
            break;
        else:
            # not for us
            pass

print("Got", len(rxLines), "rx datasets")
print("Got", len(txLines), "tx datasets")
print("Node id rx:", nodeIdRx)
print("Node id tx:", nodeIdTx)

# Generic filename
timestamp = str(int(time.time()))

if nodeIdRx:
    with open(timestamp+"_rx_"+nodeIdRx+".csv", "w") as file_rx:
        file_rx.write(";".join(RX_FORMAT)+"\n")
        for data in rxLines:
            file_rx.write(data+"\n")
else:
    print("No RX data received")

if nodeIdTx:
    with open(timestamp+"_tx_"+nodeIdTx+".csv", "w") as file_tx:
        file_tx.write(";".join(TX_FORMAT)+"\n")
        for data in txLines:
            file_tx.write(data+"\n")
else:
    print("No TX data received")

print("Done")

