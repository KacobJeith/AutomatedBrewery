#!/usr/bin/python -tt

'''
    Python driver for [MAX38865PMB1 RTD-to-digital converter] (https://datasheets.maximintegrated.com/en/ds/MAX31865PMB1.pdf)
   
    Requires:
     - The [GPIO Library](https://code.google.com/p/raspberry-gpio-python/) (Already on most Raspberry Pi OS builds)
     - A [Raspberry Pi](http://www.raspberrypi.org/)
   
    Author:
    Alexey B. Tikhomirov 

    Version:
    1.0, 05-Jan-2016
    Comments: Adopted from https://github.com/Tuckie/max31855
              Additionally edited by Justin Kahn for use in AutomatedBrewery
'''

__author__ = 'Alexey Tikhomirov'
__copyright__ = 'Copyright 2016, Alexey Tikhomirov'
__credits__ = ['']
__license__ = 'GPL'
__version__ = '1.0'
__date__  = '05-Jan-2016'
__maintainer__ = 'Alexey Tikhomirov'
__status__ = 'Production'

#import RPi.GPIO as GPIO
from EmulatorGUI import GPIO
import time

class MAX31865(object):
    @property
    def temp(self):
        return self.get_temp()
    

    def __init__(self, cs_pin, clock_pin, data_in_pin, data_out_pin, address=int(0x80), data=int(0xc2), units = "f", board = GPIO.BCM):

        '''Initialize Soft (Bitbang) SPI bus
        Parameters:
        - cs_pin:    Chip Select (CS) / Slave Select (SS) pin (Any GPIO)  
        - clock_pin: Clock (SCLK / SCK) pin (Any GPIO)
        - data_in_pin:  Data input (SO / MOSI) pin (Any GPIO)
         - data_out_pin: Data output (MISO) pin (Any GPIO)
        - units:     (optional) unit of measurement to return. ("c" (default) | "k" | "f")
        - board:     (optional) pin numbering method as per RPi.GPIO library (GPIO.BCM (default) | GPIO.BOARD)
        '''

        self.cs_pin = cs_pin
        self.clock_pin = clock_pin
        self.data_in_pin = data_in_pin
        self.data_out_pin = data_out_pin
        self.address = address           # address of the register to write/read
        #self.data = data                # data to write/read
        self.units = units
        self.data = data
        self.board = board

        # Initialize needed GPIO
        GPIO.setmode(self.board)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.data_in_pin, GPIO.IN)
        GPIO.setup(self.data_out_pin, GPIO.OUT)

        # Pull chip select high to make chip inactive
        GPIO.output(self.cs_pin, GPIO.HIGH)
        
    def get_data(self):
        '''Acqures raw RDT data.'''
        self.address = int(0x01)    #RTD MSBs
        MSB = self.read()
        self.address = int(0x02)    #RTD LSBs
        LSB = self.read()
        #print MSB
        #print LSB
        MSB = MSB<<8 
        raw = MSB+LSB
        #print raw
        #fault = raw & 1
        #print fault
        raw = raw>>1
        #print raw      
        #print self
        #self.checkErrors()        
        return raw

    def write(self):
        '''Writes 8 bit of data to the 8 bit address'''
        GPIO.output(self.cs_pin, GPIO.LOW)
        GPIO.output(self.clock_pin, GPIO.LOW)
         
        # Write to address 
        for i in range(8):        
            #print address, data
            bit  = self.address>>(7 - i)
            bit = bit & 1 
            #GPIO.output(self.clock_pin, GPIO.LOW)
            GPIO.output(self.data_out_pin, bit)
            #if bit:
            #    GPIO.output(self.data_out_pin, GPIO.HIGH)
            #else:
            #    GPIO.output(self.data_out_pin, GPIO.LOW)
            GPIO.output(self.clock_pin, GPIO.HIGH)            
            GPIO.output(self.clock_pin, GPIO.LOW)
                
        for i in range(8):        
            bit  = self.data>>(7 - i)
            bit = bit & 1 
            #GPIO.output(self.clock_pin, GPIO.LOW)
            GPIO.output(self.data_out_pin, bit)
            #if bit:
            #    GPIO.output(self.data_out_pin, GPIO.HIGH)
            #else:
            #    GPIO.output(self.data_out_pin, GPIO.LOW)
            GPIO.output(self.clock_pin, GPIO.HIGH)
            GPIO.output(self.clock_pin, GPIO.LOW)
            #GPIO.output(self.data_out_pin, GPIO.LOW)
        
        GPIO.output(self.clock_pin, GPIO.HIGH)                      
        # Unselect the chip
        GPIO.output(self.cs_pin, GPIO.HIGH)
        

    def read(self):
        '''Reads 16 bits of the SPI bus from a self.address register & stores as an integer in self.data.'''
        bytesin = 0                
        
        # Select the chip
        GPIO.output(self.cs_pin, GPIO.LOW)
        # Assert clock bit
        GPIO.output(self.clock_pin, GPIO.LOW)
         
        # Write to address 
        for i in range(8):        
            #print address, data
            bit  = self.address>>(7 - i)
            bit = bit & 1 
            #GPIO.output(self.clock_pin, GPIO.LOW)
            GPIO.output(self.data_out_pin, bit)
            #if bit:
            #    GPIO.output(self.data_out_pin, GPIO.HIGH)
            #else:
            #    GPIO.output(self.data_out_pin, GPIO.LOW)
            GPIO.output(self.clock_pin, GPIO.HIGH)
            GPIO.output(self.clock_pin, GPIO.LOW)
            #GPIO.output(self.data_out_pin, GPIO.LOW)
        
        # Read in 8 bits        
        for i in range(8):
            GPIO.output(self.clock_pin, GPIO.HIGH)
            bytesin = bytesin << 1
            if (GPIO.input(self.data_in_pin)):
                bytesin = bytesin | 1
            GPIO.output(self.clock_pin, GPIO.LOW)
        
        # Dsable clock                
        GPIO.output(self.clock_pin, GPIO.HIGH)
        # Unselect the chip
        GPIO.output(self.cs_pin, GPIO.HIGH)
        
        # Save data
        self.data = bytesin
        #print bytesin
        return self.data

    def checkErrors(self, data_32 = None):
    # Not finished yet
        '''Checks error bits to see if there are any SCV, SCG, or OC faults'''
        if data_32 is None:
            data_32 = self.data
        anyErrors = (data_32 & 0x10000) != 0    # Fault bit, D16
        noConnection = (data_32 & 1) != 0       # OC bit, D0
        shortToGround = (data_32 & 2) != 0      # SCG bit, D1
        shortToVCC = (data_32 & 4) != 0         # SCV bit, D2
        if anyErrors:
            if noConnection:
                raise MAX31865Error("No Connection")
            elif shortToGround:
                raise MAX31865Error("Thermocouple short to ground")
            elif shortToVCC:
                raise MAX31865Error("Thermocouple short to VCC")
            else:
                # Perhaps another SPI device is trying to send data?
                # Did you remember to initialize all other SPI devices?
                raise MAX31865Error("Unknown Error")

    def data_to_temp(self,raw):
        #Takes raw RTD data and returns RTD temperature in units as well as RTD resistance.
        RefR = 400.0 #RefR/2        
        R0 = raw * RefR / 32768
        if R0==0:
            temperature_data = ['', '', '']       
        else:         
            t = -247.29 + 2.3992*R0 + 0.00063962*R0*R0 + 1.0241E-6*R0*R0*R0
            if self.units == "f":
                t=self.to_f(t)
            elif self.units == "k":
                t=self.to_k(t)
            #temperature_data = ['{:.0f}'.format(raw), '{:.4f}'.format(R0), '{:.4f}'.format(t)]
            temperature_data = [raw,R0,t] 
            return temperature_data

    def convert(self, raw):
        temperature_data = self.data_to_temp(raw)

        temperature_data = ['{:.0f}'.format(temperature_data[0]), '{:.4f}'.format(temperature_data[1]), '{:.4f}'.format(temperature_data[2])]            
        temperature_data = tuple('-' if x == '' else x for x in temperature_data)
        temperature_data = '\t'.join(temperature_data)                   
        #return raw, R0, t
        #tempurature_data[3]=self.to_f(temperature_data[3])
        return temperature_data

    def get_temp(self):
        raw = self.get_data()
        temperature_data=self.data_to_temp(raw)
        #print(temperature_data)
        #print(type(temperature_data))
        if temperature_data != None:
            temperature = temperature_data[2]
        else:
            temperature = None
        return temperature
        
    
    def to_c(self, celsius):
        '''Celsius passthrough for generic to_* method.'''
        return celsius

    def to_k(self, celsius):
        '''Convert celsius to kelvin.'''
        return celsius + 273.15

    def to_f(self, celsius):
        '''Convert celsius to fahrenheit.'''
        return celsius * 9.0/5.0 + 32

    def cleanup(self):
        '''Selective GPIO cleanup'''
        GPIO.setup(self.cs_pin, GPIO.IN)
        GPIO.setup(self.clock_pin, GPIO.IN)