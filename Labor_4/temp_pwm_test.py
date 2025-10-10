"""-----------------------------------------------------
¦    File name: L4_DCmotor_pwm_safe.py                 ¦
¦    Version: 2.1                                       ¦
¦    Authors:                                           ¦
¦       Jonas Josi                                      ¦
¦       Matthias Lang                                   ¦
¦       Christian Hohmann                               ¦
¦       Joschka Maters                                  ¦
¦    Date created: 2024/05/01                           ¦
¦    Last modified: 2025/10/06                          ¦
¦    Python Version: 3.11.2                             ¦
¦    Description: Enhanced version with temporary PWM   ¦
¦                 disable for stepper motor operation   ¦
------------------------------------------------------"""
 
# ----------- import external Python module -----------
import lgpio
import time
import os
import subprocess
import atexit
from contextlib import contextmanager

# ----------- global constant -----------
# assign motor driver interface to GPIO's of Raspberry Pi
M1 = 20
M2 = 21
M3 = 6
M4 = 13
D1 = 26  # enable/disable output pins M1, M2
D2 = 12  # enable/disable output pins M3, M4 (PWM-PIN!)
 
# settings of stepper motor
DIRECTION = 0  # *** CHANGE ME *** movement direction (0 or 1) of slide on linear guideway
STEP_TIME = 0.0015 # *** CHANGE ME *** time in [s] between two consecutive steps of stepper motor

# Global storage for PWM state restoration
pwm_restore_data = {}

class PWMController:
    """
    Klasse zur temporären PWM-Kontrolle ohne dauerhafte Systemänderungen
    """
    
    def __init__(self):
        self.pwm_channels = []
        self.original_states = {}
        self.gpio_handle = None
        
    def scan_active_pwm_channels(self):
        """
        Scannt nach aktuell aktiven PWM-Kanälen
        """
        print("Scanning for active PWM channels...")
        active_channels = []
        
        # Prüfe PWM-Chips
        for chip_id in range(4):  # PWM-Chips 0-3 prüfen
            chip_path = f'/sys/class/pwm/pwmchip{chip_id}'
            if os.path.exists(chip_path):
                print(f"Found PWM chip: {chip_id}")
                
                # Prüfe Kanäle in diesem Chip
                try:
                    exported_path = os.path.join(chip_path, 'export')
                    if os.path.exists(exported_path):
                        # Prüfe welche Kanäle exportiert sind
                        for channel in range(4):  # 0-3 Kanäle pro Chip
                            channel_path = os.path.join(chip_path, f'pwm{channel}')
                            if os.path.exists(channel_path):
                                # Kanal ist exportiert, prüfe Status
                                enable_path = os.path.join(channel_path, 'enable')
                                if os.path.exists(enable_path):
                                    try:
                                        with open(enable_path, 'r') as f:
                                            enabled = f.read().strip()
                                        
                                        channel_info = {
                                            'chip': chip_id,
                                            'channel': channel,
                                            'path': channel_path,
                                            'enabled': enabled == '1'
                                        }
                                        
                                        active_channels.append(channel_info)
                                        print(f"  Channel {channel}: {'enabled' if channel_info['enabled'] else 'disabled'}")
                                        
                                    except Exception as e:
                                        print(f"  Error reading channel {channel}: {e}")
                                        
                except Exception as e:
                    print(f"Error scanning chip {chip_id}: {e}")
        
        return active_channels
    
    def backup_pwm_state(self):
        """
        Sichert aktuellen PWM-Zustand für spätere Wiederherstellung
        """
        print("Backing up PWM state...")
        self.pwm_channels = self.scan_active_pwm_channels()
        
        for channel_info in self.pwm_channels:
            try:
                channel_path = channel_info['path']
                state = {}
                
                # Sichere alle relevanten Parameter
                for param in ['enable', 'period', 'duty_cycle', 'polarity']:
                    param_path = os.path.join(channel_path, param)
                    if os.path.exists(param_path):
                        try:
                            with open(param_path, 'r') as f:
                                state[param] = f.read().strip()
                        except Exception as e:
                            print(f"Warning: Could not backup {param}: {e}")
                            state[param] = None
                
                channel_info['backup_state'] = state
                print(f"Backed up PWM chip{channel_info['chip']} channel{channel_info['channel']}")
                
            except Exception as e:
                print(f"Error backing up PWM state: {e}")
    
    def disable_pwm_temporarily(self):
        """
        Deaktiviert PWM temporär (ohne Systemänderungen)
        """
        print("Temporarily disabling PWM channels...")
        
        for channel_info in self.pwm_channels:
            if channel_info['enabled']:
                try:
                    enable_path = os.path.join(channel_info['path'], 'enable')
                    with open(enable_path, 'w') as f:
                        f.write('0')
                    print(f"Disabled PWM chip{channel_info['chip']} channel{channel_info['channel']}")
                except Exception as e:
                    print(f"Warning: Could not disable PWM channel: {e}")
    
    def restore_pwm_state(self):
        """
        Stellt ursprünglichen PWM-Zustand wieder her
        """
        print("Restoring original PWM state...")
        
        for channel_info in self.pwm_channels:
            if 'backup_state' in channel_info:
                try:
                    channel_path = channel_info['path']
                    state = channel_info['backup_state']
                    
                    # Stelle Parameter in korrekter Reihenfolge wieder her
                    param_order = ['polarity', 'period', 'duty_cycle', 'enable']
                    
                    for param in param_order:
                        if param in state and state[param] is not None:
                            param_path = os.path.join(channel_path, param)
                            if os.path.exists(param_path):
                                try:
                                    with open(param_path, 'w') as f:
                                        f.write(state[param])
                                except Exception as e:
                                    print(f"Warning: Could not restore {param}: {e}")
                    
                    print(f"Restored PWM chip{channel_info['chip']} channel{channel_info['channel']}")
                    
                except Exception as e:
                    print(f"Error restoring PWM channel: {e}")
    
    def force_gpio_digital_mode(self, pin_numbers):
        """
        Stellt sicher, dass spezifische GPIO-Pins im digitalen Modus sind
        """
        print(f"Configuring pins {pin_numbers} for digital I/O...")
        
        try:
            self.gpio_handle = lgpio.gpiochip_open(0)
            
            for pin in pin_numbers:
                try:
                    # Pin als digitalen Ausgang konfigurieren
                    lgpio.gpio_claim_output(self.gpio_handle, pin, 0)
                    print(f"GPIO {pin} configured as digital output")
                except Exception as e:
                    print(f"Warning: GPIO {pin} configuration: {e}")
                    
        except Exception as e:
            print(f"Error in GPIO configuration: {e}")
            return False
        
        return True

