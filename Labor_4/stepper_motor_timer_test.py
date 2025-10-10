"""-----------------------------------------------------
¦    File name: L4_DCmotor_timer_test.py                ¦
¦    Version: 2.0                                       ¦
¦    Authors:                                           ¦
¦       Jonas Josi                                      ¦
¦       Matthias Lang                                   ¦
¦       Christian Hohmann                               ¦
¦       Joschka Maters                                  ¦
¦    Date created: 2024/05/01                           ¦
¦    Last modified: 2025/10/06                          ¦
¦    Python Version: 3.11.2                             ¦
¦    Description: Enhanced version with multiple timer  ¦
¦                 implementations for testing           ¦
------------------------------------------------------"""
 
# ----------- import external Python module -----------
import lgpio
import time
import threading
import statistics
from enum import Enum

class TimerMode(Enum):
    """Enumeration for different timer implementations"""
    ORIGINAL_BUSY = "original"
    TIME_SLEEP = "time_sleep"
    PERF_COUNTER = "perf_counter"
    ADAPTIVE = "adaptive"
    STEPPER_OPTIMIZED = "stepper_optimized"
    YIELD_FRIENDLY = "yield_friendly"
    THREADING_BASED = "threading"

# ----------- global constant -----------
# assign motor driver interface to GPIO's of Raspberry Pi
M1 = 20
M2 = 21
M3 = 6
M4 = 13
D1 = 26  # enable/disable output pins M1, M2
D2 = 12  # enable/disable output pins M3, M4
 
# settings of stepper motor
DIRECTION = 0  # *** CHANGE ME *** movement direction (0 or 1) of slide on linear guideway
STEP_TIME = 0.003  # *** CHANGE ME *** time in [s] between two consecutive steps of stepper motor

# Global variables for timing analysis
timing_stats = []
current_timer_mode = TimerMode.ORIGINAL_BUSY
adaptive_sleep_overhead = 0.0005  # Initial value for adaptive mode
 
# ----------- timer function implementations -----------

def original_busy_sleep(secs):
    """Original busy_sleep implementation"""
    start_timestamp = time.time()
    if secs > 0.0004:
        time.sleep(secs - 0.0002)
    while time.time() - start_timestamp < secs:
        pass

def simple_time_sleep(secs):
    """Simple time.sleep() for comparison"""
    time.sleep(secs)

def perf_counter_busy_sleep(secs):
    """Improved version using time.perf_counter()"""
    if secs <= 0:
        return
    
    start_time = time.perf_counter()
    target_time = start_time + secs
    
    if secs > 0.001:  # 1ms
        time.sleep(secs - 0.0005)  # 0.5ms buffer
    
    while time.perf_counter() < target_time:
        pass

def adaptive_busy_sleep(secs):
    """Adaptive version that learns system sleep behavior"""
    global adaptive_sleep_overhead
    
    if secs <= 0:
        return
    
    start_time = time.perf_counter()
    target_time = start_time + secs
    
    # For very short times: only active waiting
    if secs <= adaptive_sleep_overhead * 2:
        while time.perf_counter() < target_time:
            pass
        return
    
    # Passive waiting with adaptive buffer
    passive_sleep_time = secs - adaptive_sleep_overhead
    sleep_start = time.perf_counter()
    time.sleep(passive_sleep_time)
    actual_sleep_time = time.perf_counter() - sleep_start
    
    # Adjust buffer based on actual sleep performance
    sleep_error = actual_sleep_time - passive_sleep_time
    if sleep_error > 0:
        adaptive_sleep_overhead = min(adaptive_sleep_overhead * 1.1, 0.002)
    elif sleep_error < -0.0001:
        adaptive_sleep_overhead = max(adaptive_sleep_overhead * 0.9, 0.0002)
    
    # Active waiting for remaining time
    while time.perf_counter() < target_time:
        pass

def stepper_optimized_sleep(secs):
    """Optimized specifically for stepper motor timing ranges"""
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

