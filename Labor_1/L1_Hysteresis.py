"""-----------------------------------------------------
¦    File name: L1_Hysteresis.py                        ¦
¦    Version: 1.1                                       ¦
¦    Authors:                                           ¦
¦       Jonas Josi                                      ¦
¦       Matthias Lang                                   ¦
¦       Christian Hohmann                               ¦
¦    Date created: 2023/03/01                           ¦
¦    Last modified: 2025/08/19                          ¦
¦    Python Version: 3.11.2                             ¦
------------------------------------------------------"""

# ----------- import external Python module -----------
import time
from grove.adc import ADC
from grove.gpio import GPIO
#import grovepi

# ----------- global constant -----------
POT_PIN = 2  # Connect the Grove Rotary Angle Sensor to analog port A0 of GrovePi-Board
PROX_PIN = 16  # Connect inductive proximity sensor to digital port D2 of GrovePi-Board
ADC_REF = 3.3  # Reference voltage of ADC (which is built-in the Grove BaseHat) is 3.3 V
ADC_RES = 4095  # The ADC on the GrovePi-Board has a resolution of 10 bit -> 1024 different digital levels in range of 0-1023

# -------------------- Klassen und Funktionen --------------------
adc = ADC() # Create ADC Object once
prox_gpio = GPIO(PROX_PIN, GPIO.IN) # Initialize Grove BaseHat port for Digital Reading 

# ----------- function definition -----------
def read_proximity_sensor(pin):
    """
    Returns if a (metalic) object is within the sensing distance of the inductive proximity sensor.

    Parameters
    ----------
    pin : int
        digital port of Grove BaseHat connected to (inductive) proximity sensor.

    Returns
    -------
    bool
        True if an object is detected, False otherwise.gpioinfo gpiochip0
    """
    detected = bool(prox_gpio.read())
    return detected

def read_voltage_potentiometer(pin):
    """
    Returns the current voltage in [V] of the potentiometer by mapping the (digital) value returned
    by the function adc.read(channel) to the reference voltage of the ADC (analog-to-digital-converter)

    Parameters
    ----------
    pin : int
        analog port of Grove BaseHat connected to potentiometer.

    Returns
    -------
    float
        voltage of potentiometer in [V].
    """
    sensor_value = adc.read(pin) # digital value between 0 and 4095 (see constant "ADC_RES")
    voltage = float(sensor_value) * ADC_REF / ADC_RES
    return voltage

def read_angle_potentiometer(pin, offset, sensitivity):
    """
    Returns the current angle in [°] of the potentiometer.

    Parameters
    ----------
    pin : int
        analog port of Grove BaseHat connected to potentiometer.
    offset : float
        Voltage offset in [V] for zero-position / reference-position. This value can be determined by running the
        function calibrate_potentiometer())
    sensitivity : float
        Change of the measured voltage in relation to the change of position/angle of the potentiometer
        in [V/°]. This value can be determined by running the function calibrate_potentiometer())

    Returns
    -------
    float
        angle of potentiometer in [°].
    """
    voltage = read_voltage_potentiometer(pin)
    angle = round((offset - voltage) / sensitivity, 2)
    return angle

def calibrate_potentiometer(pin, min_cal_angle, max_cal_angle):
    """
    Returns the sensitivity of the potentiometer in [V/°] and the offset in [V] at the zero-position (0°)
    of the potentiometer. The user is guided through the calibration process via user prompt and
    is instructed to do calibration measurements on three predefined angular positions of the potentiometer
    (min_cal_angle, max_cal_angle, and zero-position).

    Parameters
    ----------
    pin : int
        analog port of Grove BaseHat connected to potentiometer.
    min_cal_angle : int
        Real angular position/orientation [°] of potentiometer at first/min calibration point.
    max_cal_angle : int
        Real angular position/orientation [°] of potentiometer at second/max calibration point.

    Returns
    -------
    tuple
        A tuple containing:
            - sensitivity of the potentiometer in [V/°].
            - offset of the potentiometer in [V] at the zero-position (0°).
    """
    range_cal_deg = abs(max_cal_angle - min_cal_angle)  # calibration range [°]
    print("*" * 20, "Kalibrierung von Potentiometer", "*" * 20)
    
    input(f"Bitte Potentiometer auf {min_cal_angle} ° positionieren und mit <Enter> bestätigen\n")
    min_cal_voltage = read_voltage_potentiometer(pin)  # potentiometer voltage [V] at min. calibration angle

    input(f"Bitte Potentiometer auf {max_cal_angle} ° positionieren und mit <Enter> bestätigen\n")
    max_cal_voltage = read_voltage_potentiometer(pin)  # potentiometer voltage [V] at max. calibration angle
    
    range_cal_voltage = abs(max_cal_voltage - min_cal_voltage)  # change in potentiometer voltage [V] over full range of calibration angle
    _pot_sensitivity = range_cal_voltage / range_cal_deg  # potentiometer sensitivity [V/°]
    # print(f"voltage diff between min. calibration angle ({min_cal_angle}) and max. calibration angle ({max_cal_angle}): {range_cal_voltage}")
    
    input("Bitte Potentiometer auf 0° positionieren und mit <Enter> bestätigen\n")
    pot_zero_offset = read_voltage_potentiometer(pin)  # offset at zero position (0 °) in [V]
    
    print(f"Kalibrierung des Potentiometers beendet -> Sensitivität: {_pot_sensitivity} [V/°], Spannungs-Offset zu Nullpunkt (0 °): {pot_zero_offset} [V]")
    return _pot_sensitivity, pot_zero_offset


# ----------- main code -----------
if __name__ == "__main__":
    # calibrate potentiometer
    pot_sensitivity, pot_offset = calibrate_potentiometer(POT_PIN, -90, 90)
    
    # start angle measurement (with potentiometer)
    print("\n\nMessung gestartet\n")
    print("*" * 28, " Messung ", "*" * 28)
    pot_angle = read_angle_potentiometer(POT_PIN, pot_offset, pot_sensitivity)  # read angle of potentiometer
    material_detected = read_proximity_sensor(PROX_PIN)  # check if material is detected by ind. proximity sensor
    print(f"\rPotentiometer Winkel: {str(pot_angle) + ' °':<11} Material detektiert: {'Ja  ' if material_detected else 'Nein'}", end='')
    
    # endless loop
    while True: 
        _pot_angle = read_angle_potentiometer(POT_PIN, pot_offset, pot_sensitivity)  # read angle of potentiometer
        _prox_detected = read_proximity_sensor(PROX_PIN)  # check if material is detected by ind. proximity sensor
        if _pot_angle != pot_angle or _prox_detected != material_detected:  # if position of potentiometer and/or state of proximity sensor has changed, refresh print output
            pot_angle = _pot_angle
            material_detected = bool(_prox_detected)
            print(f"\rPotentiometer Winkel: {str(pot_angle) + ' °':<11} Material detektiert: {'Ja  ' if material_detected else 'Nein'}", end='')
        time.sleep(0.1)