@contextmanager
def stepper_pwm_safe_mode():
    """
    Context Manager für PWM-sicheren Schrittmotor-Betrieb
    Verwendung: with stepper_pwm_safe_mode(): ...
    """
    pwm_controller = PWMController()
    
    try:
        print("\n" + "="*50)
        print("ENTERING PWM-SAFE STEPPER MODE")
        print("="*50)
        
        # 1. PWM-Zustand sichern
        pwm_controller.backup_pwm_state()
        
        # 2. PWM temporär deaktivieren
        pwm_controller.disable_pwm_temporarily()
        
        # 3. GPIO-Pins für digitale Verwendung konfigurieren
        critical_pins = [D2, M4]  # GPIO 12 und 13 (beide PWM-Pins)
        if not pwm_controller.force_gpio_digital_mode(critical_pins):
            raise Exception("Failed to configure GPIO pins")
        
        print("PWM-safe mode activated - stepper motor ready")
        print("-" * 50)
        
        # Stepper-Code kann hier ausgeführt werden
        yield pwm_controller.gpio_handle
        
    finally:
        print("\n" + "-" * 50)
        print("EXITING PWM-SAFE STEPPER MODE")
        print("-" * 50)
        
        # GPIO cleanup
        if pwm_controller.gpio_handle:
            try:
                # Alle Stepper-Pins freigeben
                stepper_pins = [M1, M2, M3, M4, D1, D2]
                for pin in stepper_pins:
                    try:
                        lgpio.gpio_free(pwm_controller.gpio_handle, pin)
                    except:
                        pass
                lgpio.gpiochip_close(pwm_controller.gpio_handle)
            except:
                pass
        
        # PWM-Zustand wiederherstellen
        pwm_controller.restore_pwm_state()
        print("Original PWM state restored")
        print("="*50)