def yield_friendly_sleep(secs):
    """CPU-friendly version with occasional yields"""
    if secs <= 0:
        return
    
    start_time = time.perf_counter()
    target_time = start_time + secs
    
    if secs > 0.001:
        time.sleep(secs - 0.0005)
    
    yield_counter = 0
    while time.perf_counter() < target_time:
        yield_counter += 1
        if yield_counter % 1000 == 0:
            time.sleep(0)  # Yield to other threads
        pass

class ThreadingStepperController:
    """Threading-based precise stepper controller"""
    def __init__(self, gpio_handle):
        self.gpio_handle = gpio_handle
        self.running = False
        self.step_interval = STEP_TIME
        self.direction = DIRECTION
        self.step_sequences = {
            0: [(0,1,0,1), (0,1,1,0), (1,0,1,0), (1,0,0,1)],  # Direction 0
            1: [(1,0,0,1), (1,0,1,0), (0,1,1,0), (0,1,0,1)]   # Direction 1
        }
        self.current_step = 0
        
    def execute_step(self):
        """Execute one motor step"""
        sequence = self.step_sequences[self.direction]
        coils = sequence[self.current_step % len(sequence)]
        set_motor_coils(*coils)
        self.current_step += 1
        
    def step_thread(self):
        """Precise timing thread"""
        next_step = time.perf_counter()
        
        while self.running:
            self.execute_step()
            
            next_step += self.step_interval
            sleep_time = next_step - time.perf_counter()
            
            if sleep_time > 0.0001:
                time.sleep(sleep_time - 0.0001)
            
            while time.perf_counter() < next_step:
                pass
    
    def start(self):
        """Start the threading-based controller"""
        self.running = True
        self.thread = threading.Thread(target=self.step_thread, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the threading-based controller"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)

# Timer function selector
def get_sleep_function(mode):
    """Return the appropriate sleep function based on mode"""
    functions = {
        TimerMode.ORIGINAL_BUSY: original_busy_sleep,
        TimerMode.TIME_SLEEP: simple_time_sleep,
        TimerMode.PERF_COUNTER: perf_counter_busy_sleep,
        TimerMode.ADAPTIVE: adaptive_busy_sleep,
        TimerMode.STEPPER_OPTIMIZED: stepper_optimized_sleep,
        TimerMode.YIELD_FRIENDLY: yield_friendly_sleep,
        TimerMode.THREADING_BASED: None  # Special case
    }
    return functions[mode]

# ----------- existing function definitions -----------
def set_motor_coils(coil_1, coil_2, coil_3, coil_4):
    """
    Set state (HIGH/LOW) of all 4 coils of stepper motor by controlling the output pins of the motor driver (M1, M2, M3, M4).
    """
    lgpio.gpio_write(gpio0, M1, coil_1)
    lgpio.gpio_write(gpio0, M2, coil_2)
    lgpio.gpio_write(gpio0, M3, coil_3)
    lgpio.gpio_write(gpio0, M4, coil_4)

def stop_motor():
    """
    Set state of all 4 coils of stepper motor to LOW by controlling the output pins of the motor driver (M1, M2, M3, M4).
    Then disable all motor driver output pins (M1, M2, M3, M4).
    """
    # enable motor driver outputs
    lgpio.gpio_write(gpio0, D1, 1)
    lgpio.gpio_write(gpio0, D2, 1)
 
    # turn off all coils
    set_motor_coils(0, 0, 0, 0)
    time.sleep(STEP_TIME)  # Use simple sleep here
 
    # disable motor driver outputs
    lgpio.gpio_write(gpio0, D1, 0)
    lgpio.gpio_write(gpio0, D2, 0)
    print("\\nMotor stopped")

def measure_timing_precision(sleep_func, target_time, iterations=10):
    """Measure timing precision of a sleep function"""
    errors = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        sleep_func(target_time)
        actual_time = time.perf_counter() - start
        error = abs(actual_time - target_time) * 1000  # in ms
        errors.append(error)
    
    return {
        'avg_error': statistics.mean(errors),
        'max_error': max(errors),
        'min_error': min(errors),
        'std_dev': statistics.stdev(errors) if len(errors) > 1 else 0
    }

def run_timing_benchmark():
    """Run timing benchmark for all sleep functions"""
    print("\\n" + "="*60)
    print("TIMING PRECISION BENCHMARK")
    print("="*60)
    
    test_times = [0.0005, 0.0008, 0.001, 0.002, 0.003, 0.005, 0.01]
    
    for target_time in test_times:
        print(f"\\nTarget time: {target_time*1000:.1f}ms")
        print("-" * 50)
        
        for mode in TimerMode:
            if mode == TimerMode.THREADING_BASED:
                continue  # Skip threading mode in benchmark
                
            sleep_func = get_sleep_function(mode)
            stats = measure_timing_precision(sleep_func, target_time, 5)
            
            print(f"{mode.value:18}: Avg: {stats['avg_error']:.3f}ms, "
                  f"Max: {stats['max_error']:.3f}ms, "
                  f"StdDev: {stats['std_dev']:.3f}ms")

def display_menu():
    """Display the timer selection menu"""
    print("\\n" + "="*60)
    print("STEPPER MOTOR TIMER TEST")
    print("="*60)
    print("Current step time: {:.4f}s ({:.1f}ms)".format(STEP_TIME, STEP_TIME*1000))
    print("Current direction:", DIRECTION)
    print("\\nAvailable timer modes:")
    
    for i, mode in enumerate(TimerMode, 1):
        active = " (ACTIVE)" if mode == current_timer_mode else ""
        descriptions = {
            TimerMode.ORIGINAL_BUSY: "Original busy_sleep with time.time()",
            TimerMode.TIME_SLEEP: "Simple time.sleep() (for comparison)",
            TimerMode.PERF_COUNTER: "Improved with time.perf_counter()",
            TimerMode.ADAPTIVE: "Adaptive buffer adjustment",
            TimerMode.STEPPER_OPTIMIZED: "Optimized for stepper motor ranges",
            TimerMode.YIELD_FRIENDLY: "CPU-friendly with yields",
            TimerMode.THREADING_BASED: "Threading-based precise timing"
        }
        print(f"{i}. {descriptions[mode]}{active}")
    
    print(f"\\n{len(TimerMode)+1}. Run timing precision benchmark")
    print(f"{len(TimerMode)+2}. Change step time")
    print(f"{len(TimerMode)+3}. Toggle direction")
    print("0. Exit")
    print("\\nPress Ctrl+C during motor operation to return to menu")

def run_motor_with_timer(timer_mode):
    """Run the motor with the specified timer mode"""
    global timing_stats
    timing_stats = []
    
    print(f"\\nStarting motor with {timer_mode.value} timer...")
    print("Press Ctrl+C to stop and return to menu")
    
    if timer_mode == TimerMode.THREADING_BASED:
        # Use threading-based controller
        controller = ThreadingStepperController(gpio0)
        controller.step_interval = STEP_TIME
        controller.direction = DIRECTION
        
        try:
            controller.start()
            print("Threading-based controller started. Press Ctrl+C to stop...")
            while True:
                time.sleep(0.1)  # Just wait for interrupt
        except KeyboardInterrupt:
            controller.stop()
            print("\\nThreading controller stopped")
    else:
        # Use traditional loop with selected sleep function
        sleep_func = get_sleep_function(timer_mode)
        step_sequences = {
            0: [(0,1,0,1), (0,1,1,0), (1,0,1,0), (1,0,0,1)],
            1: [(1,0,0,1), (1,0,1,0), (0,1,1,0), (0,1,0,1)]
        }
        
        sequence = step_sequences[DIRECTION]
        step_count = 0
        
        try:
            while True:
                step_start = time.perf_counter()
                
                # Execute motor step
                coils = sequence[step_count % len(sequence)]
                set_motor_coils(*coils)
                
                # Precise timing
                sleep_func(STEP_TIME)
                
                # Record timing for analysis
                actual_step_time = time.perf_counter() - step_start
                timing_stats.append(actual_step_time)
                
                # Keep only last 1000 measurements
                if len(timing_stats) > 1000:
                    timing_stats.pop(0)
                
                step_count += 1
                
                # Print statistics every 100 steps
                if step_count % 100 == 0 and len(timing_stats) >= 10:
                    avg_time = statistics.mean(timing_stats[-100:]) * 1000
                    error = abs(avg_time - STEP_TIME*1000)
                    print(f"Steps: {step_count}, Avg time: {avg_time:.3f}ms, Error: {error:.3f}ms")
                    
        except KeyboardInterrupt:
            print(f"\\nMotor stopped after {step_count} steps")
            if timing_stats:
                avg_time = statistics.mean(timing_stats) * 1000
                error = abs(avg_time - STEP_TIME*1000)
                std_dev = statistics.stdev(timing_stats) * 1000 if len(timing_stats) > 1 else 0
                print(f"Final stats - Avg: {avg_time:.3f}ms, Error: {error:.3f}ms, StdDev: {std_dev:.3f}ms")

            """ # Fügen Sie diese Mikrostepping-Sequenzen zu Ihrem Code hinzu:  
                def get_microstep_sequence():     
                    #8-fach Mikrostepping Sequenz     
                    return [(1, 0, 0, 0),    # Vollschritt         
                            (1, 1, 0, 0),    # Zwischenschritt           
                            (0, 1, 0, 0),    # Vollschritt         
                            (0, 1, 1, 0),    # Zwischenschritt         
                            (0, 0, 1, 0),    # Vollschritt         
                            (0, 0, 1, 1),    # Zwischenschritt         
                            (0, 0, 0, 1),    # Vollschritt         
                            (1, 0, 0, 1),    # Zwischenschritt     
                            ]  
                def run_with_microstepping():     
                    #Motor mit Mikrostepping betreiben     
                    sequence = get_microstep_sequence()     
                    step_count = 0     # Verwenden Sie STEP_TIME / 2 für Mikrostepping     
                    micro_step_time = STEP_TIME / 2     
                    while True:         
                        coils = sequence[step_count % len(sequence)]         
                        set_motor_coils(*coils)         
                        stepper_optimized_sleep(micro_step_time)         
                        step_count += 1"""

# ----------- main code -----------
if __name__ == "__main__":
    # initialize lgpio
    gpio0 = lgpio.gpiochip_open(0)
    
    # initialize all pins to safe state
    lgpio.gpio_write(gpio0, M1, 0)
    lgpio.gpio_write(gpio0, M2, 0)
    lgpio.gpio_write(gpio0, M3, 0)
    lgpio.gpio_write(gpio0, M4, 0)
    lgpio.gpio_write(gpio0, D1, 0)
    lgpio.gpio_write(gpio0, D2, 0)
    
    # enable motor driver outputs
    lgpio.gpio_write(gpio0, D1, 1)
    lgpio.gpio_write(gpio0, D2, 1)
    
    threading_controller = None
    
    try:
        while True:
            display_menu()
            
            try:
                choice = input("\\nSelect option: ").strip()
                
                if choice == '0':
                    break
                elif choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(TimerMode):
                        current_timer_mode = list(TimerMode)[choice_num - 1]
                        run_motor_with_timer(current_timer_mode)
                    elif choice_num == len(TimerMode) + 1:
                        run_timing_benchmark()
                    elif choice_num == len(TimerMode) + 2:
                        new_time = input(f"Enter new step time in seconds (current: {STEP_TIME}): ")
                        try:
                            STEP_TIME = float(new_time)
                            if STEP_TIME <= 0:
                                raise ValueError
                            print(f"Step time changed to {STEP_TIME}s")
                        except ValueError:
                            print("Invalid step time!")
                    elif choice_num == len(TimerMode) + 3:
                        DIRECTION = 1 - DIRECTION
                        print(f"Direction changed to {DIRECTION}")
                    else:
                        print("Invalid option!")
                else:
                    print("Invalid input!")
                    
            except (ValueError, KeyboardInterrupt):
                print("\\nReturning to menu...")
                continue
                
    except KeyboardInterrupt:
        print("\\nShutting down...")
    finally:
        stop_motor()
        # Free GPIO pins
        lgpio.gpio_free(gpio0, M1)
        lgpio.gpio_free(gpio0, M2)
        lgpio.gpio_free(gpio0, M3)
        lgpio.gpio_free(gpio0, M4)
        lgpio.gpiochip_close(gpio0)
        print("Exit Python")