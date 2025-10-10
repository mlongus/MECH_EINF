"""-----------------------------------------------------
¦    File name: L3_ReadUltrasonic.py                    ¦
¦    Version: 2.0                                       ¦
¦    Author: Jonas Josi                                 ¦
¦    Date created: 2024/04/10                           ¦
¦    Last modified: 2025/03/07                          ¦
¦    Python Version: 3.11.2                             ¦
------------------------------------------------------"""

# ----------- Import external Python module -----------
import time
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

# ----------- Global constant -----------
ULTRASONIC_PORT = 5  # Connect Ultra Sonic Ranger to digital Port D5 on GrovePi
ULTRASONIC_UPDATE_INTERVAL = 0.1  # Delay in seconds [s] between two consecutive distance measurements
ULTRASONIC_UPDATE_ON_CHANGE = False  # Only update the distance when the measured distance has changed


# ----------- Function definition -----------
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


# ----------- Main code -----------
if __name__ == "__main__":
    try:
        previous_distance = None  # Last measured distance in [cm]
        # Initialize object of class GroveUltrasonicRanger
        ultrasonic_ranger = GroveUltrasonicRanger(ULTRASONIC_PORT)

        # Endless loop
        while True:
            new_distance = get_ultra_sonic_distance(ultrasonic_ranger)

            if ULTRASONIC_UPDATE_ON_CHANGE:
                if new_distance != previous_distance:
                    previous_distance = new_distance
                    print(previous_distance, 'cm')
            else:
                previous_distance = new_distance
                print(previous_distance, 'cm')

            time.sleep(ULTRASONIC_UPDATE_INTERVAL)

    except KeyboardInterrupt:
        # Program is stopped (either by pressing the red square in PyCharm or by pressing <Ctrl> + <C>)
        print("\nExit Python!")