# ----------- function definition -----------
def set_motor_coils(gpio_handle, coil_1, coil_2, coil_3, coil_4):
    """
    Set state (HIGH/LOW) of all 4 coils of stepper motor
    """
    lgpio.gpio_write(gpio_handle, M1, coil_1)
    lgpio.gpio_write(gpio_handle, M2, coil_2)
    lgpio.gpio_write(gpio_handle, M3, coil_3)
    lgpio.gpio_write(gpio_handle, M4, coil_4)

def stepper_optimized_sleep(secs):
    """
    Optimized sleep function for stepper motor timing ranges
    """
    if secs <= 0:
        return
    
    start_time = time.perf_counter()
    target_time = start_time + secs
    
    if secs < 0.0005:  # < 0.5ms: Only active waiting
        while time.perf_counter() < target_time:
            pass
    elif secs < 0.002:  # 0.5-2ms: Short passive + active
        time.sleep(secs - 0.0003)
        while time.perf_counter() < target_time:
            pass
    elif secs < 0.01:   # 2-10ms: Standard hybrid
        time.sleep(secs - 0.0005)
        while time.perf_counter() < target_time:
            pass
    else:               # > 10ms: Larger passive portion
        time.sleep(secs - 0.001)
        while time.perf_counter() < target_time:
            pass

def stop_motor(gpio_handle):
    """
    Stop stepper motor safely
    """
    # enable motor driver outputs
    lgpio.gpio_write(gpio_handle, D1, 1)
    lgpio.gpio_write(gpio_handle, D2, 1)
 
    # turn off all coils
    set_motor_coils(gpio_handle, 0, 0, 0, 0)
    stepper_optimized_sleep(STEP_TIME)
 
    # disable motor driver outputs
    lgpio.gpio_write(gpio_handle, D1, 0)
    lgpio.gpio_write(gpio_handle, D2, 0)
    print("\\nMotor stopped")

def run_stepper_motor():
    """
    Hauptfunktion für Schrittmotor mit PWM-Schutz
    """
    
    # PWM-sicherer Modus verwenden
    with stepper_pwm_safe_mode() as gpio_handle:
        
        # initialize all pins to safe state
        lgpio.gpio_write(gpio_handle, M1, 0)
        lgpio.gpio_write(gpio_handle, M2, 0)
        lgpio.gpio_write(gpio_handle, M3, 0)
        lgpio.gpio_write(gpio_handle, M4, 0)
        lgpio.gpio_write(gpio_handle, D1, 0)
        lgpio.gpio_write(gpio_handle, D2, 0)
 
        # enable motor driver outputs
        lgpio.gpio_write(gpio_handle, D1, 1)  # enable output pins M1, M2
        lgpio.gpio_write(gpio_handle, D2, 1)  # enable output pins M3, M4
        
        print(f"Starting stepper motor (Direction: {DIRECTION}, Step time: {STEP_TIME}s)")
        print("Press Ctrl+C to stop...")
        
        try:
            step_count = 0
            timing_errors = []
            
            # endless loop
            while True:
                step_start = time.perf_counter()
                
                if DIRECTION == 0:
                    # activate coil 2 & coil 4
                    set_motor_coils(gpio_handle, 0, 1, 0, 1)
                    stepper_optimized_sleep(STEP_TIME)
                    # activate coil 2 & coil 3
                    set_motor_coils(gpio_handle, 0, 1, 1, 0)
                    stepper_optimized_sleep(STEP_TIME)
                    # activate coil 1 & coil 3
                    set_motor_coils(gpio_handle, 1, 0, 1, 0)
                    stepper_optimized_sleep(STEP_TIME)
                    # activate coil 1 & coil 4
                    set_motor_coils(gpio_handle, 1, 0, 0, 1)
                    stepper_optimized_sleep(STEP_TIME)
                else:
                    # activate coil 1 & coil 4
                    set_motor_coils(gpio_handle, 1, 0, 0, 1)
                    stepper_optimized_sleep(STEP_TIME)
                    # activate coil 1 & coil 3
                    set_motor_coils(gpio_handle, 1, 0, 1, 0)
                    stepper_optimized_sleep(STEP_TIME)
                    # activate coil 2 & coil 3
                    set_motor_coils(gpio_handle, 0, 1, 1, 0)
                    stepper_optimized_sleep(STEP_TIME)
                    # activate coil 2 & coil 4
                    set_motor_coils(gpio_handle, 0, 1, 0, 1)
                    stepper_optimized_sleep(STEP_TIME)
                
                # Timing-Analyse
                actual_cycle_time = time.perf_counter() - step_start
                expected_cycle_time = STEP_TIME * 4
                timing_error = abs(actual_cycle_time - expected_cycle_time) * 1000
                timing_errors.append(timing_error)
                
                step_count += 4  # 4 Schritte pro Zyklus
                
                # Status alle 25 Zyklen (100 Schritte)
                if len(timing_errors) % 25 == 0:
                    recent_errors = timing_errors[-25:]
                    avg_error = sum(recent_errors) / len(recent_errors)
                    print(f"Steps: {step_count}, Avg timing error: {avg_error:.3f}ms")
                    
                    # Halten nur die letzten 100 Messungen
                    if len(timing_errors) > 100:
                        timing_errors = timing_errors[-100:]
 
        # detect exception - usually triggered by a user input, stopping the script
        except KeyboardInterrupt:
            stop_motor(gpio_handle)
            
            # Finale Statistiken
            if timing_errors:
                avg_error = sum(timing_errors) / len(timing_errors)
                max_error = max(timing_errors)
                print(f"\\nFinal timing statistics:")
                print(f"Steps completed: {step_count}")
                print(f"Average timing error: {avg_error:.3f}ms")
                print(f"Maximum timing error: {max_error:.3f}ms")
                
                if avg_error < 0.5:
                    print("✅ Excellent timing precision achieved!")
                elif avg_error < 1.0:
                    print("✅ Good timing precision")
                else:
                    print("⚠️  Timing could be improved")
            
            print("\\nPWM state will be restored automatically...")

