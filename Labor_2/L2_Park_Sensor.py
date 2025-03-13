"""-----------------------------------------------------
¦    File name: L2_Park_Sensor.py                       ¦
¦    Version: 1.0                                       ¦
¦    Author: Jonas Josi                                 ¦
¦    Date created: 2024/04/10                           ¦
¦    Last modified: 2024/04/10                          ¦
¦    Python Version: 3.7.3                              ¦
------------------------------------------------------"""

# ----------- import external Python module -----------
import grovepi

# ----------- global constant -----------
ULTRA_SONIC_PORT = 5  # Connect Ultra Sonic Ranger to digital Port D5 on GrovePi
LED_BAR_PORT = 2  # Connect LED bar to digital Port D2 on GrovePi
LED_BAR_LEVELS = 10  # Number of LEDs on LED bar
LED_BAR_DIST_MAX_LEVEL = 40  # Distance in [cm], represented by all leds on the LED bar lighting up

# ----------- global variable -----------
previous_distance = None # last measured distance in [cm]
led_level = 0

# ----------- function definition -----------
def get_ultra_sonic_distance(port, n_measurement=1, return_on_change = False):
    """
    Returns the measured distance of the ultrasonic sensor in centimeters.

    Parameters
    ----------
    port : int
        digital port of GrovePi connected to the ultrasonic sensor.
    n_measurement : int, optional
        Number of measurements to be taken. If greater than 1, the mean value of all measurements is returned.
    return_on_change : bool, optional
        If True, the function only returns a value if the measured distance differs from the last measured distance.

    Returns
    -------
    int or None
        The measured distance in centimeters, or None if return_on_change is True and the distance has not changed.
    """

    distance_sum = 0
    n_measurement = int(n_measurement)

    if n_measurement >= 1:
        # sum the output of n measurement(s)
        for _ in range(n_measurement):
            distance_sum += grovepi.ultrasonicRead(port)  # get distance from ultra sonic sensor
        _distance = distance_sum / n_measurement # calculate mean value of all n measurements
        _distance = int(round(_distance, 0))
    else:
        _distance = grovepi.ultrasonicRead(port)  # get distance from ultra sonic sensor

    if return_on_change and _distance == previous_distance:
        return
    else:
        return _distance


# ----------- main code -----------
if __name__ == "__main__":
    # Initialize LED bar
    grovepi.ledBar_init(LED_BAR_PORT, 0)
    grovepi.ledBar_orientation(LED_BAR_PORT, 1)
    grovepi.pinMode(LED_BAR_PORT, "OUTPUT")

    try:
        # endless loop
        while True:
            distance = get_ultra_sonic_distance(ULTRA_SONIC_PORT, 5, True)
            if distance:
                led_level = LED_BAR_LEVELS - int(min(LED_BAR_LEVELS / LED_BAR_DIST_MAX_LEVEL * distance, LED_BAR_LEVELS))
                # Print distance value from the Ultrasonic sensor and level of led bar
                print(distance, 'cm', "--->", led_level, "LEDs")
                grovepi.ledBar_setLevel(LED_BAR_PORT, led_level)
                previous_distance = distance
    except KeyboardInterrupt:
        # Turn off LED bar
        grovepi.ledBar_setLevel(LED_BAR_PORT, 0)
        print("\nExit Python!")
        exit(0)