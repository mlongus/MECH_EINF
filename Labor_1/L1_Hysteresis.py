"""-----------------------------------------------------
¦    File name: L1_Hysteresis.py                        ¦
¦    Version: 1.0                                       ¦
¦    Author: Jonas Josi                                 ¦
¦    Date created: 2023/03/01                           ¦
¦    Last modified: 2023/03/01                          ¦
¦    Python Version: 3.7.3                              ¦
------------------------------------------------------"""

import time
import grovepi

# -------------------- global constants --------------------
POT_PIN = 0  # Connect the Grove Rotary Angle Sensor to analog port A0 of GrovePi-Board
PROX_PIN = 2 # Connect inductive proximity sensor to digital port D2 of GrovePi-Board
ADC_REF = 5  # Reference voltage of ADC (which is built-in the GrovePi-Board) is 5 V
ADC_RES = 1023  # The ADC on the GrovePi-Board has a resolution of 10 bit -> 1024 different digital levels in range of 0-1023


# -------------------- functions --------------------
def read_proximity_sensor(pin):
    """
    Returns True, if the (inductive) proximity sensor detects the presence of a (metalic) object.
    If no (metalic) object is detected by the sensor, False is returned.

    Parameters
    ----------
    pin : int
        GPIO of GrovePi connected to (inductive) proximity sensor.
    """
    detected = bool(grovepi.digitalRead(pin))
    return detected

def read_voltage_potentiometer(pin):
    """
    Returns the current voltage in [V] of the potentiometer by mapping the (digital) value returned
    by the function grovepi.analogRead() to the reference voltage of the ADC (analog-to-digital-converter)

    Parameters
    ----------
    pin : int
        GPIO of GrovePi connected to potentiometer.
    """
    sensor_value = grovepi.analogRead(pin) # digital value between 0 and 1023 (see constant "ADC_RES")
    voltage = float(sensor_value) * ADC_REF / ADC_RES
    return voltage


def read_angle_potentiometer(pin, offset, sensitivity):
    """
    Returns the current angle in [°] of the potentiometer.

    Parameters
    ----------
    pin : int
        GPIO of GrovePi connected to potentiometer.
    offset : int
        Voltage offset in [V] for zero-position / reference-position. This value can be determined by running the
        function calibrate_potentiometer())
    sensitivity : float
        Change of the measured voltage in relation to the change of position/angle of the potentiometer
        in [V/°]. This value can be determined by running the function calibrate_potentiometer())
    """
    voltage = read_voltage_potentiometer(pin)
    # angle = round((voltage - offset) / sensitivity, 2)
    angle = round((offset - voltage) / sensitivity, 2)
    return angle


def calibrate_potentiometer(pin, min_cal_angle, max_cal_angle):
    """
    Returns the sensitivity of the potentiometer in [V/°] and the offset in [V] to the zero-position /
    reference-position of the potentiometer. The user is guided through the calibration process via user prompt and
    is instructed to do calibration measurements on three predefined angular positions of the potentiometer
    (min_cal_angle, max_cal_angle, and zero-position).

    Parameters
    ----------
    pin : int
        GPIO of GrovePi connected to potentiometer.
    min_cal_angle : int
        Real angular position/orientation of potentiometer at first/min calibration point.
    max_cal_angle : int
        Real angular position/orientation of potentiometer at second/max calibration point.
    """
    range_cal_deg = abs(max_cal_angle - min_cal_angle)
    print("*" * 20, "Kalibrierung von Potentiometer", "*" * 20)
    input(f"Bitte Potentiometer auf {min_cal_angle} ° positionieren und mit <Enter> bestätigen\n")
    min_cal_voltage = read_voltage_potentiometer(pin)
    input(f"Bitte Potentiometer auf {max_cal_angle} ° positionieren und mit <Enter> bestätigen\n")
    max_cal_voltage = read_voltage_potentiometer(pin)
    range_cal_voltage = abs(max_cal_voltage - min_cal_voltage)
    _pot_sensitivity = range_cal_voltage / range_cal_deg  # [V/°]
    # print(f"voltage diff between min. calibration angle ({min_cal_angle}) and max. calibration angle ({max_cal_angle}): {range_cal_voltage}")
    input("Bitte Potentiometer auf 0° positionieren und mit <Enter> bestätigen\n")
    pot_zero_offset = read_voltage_potentiometer(pin)  # offset at zero position in [V]
    print(f"Kalibrierung des Potentiometers beendet -> Sensitivität: {_pot_sensitivity} [V/°], Spannungs-Offset zu Nullpunkt (0 °): {pot_zero_offset} [V]")
    return _pot_sensitivity, pot_zero_offset


# -------------------- main --------------------
if __name__ == "__main__":
    pot_sensitivity, pot_offset = calibrate_potentiometer(POT_PIN, -90, 90)
    print("\n\nMessung gestartet\n")
    print("*" * 28, " Messung ", "*" * 28)
    pot_angle = read_angle_potentiometer(POT_PIN, pot_offset, pot_sensitivity)
    prox_detected = read_proximity_sensor(PROX_PIN)
    print(f"\rPotentiometer Winkel: {str(pot_angle) + ' °':<11} Material detektiert: {'Ja  ' if prox_detected else 'Nein'}", end='')
    while True: # refresh potentiometer position and state of proximity sensor 
        _pot_angle = read_angle_potentiometer(POT_PIN, pot_offset, pot_sensitivity)
        _prox_detected = read_proximity_sensor(PROX_PIN)
        if _pot_angle != pot_angle or _prox_detected != prox_detected: # if position of potentiometer and/or state of proximity sensor has changed, refresh print output
            pot_angle = _pot_angle
            prox_detected = bool(_prox_detected)
            print(f"\rPotentiometer Winkel: {str(pot_angle) + ' °':<11} Material detektiert: {'Ja  ' if prox_detected else 'Nein'}", end='')
        time.sleep(0.1)