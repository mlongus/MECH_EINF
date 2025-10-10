"""-----------------------------------------------------
¦    File name: L2_Park_Sensor.py                       ¦
¦    Version: 1.1                                       ¦
¦    Authors:                                           ¦
¦       Jonas Josi                                      ¦
¦       Matthias Lang                                   ¦
¦       Christian Hohmann                               ¦
¦       Joschka Maters                                  ¦
¦    Date created: 2024/04/10                           ¦
¦    Last modified: 2025/08/20                          ¦
¦    Python Version: 3.11.2                             ¦
------------------------------------------------------"""

# ----------- import external Python module -----------
import time
import grove
from grove.gpio import GPIO
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger


# ----------- global constant -----------
ULTRA_SONIC_PORT = 5  # Connect Ultra Sonic Ranger to digital Port D5 on GrovePi
ULTRASONIC_UPDATE_INTERVAL = 0.1  # Delay in seconds [s] between two consecutive distance measurements
ULTRASONIC_UPDATE_ON_CHANGE = False  # Only update the distance when the measured distance has changed
LED_BAR_PORT = 18  # Connect LED bar to digital Port D18 on GrovePi
LED_BAR_LEVELS = 10  # Number of LEDs on LED bar
LED_BAR_DIST_MAX_LEVEL = 40  # Distance in [cm], represented by all leds on the LED bar lighting up

# ----------- global variable -----------
previous_distance = None # last measured distance in [cm]
led_level = 0

# ----------- class with LED_bar functions ---------------
#=========================================================
#=========================================================
__all__ = ['GroveLedBar']

class GroveLedBar(object):
    '''
    Class for Grove - LED Bar

    Args:
        pin(int): number of digital pin the led bar connected.
        reverse: sets the led bar direction for level values. default False.
    '''
    def __init__(self, pin, reverse=False):
        self._dio = GPIO(pin, direction=GPIO.OUT)
        self._clk = GPIO(pin + 1, direction=GPIO.OUT)
        self._reverse = reverse
        self._clk_data = 0

    def __del__(self):
        self.level(0)
        self._dio.write(0)
        self._clk.write(0)

    @property
    def reverse(self):
        '''
        led bar direction for level values.
        '''
        return self._reverse
    
    @reverse.setter
    def reverse(self, value: bool):
        if type(value) is not bool:
            raise TypeError('reverse must be bool')
        self._reverse = value

    def level(self, value, brightness=255):
        '''
        select a level to light the led bar.
        value: number of level, 0 - 10.
        brightness:
            8-bit grayscale mode: 0 - 127 (128 - 255)
        '''
        
        self._begin()
        for i in range(10) if self._reverse else range(9,-1,-1) :
            self._write16(brightness if value > i else 0)
        self._end()
        # print(']')

    def bits(self, val, brightness=255):
        val &= 0x3FF
        self._begin()
        for i in range(9,-1,-1) if self._reverse else range(10):
            self._write16(brightness if (val >> i) & 1 else 0)
        self._end()

    def bytes(self, buf):
        self._begin()
        for i in range(9,-1,-1) if self._reverse else range(10):
            self._write16(buf[i])
        self._end()

    def _begin(self):
        self._write16(0)    # 8-bit grayscale mode

    def _end(self):
        '''
        fill to 208-bit shift register
        '''
        self._write16(0)
        self._write16(0)
        self._latch()


    def _send_clock(self):
        self._clk_data = abs(self._clk_data - 1)
        self._clk.write(self._clk_data)

    def _write16(self, data):
        for i in range(15, -1, -1):
            self._dio.write((data >> i) & 1)
            self._send_clock()

    def _latch(self):
        '''
        Internal-latch control cycle
        '''
        self._dio.write(0)
        self._send_clock()  # keeping DCKI level
        time.sleep(.00022)  # Tstart: >220us

        for i in range(4):  # Send 4 DI pulses
            self._dio.write(1)
            time.sleep(.00000007)    # twH: >70ns
            self._dio.write(0)
            time.sleep(.00000023)    # twL: >230ns

        time.sleep(.0000002)    # Tstop: >200ns (not supported cascade)


# ----------- function definition -----------
def get_ultra_sonic_distance(sensor, n_measurements=1):
    """
    Return the measured distance of the ultrasonic sensor in centimeters [cm].

    Parameters
    ----------
    sensor : GroveUltrasonicRanger
        object of ultrasonic sensor
    n_measurements : int, optional
        Number of measurements to be taken.

    Returns
    -------
    int
        Measured distance in centimeters [cm]. If n_measurements > 1, the rounded mean value of all measurements is returned.
    """
    distance_sum = 0
    n_measurements = int(n_measurements)

    if n_measurements >= 1:
        # Sum the output of n measurement(s)
        for _ in range(n_measurements):
            distance_sum += sensor.get_distance()  # Get distance from ultrasonic sensor
        average_distance = distance_sum / n_measurements  # Calculate mean value of all n measurements
        average_distance = int(round(average_distance, 0)) # Convert the averaged distance to a whole number
    else:
        average_distance = sensor.get_distance()  # Get distance from ultrasonic sensor
    return average_distance


# ----------- main code -----------
if __name__ == "__main__":
    # Initialize LED bar
    ledbar = GroveLedBar(LED_BAR_PORT)
    # Initialize Ultrasonic Ranger    
    ultrasonic = GroveUltrasonicRanger(ULTRA_SONIC_PORT)

    try:
        previous_distance = None  
        # endless loop
        while True:

            new_distance = get_ultra_sonic_distance(ultrasonic)

            if ULTRASONIC_UPDATE_ON_CHANGE:
                if new_distance != previous_distance:
                    previous_distance = new_distance
                    print(previous_distance, 'cm')
                    print("here")

            else:
                previous_distance = new_distance
                led_level = LED_BAR_LEVELS - int(min(LED_BAR_LEVELS / LED_BAR_DIST_MAX_LEVEL * previous_distance, LED_BAR_LEVELS))
                # Print distance value from the Ultrasonic sensor and level of led bar
                print(previous_distance, 'cm', "--->", led_level, "LEDs")
                ledbar.level(led_level)
                #previous_distance = distance
                #print(previous_distance, 'cm')
                
            time.sleep(ULTRASONIC_UPDATE_INTERVAL)

            """time.sleep(ULTRASONIC_UPDATE_INTERVAL)
            distance = get_ultra_sonic_distance(5, True)
            if distance:
                led_level = LED_BAR_LEVELS - int(min(LED_BAR_LEVELS / LED_BAR_DIST_MAX_LEVEL * distance, LED_BAR_LEVELS))
                # Print distance value from the Ultrasonic sensor and level of led bar
                print(distance, 'cm', "--->", led_level, "LEDs")
                ledbar.level(led_level)
                previous_distance = distance"""
    except KeyboardInterrupt:
        # Turn off LED bar
        ledbar.level(0)
        print("\nExit Python!")
        exit(0)