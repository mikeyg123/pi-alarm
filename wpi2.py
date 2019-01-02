#! /usr/bin/python

import wiringpi2 as wiringpi  
from time import sleep       # allows us a time delay  
wiringpi.wiringPiSetupGpio()  
wiringpi.pinMode(24, 1)      # sets GPIO 24 to output  
wiringpi.digitalWrite(24, 0) # sets port 24 to 0 (0V, off)  
  
wiringpi.pinMode(25, 0)      # sets GPIO 25 to input  
try:  
    while True:  
        if wiringpi.digitalRead(25):     # If button on GPIO25 pressed   
            wiringpi.digitalWrite(24, 1) # switch on LED. Sets port 24 to 1 (3V3, on)  
        else:  
            wiringpi.digitalWrite(24, 0) # switch off LED. Sets port 24 to 0 (0V, off)  
        sleep(0.05)                      # delay 0.05s  
  
finally:  # when you CTRL+C exit, we clean up  
    wiringpi.digitalWrite(24, 0) # sets port 24 to 0 (0V, off)  
    wiringpi.pinMode(24, 0)      # sets GPIO 24 back to input Mode  
    # GPIO 25 is already an input, so no need to change anything  

