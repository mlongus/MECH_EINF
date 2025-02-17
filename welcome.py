"""-----------------------------------------------------
¦    File name: welcome.py                              ¦
¦    Version: 1.0                                       ¦
¦    Author: Jonas Josi                                 ¦
¦    Date created: 2025/02/17                           ¦
¦    Last modified: 2025/02/17                          ¦
¦    Python Version: 3.7.3                              ¦
------------------------------------------------------"""

# ----------- import external Python module -----------
import time
import os


# ----------- global constant -----------
CLASS_NAME = "MECH_LAB"
PDF_FILE_DEV_ENV_INSTRUCTION = "Konfiguration_Entwicklungsumgebung.pdf"

LED_BAR_PORT = 2  # Connect LED bar to digital Port D2 on GrovePi
LED_BAR_LEDS = 10  # Number of individual LEDs on Led-Bar
LED_BAR_SWITCH_DELAY = 0.3  # delay in seconds  


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
        import grovepi

        # Initialize LED bar
        grovepi.ledBar_init(LED_BAR_PORT, 0)
        grovepi.ledBar_orientation(LED_BAR_PORT, 1)
        grovepi.pinMode(LED_BAR_PORT, "OUTPUT")

        try:
            hostname = os.uname().nodename + ".simple.eee.intern"
            print("\nLED-Bar ansteuern", end="", flush=True)

            # Ascending ramp: 0 -> 10 active LEDs
            for active_led in range(LED_BAR_LEDS + 1):
                grovepi.ledBar_setLevel(LED_BAR_PORT, active_led)
                print(".", end="", flush=True)  # Add progress indicator (progress bar)
                time.sleep(LED_BAR_SWITCH_DELAY)

            # Descending ramp: 10 -> 0 active LEDs
            for active_led in range(LED_BAR_LEDS, -1, -1):
                grovepi.ledBar_setLevel(LED_BAR_PORT, active_led)
                print(".", end="", flush=True)  # Add progress indicator (progress bar)
                time.sleep(LED_BAR_SWITCH_DELAY)

            print("\n\n******************* Gratulation! *******************")
            print(f"Sie haben soeben ein Python Skript zur Ansteuerung einer LED-Bar auf dem Raspberry Pi '{hostname}' ausgeführt. Somit haben Sie die für das Modul {CLASS_NAME} verwendete Programierumgebung erfolgreich eingerichtet.")
        except KeyboardInterrupt:
            # Turn off LED bar before exiting
            grovepi.ledBar_setLevel(LED_BAR_PORT, 0)
            print("\nExiting Python!")
            exit(0)
    else:
        print("\n\n******************* Fast geschafft! *******************")
        print(f"Dieses Python-Skript wird auf ihrem persönlichen Computer/Laptop ausgeführt. Folgen Sie den Instruktionen des Abschnitts '5.1 - 5.3' des auf ILIAS abgelegten File '{PDF_FILE_DEV_ENV_INSTRUCTION}', um die Konfiguration der Entwicklungsumgebung abzuschliessen und dieses Python-Skript auf dem Raspberry Pi auszuführen.")