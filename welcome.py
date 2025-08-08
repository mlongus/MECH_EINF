"""-----------------------------------------------------
¦    File name: welcome.py                              ¦
¦    Version: 1.1                                       ¦
¦    Authors:                                           ¦
¦       Jonas Josi                                      ¦
¦       Christian Hohmann                               ¦
¦    Date created: 2025/02/17                           ¦
¦    Last modified: 2025/08/08                          ¦
¦    Python Version: 3.11.2                             ¦
¦                                                       ¦
¦    Adoptions:                                         ¦
¦     - Implementation of Grove Base Hat                ¦             
------------------------------------------------------"""

# ----------- import external Python module -----------
import time
import os


# ----------- global constant -----------
CLASS_NAME = "MECH_LAB"
PDF_FILE_DEV_ENV_INSTRUCTION = "Konfiguration_Entwicklungsumgebung.pdf"

LED_BAR_PORT = 18  # Connect LED bar to digital Port D18 on BaseHat
LED_BAR_LEDS = 10  # Number of individual LEDs on Led-Bar
LED_BAR_SWITCH_DELAY = 0.3  # delay in seconds  

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

# -------------------- functions --------------------
def is_raspberry_pi():
    """
    Returns True if the script is running on a Raspberry Pi, otherwise False.

    The function checks for the presence of the file '/proc/device-tree/model'
    and verifies if the string "raspberry pi" is contained in it. This method
    reliably identifies Raspberry Pi devices.

    Returns
    -------
    bool
        True if running on a Raspberry Pi, otherwise False.
    """
    try:
        # check if String "raspberry pi" is in file /proc/device-tree/model
        model_path = "/proc/device-tree/model"
        if os.path.exists(model_path):
            with open(model_path, "r") as f:
                model = f.read().lower()
                if "raspberry pi" in model:
                    return True
    except Exception as e:
        print(f"Error occured in function is_raspberry_pi: {e}")
    return False

# ----------- main code -----------
if __name__ == "__main__":
    # Check if this script is running on a Raspberry Pi
    if is_raspberry_pi():
        import grove
        from grove.gpio import GPIO

        # Initialize LED bar
        ledbar = GroveLedBar (LED_BAR_PORT)

        try:
            hostname = os.uname().nodename + ".simple.eee.intern"
            print("\nLED-Bar ansteuern", end="", flush=True)

            # Ascending ramp: 0 -> 10 active LEDs
            for active_led in range(LED_BAR_LEDS + 1):
                ledbar.level(active_led, 64)
                print(".", end="", flush=True)  # Add progress indicator (progress bar)
                time.sleep(LED_BAR_SWITCH_DELAY)

            # Descending ramp: 10 -> 0 active LEDs
            for active_led in range(LED_BAR_LEDS, -1, -1):
                ledbar.level(active_led, 64)
                print(".", end="", flush=True)  # Add progress indicator (progress bar)
                time.sleep(LED_BAR_SWITCH_DELAY)

            print("\n\n******************* Gratulation! *******************")
            print(f"Sie haben soeben ein Python Skript zur Ansteuerung einer LED-Bar auf dem Raspberry Pi '{hostname}' ausgeführt. Somit haben Sie die für das Modul {CLASS_NAME} verwendete Programierumgebung erfolgreich eingerichtet.")
        except KeyboardInterrupt:
            # Turn off LED bar before exiting
            ledbar.level(0)
            print("\nExiting Python!")
            exit(0)
    else:
        print("\n\n******************* Fast geschafft! *******************")
        print(f"Dieses Python-Skript wird auf ihrem persönlichen Computer/Laptop ausgeführt. Folgen Sie den Instruktionen des Abschnitts '5.1 - 5.3' des auf ILIAS abgelegten File '{PDF_FILE_DEV_ENV_INSTRUCTION}', um die Konfiguration der Entwicklungsumgebung abzuschliessen und dieses Python-Skript auf dem Raspberry Pi auszuführen.")