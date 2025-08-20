"""-----------------------------------------------------
¦    File name: L2_SetLED.py                            ¦
¦    Version: 1.1                                       ¦
¦    Authors:                                           ¦
¦       Jonas Josi                                      ¦
¦       Matthias Lang                                   ¦
¦       Christian Hohmann                               ¦
¦    Date created: 2024/04/10                           ¦
¦    Last modified: 2025/08/20                          ¦
¦    Python Version: 3.11.2                             ¦
------------------------------------------------------"""
# ----------- import external Python module -----------
import time
import grove
from grove.gpio import GPIO

# ----------- global constant -----------
LED_BAR_PORT = 18  # Connect LED bar to digital Port D18 on GrovePi

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


# ----------- main code -----------
if __name__ == "__main__":
    # Initialize LED bar
    ledbar = GroveLedBar(LED_BAR_PORT)

    try:
        # endless loop
        while True:
            # Ask for a user input between 0 and 10
            user_input = input('\nGeben sie eine ganze Zahl mit Wert zwischen 0 und 10 ein: ')
            valid_user_input = False

            if user_input.isdigit():
                user_input = int(user_input)  # cast/convert user input to integer
                if 0 <= user_input <= 10:
                    valid_user_input = True

            if valid_user_input:
                ledbar.level(user_input) 
                print("-" * 10, user_input, "LEDs and LED-Bar eingeschaltet", "-" * 10)
            else:
                print("Eingegebner Wert ausserhalb des gültigen Bereichs")
    except KeyboardInterrupt:
        # Turn off LED bar
        ledbar.level(0)
        print("\nExit Python!")
        exit(0)