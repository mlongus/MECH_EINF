"""-----------------------------------------------------
¦    File name: L3_SetLED.py                            ¦
¦    Version: 1.0                                       ¦
¦    Author: Jonas Josi                                 ¦
¦    Date created: 2024/04/10                           ¦
¦    Last modified: 2024/04/10                          ¦
¦    Python Version: 3.7.3                              ¦
------------------------------------------------------"""

# ----------- import external Python module -----------
import grovepi

# ----------- global constant -----------
LED_BAR_PORT = 2  # Connect LED bar to digital Port D2 on GrovePi

# ----------- main code -----------
if __name__ == "__main__":
    # Initialize LED bar
    grovepi.ledBar_init(LED_BAR_PORT, 0)
    grovepi.ledBar_orientation(LED_BAR_PORT, 1)
    grovepi.pinMode(LED_BAR_PORT, "OUTPUT")

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
                grovepi.ledBar_setLevel(LED_BAR_PORT, user_input)
                print("-" * 10, user_input, "LEDs and LED-Bar eingeschalten", "-" * 10)
            else:
                print("Eingegebner Wert ausserhalb des gültigen Bereichs")
    except KeyboardInterrupt:
        # Turn off LED bar
        grovepi.ledBar_setLevel(LED_BAR_PORT, 0)
        print("\nExit Python!")
        exit(0)