# Test-Funktion für verschiedene Frequenzen
def test_different_frequencies():
    """
    Testet verschiedene Step-Times mit PWM-Schutz
    """
    test_times = [0.0008, 0.002, 0.006]  # Ihre problematischen Zeiten
    
    print("\\nTesting different step frequencies with PWM protection...")
    print("=" * 60)
    
    for step_time in test_times:
        global STEP_TIME
        STEP_TIME = step_time
        
        freq_hz = 1 / step_time
        print(f"\\nTesting step time: {step_time}s ({freq_hz:.0f}Hz)")
        print("-" * 40)
        
        try:
            with stepper_pwm_safe_mode() as gpio_handle:
                
                # Kurzer Test mit 20 Schritten
                lgpio.gpio_write(gpio_handle, D1, 1)
                lgpio.gpio_write(gpio_handle, D2, 1)
                
                timing_errors = []
                
                for step in range(20):
                    start_time = time.perf_counter()
                    
                    # Ein Schritt
                    step_pattern = [(0,1,0,1), (0,1,1,0), (1,0,1,0), (1,0,0,1)]
                    coils = step_pattern[step % 4]
                    set_motor_coils(gpio_handle, *coils)
                    stepper_optimized_sleep(step_time)
                    
                    actual_time = time.perf_counter() - start_time
                    error_ms = abs(actual_time - step_time) * 1000
                    timing_errors.append(error_ms)
                
                # Stopp
                set_motor_coils(gpio_handle, 0, 0, 0, 0)
                lgpio.gpio_write(gpio_handle, D1, 0)
                lgpio.gpio_write(gpio_handle, D2, 0)
                
                # Auswertung
                avg_error = sum(timing_errors) / len(timing_errors)
                max_error = max(timing_errors)
                
                status = "✅ PASSED" if avg_error < 1.0 else "❌ FAILED"
                print(f"Result: {status}")
                print(f"Average error: {avg_error:.3f}ms, Max error: {max_error:.3f}ms")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        time.sleep(1)  # Pause zwischen Tests

# ----------- main code -----------
if __name__ == "__main__":
    print("PWM-Safe Stepper Motor Controller")
    print("=" * 50)
    
    try:
        while True:
            print("\\nOptions:")
            print("1. Run stepper motor (normal operation)")
            print("2. Test different frequencies")  
            print("3. Exit")
            
            choice = input("\\nSelect option (1-3): ").strip()
            
            if choice == '1':
                run_stepper_motor()
            elif choice == '2':
                test_different_frequencies()
            elif choice == '3':
                print("Exiting...")
                break
            else:
                print("Invalid option!")
                
    except KeyboardInterrupt:
        print("\\nProgram terminated")
    except Exception as e:
        print(f"\\nError: {e}")
    
    print("Exit Python")
