# LoPy-Distance
Simple distance measurement app for LoPy using the PyTrack-Shield

Using two LoPys with PyTrack shields, this app can be used to collect the
positions of both nodes as well as the signal indicators of received signals.

A script for exporting the collected data as an csv file is also included.

This code far away from being perfect, but maybe it will help someone.

## Button codes:

The LoPy can be controlled using the internal button:

- Press the button for 50 ms - 1 sec: Record the current position and send it via LoRa
- Press the button for 1 sec - 5 secs: Send the data (csv-file) via the serial line. Use the tool `readout.py` to receive and store the data.
- Press the button for 5 sec - 15 sec: Erase the SD card.

## Readout data:

- The script `readout.py` requires the module `pyserial`
- Connect the LoPy via USB and wait till it is started (max 10 sec)
- Start `readout.py` with the serial port of the LoPy as a parameter, for example `./readout.py /dev/ttyUSB0`
- Press the button for 1-5 secs.After a couple of seconds, you will find two new csv files in the directory where `readout.py` is located.

The file format is `<timestamp>_[rx|tx]_<nodeid>.csv.`

The csv files contain descriptive headers for each column

To get the distance and the signal indicators for two nodes, the files from two
nodes have to be considered: rx from node 1 corresponds to tx from node 2 and
vice versa.

## Contact

Feel free to open tickets, create pull requests or contact me directly:

jd@comnets.uni-bremen.de
