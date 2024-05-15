"""-----------------------------------------------------
¦    File name: L5_Regelkreis_zeit.py                ¦
¦    Version: 1.0                                       ¦
¦    Author: Jonas Josi                                 ¦
¦    Date created: 2024/05/15                           ¦
¦    Last modified: 2024/05/15                          ¦
¦    Python Version: 3.7.3                              ¦
------------------------------------------------------"""

# ----------- import external Python module -----------
import pigpio  # library to create hardware-based PWM signals on Raspberry Pi
import grovepi
import os
import re
import csv
import time


# ----------- global constant -----------
""" Settings """
k = 0.001  # *** CHANGE ME *** controller amplification factor k [s/mm]
N_MEASUREMENTS = 10  # *** CHANGE ME *** number of distance measurements [] over which to average
VOLTAGE = 6  # *** CHANGE ME *** voltage for DC motor [V] between 0 und 12 V (Voltage from power supply is always 12 V)
CSV_FILENAME = "Wegdiagramm_Zeit.csv"  # *** CHANGE ME *** file to log data (timestamp and distance)
CSV_DELIMITER = ";"  # *** CHANGE ME *** Character to separate data fields / cells in the CSV file

IR_SENSOR = 0  # Connect the Grove 80cm Infrared Proximity Sensor to analog port A0

# assign motor driver interface to GPIO's of Raspberry Pi
M1 = 20
M2 = 21
D1 = 26  # enable/disable output pins M1, M2


ADC_REF = 5  # Reference voltage of ADC (which is built-in the GrovePi-Board) is 5 V
ADC_RES = 1023  # The ADC on the GrovePi-Board has a resolution of 10 bit -> 1024 different digital levels in range of 0-1023


# auxiliary parameters
MAX_VOLTAGE = 12  # supply voltage of motor driver is 12 V (which equals the max. rated voltage of the DC motor)
PWM_FREQUENCY = 4000  # Hz
PWM_DUTYCYCLE_RESOLUTION = 8  # 8 bit -> value range of PWM_DUTYCYCLE is between 0 (OFF) and 255 (FULLY ON)
PWM_DUTYCYCLE = round((2 ** PWM_DUTYCYCLE_RESOLUTION - 1) / MAX_VOLTAGE * VOLTAGE, 0)  # PWM_DUTYCYCLE from 0 (OFF) to 255 bit (FULLY ON)


# ----------- function definition -----------
def stop_motor():
    """
    Set state of both output pins of the motor driver (M1, M2) to LOW (0 V).
    Then disable the motor driver output pins (M1, M2).
    """
    # enable motor driver output pins (M1 and M2)
    pi1.write(D1, 1)

    # set state of motor driver outputs (M1 and M2) to low (0 V)
    pi1.write(M1, 0)
    pi1.write(M2, 0)

    # disable motor driver output pins (M1 and M2)
    pi1.write(D1, 0)

    print("\nMotor stopped")


def create_csv_file(filename):
    """
    If the CSV file does not exist, create it. If the filename already exists, append an underscore followed by the next
    available integer to the filename.

    Parameters
    ----------
    filename : str
        Path of the CSV file to be created. The path can be either absolute (full path) or a relative path to the directory of
        this script.

    Returns
    -------
    str or None
        If the CSV file was successfully created the filename is returned.
        If creating the CSV file failed, None is returned.
    """
    try:
        if os.path.exists(filename):  # Check if filename already exists
            # Remove the ".csv" suffix if file ends with ".csv"
            if filename.endswith(".csv"):
                filename = filename[:-4]
            pattern = re.compile(rf'{re.escape(filename)}_(\d+)\.csv$')  # Pattern to match underscore followed by numbers at end of filename
            matches = [pattern.search(f) for f in os.listdir('.') if pattern.search(f) and f.startswith(filename)]
            existing_suffixes = [int(match.group(1)) for match in matches]
            next_suffix = max(existing_suffixes, default=0) + 1
            filename = f"{filename}_{next_suffix}.csv"  # Update filename with next available suffix
        with open(filename, 'x') as csvfile:
            return filename
    except Exception as e:
        print(f"Error creating CSV file '{filename}': {e}")
        return None


def add_row_to_csv(filename, row_data, delimiter):
    """
    Add a row of data to an existing csv-file.

    Parameters
    ----------
    filename : String
        Path of csv-file to be append by an row. The path can be either absolute (full path) or a relative path
        to the path of this script.
    row_data : String
        Data to be added to the new row.
    delimiter : String
        Character or string used to separate data fields in the CSV file.


    Returns
    -------
    bool
        True if a row with data was successfully added to the csv-file.
        False if adding a row with data to the csv-file failed.
    """
    try:
        # open csv-file in append mode ('a')
        with open(filename, 'a') as csvfile:
            # create csv_writer object
            csv_writer = csv.writer(csvfile, delimiter=delimiter)

            # convert string into a list in which each entry has the value of a cell
            lst_cell_values = row_data.split(delimiter)

            # append row to csv file (with corresponding data)
            csv_writer.writerow(lst_cell_values)
        return True
    except Exception as e:
        print(f"Error to add row '{row_data}' to csv-file '{filename}': {e}")
        return False

