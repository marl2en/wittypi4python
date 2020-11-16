# wittypi4python
a translation of the original software to a python library

Here we´ve got a python library for WittyPi Mini pretty much the same as the bash script library from the development team, but now it is easier to read/adjust sensor output/settings directly from python. 
WittyPi Mini is a RTC power management for Raspberry Pi (RPi). Most important it can start/shutdown RPi gracefully at specified times or battery voltage. 
This is very useful while running RPi powered by a battery. 
For a practical use of this library for a solar-powered RPi Monitor Station you can visit: 
http://www.uugear.com/product/wittypi-mini/

 # Requirement:
    • RPi
    • WittyPi Mini 
    • Python libraries: pip3 install smbus2

This software is a quick and dirty approach to get a python interface for WittyPi. The code can be rewritten in a nice python class. 
Tested on RPi 3 (Raspian) and WittyPi mini (version 3.11).
Use this software at your own risk. 


# Install:
- Follow the installation tutorial described by UUGEAR. 
- You should be able to access wittypi with the bash scripts at /home/pi/wittypi
- Copy  "wittypi.py" to your wittypi folder at RPi. 

# How to use:
- sudo python3 
- import sys
- sys.path.append("/home/pi/wittypi")
- from wittypi import *

# Examples:

- input_voltage = get_input_voltage()

Have a nice day. 