def read_voltage_ir_sensor(port):
    """
    Returns the current voltage in [V] of the infrared proximity sensor by mapping the (digital) value returned
    by the function grovepi.analogRead() to the reference voltage of the ADC (analog-to-digital-converter)

    Parameters
    ----------
    port : int
        analog port of GrovePi connected to infrared proximity sensor.

    Returns
    -------
    float or False
        if measurment of proximity sensor doesn't fail, the voltage on pin of infrared proximity sensor in [V]
        is returned. Otherwise False is returned.
    """
    try:
        sensor_value = grovepi.analogRead(port)  # digital value between 0 and 1023 (see constant "ADC_RES")
    except IOError:
        print(f"Error to read analog port {port}: {IOError}")
        return False
    voltage = float(sensor_value) * ADC_REF / ADC_RES
    return voltage


# ----------- main code -----------
if __name__ == "__main__":
    # initialize pigpio
    pi1 = pigpio.pi()  # Create an Object of class pigpio.pi
    # enable motor driver output pins (M1 and M2)
    pi1.write(D1, 1)
    # set pwm frequencies of driver output pins (M1 and M2)
    pi1.set_PWM_frequency(M1, PWM_FREQUENCY)
    pi1.set_PWM_frequency(M2, PWM_FREQUENCY)

    # initalize infrared sensor (pin)
    grovepi.pinMode(IR_SENSOR, "INPUT")

    # Ask user for the Set-distance
    valid_userinput = False
    while not valid_userinput:
        userinput = input("Auf welche Distanz zwischen 30 mm und 60 mm soll gefahren werden? ")
        if userinput.isdigit():  # if userinput includes only digits
            if 30 <= int(userinput) <= 60:  # check if userinput is within range 30 - 60 mm
                valid_userinput = True
            else:
                print("nur Werte zwischen 30 und 60 als Input erlaubt")
        else:
            print("nur ganze Zahlen als Input erlaubt")

    set_distance = float(userinput)
    filename = create_csv_file(CSV_FILENAME)
    if filename:
        print(f"csv-file '{filename}' created")
    else:
        print(f"failed to create csv-file '{CSV_FILENAME}'")
        exit(0)

    # add first row to csv file, with parameters this script
    if CSV_DELIMITER == ",":
        add_row_to_csv(filename,
                       f"k={k} (s/mm); voltage={VOLTAGE} (V); nmeasurements={N_MEASUREMENTS}; set_distance={int(set_distance)} (mm)",
                       CSV_DELIMITER)
    elif CSV_DELIMITER == ";":
        add_row_to_csv(filename,
                       f"k={k} (s/mm), voltage={VOLTAGE} (V), nmeasurements={N_MEASUREMENTS}, set_distance={int(set_distance)} (mm)",
                       CSV_DELIMITER)
    else:
        add_row_to_csv(filename,
                       f"k={k} (s/mm)  voltage={VOLTAGE} (V)  nmeasurements={N_MEASUREMENTS}  set_distance={int(set_distance)} (mm)",
                       CSV_DELIMITER)

    # add second row to csv file, with table headers 
    add_row_to_csv(filename, f"time (s){CSV_DELIMITER}ist_distanz (mm){CSV_DELIMITER}delta_distance (mm)", CSV_DELIMITER)
    
    start_timestamp = None
    
    """ control loop with constant speed and dynamically calculated drivetime """
    while True:
        try:
            measurement = 0
            sum_voltage = 0

            while measurement < N_MEASUREMENTS:
                voltage = read_voltage_ir_sensor(IR_SENSOR)
                if voltage:
                    sum_voltage += voltage
                    measurement += 1

            # calculate average voltage of all measurements done
            average_voltage = sum_voltage / N_MEASUREMENTS

            # Calculate distance using sensor characteristics, coefficients found from calibration (L5_IR_kalibrieren.py)
            distance = round(44.593 * average_voltage * average_voltage - 152.73 * average_voltage + 159.38, 2)

            if start_timestamp:
                time_elapsed = round(time.time() - start_timestamp, 3)
            else:
                start_timestamp = time.time()
                time_elapsed = 0

            # Compare current distance with set distance
            delta_distance = set_distance - distance  # control error

            # update csv-file
            add_row_to_csv(filename, f"{time_elapsed}{CSV_DELIMITER}{distance}{CSV_DELIMITER}{round(delta_distance, 3)}", CSV_DELIMITER)

            # calculate drivetime
            drivetime = abs(delta_distance * k)   # time to drive the motor in [s]

            print(f"ist: {distance} mm, soll: {set_distance} mm -> delta_dist: {round(delta_distance, 4)} mm -> drivetime: {round(drivetime, 4)} s")

            # define motor direction
            if delta_distance >= 0:
                direction = 0
            else:
                direction = 1

            # drive motor with constant speed/voltage for calculated drivetime
            if direction == 0:
                # set output "M2" on motor driver to low (0 V)
                pi1.write(M2, 0)
                # set duty cycle of PWM signal on output "M1"
                pi1.set_PWM_dutycycle(M1, PWM_DUTYCYCLE)
            elif direction == 1:
                # set output "M1" on motor driver to low (0 V)
                pi1.write(M1, 0)
                # set duty cycle of PWM signal on output "M2"
                pi1.set_PWM_dutycycle(M2, PWM_DUTYCYCLE)
            time.sleep(drivetime)
        except KeyboardInterrupt:
            stop_motor()
            pi1.stop()  # Terminate the connection to the pigpiod instance and release resources
            print("\n " + "*" * 5 + f" Measurement stopped. Data saved to Log-File: {filename} " + "*" * 5 + "\n ")
            print("Exit Python")
            exit(0)  # exit python with exit code 0