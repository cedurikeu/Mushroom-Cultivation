#!/usr/bin/env python3
"""
Individual Sensor Test Script
Run each test separately to verify your hardware connections
"""

import time
import sys

def test_scd40_i2c():
    """Test SCD40 sensor on I2C (GPIO 2/3)"""
    print("🔍 Testing SCD40 I2C Sensor (GPIO 2/3)...")
    print("   Make sure SCD40 is connected:")
    print("   - VDD → 3.3V (Pin 1)")
    print("   - GND → GND (Pin 9)")
    print("   - SDA → GPIO 2 (Pin 3)")
    print("   - SCL → GPIO 3 (Pin 5)")
    print()
    
    try:
        import board
        import busio
        import adafruit_scd4x
        
        # Create I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        print("✅ I2C bus created")
        
        # Create SCD40 sensor
        scd40 = adafruit_scd4x.SCD4X(i2c)
        print("✅ SCD40 sensor initialized")
        
        # Start periodic measurement
        scd40.start_periodic_measurement()
        print("✅ Started periodic measurement")
        
        # Wait for first reading
        print("⏳ Waiting for first reading (5 seconds)...")
        time.sleep(5)
        
        if scd40.data_ready:
            temp = scd40.temperature
            humidity = scd40.relative_humidity
            co2 = scd40.CO2
            
            print(f"✅ SCD40 Readings:")
            print(f"   Temperature: {temp:.1f}°C")
            print(f"   Humidity: {humidity:.1f}%")
            print(f"   CO2: {co2} ppm")
            return True
        else:
            print("❌ SCD40 data not ready")
            return False
            
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        print("   Install with: pip install adafruit-circuitpython-scd4x")
        return False
    except Exception as e:
        print(f"❌ SCD40 error: {e}")
        print("   Check connections and I2C is enabled")
        return False

def test_light_sensor_spi():
    """Test light sensor via MCP3008 ADC (SPI - GPIO 8,9,10,11)"""
    print("🔍 Testing Light Sensor via MCP3008 (SPI)...")
    print("   Make sure MCP3008 is connected:")
    print("   - VDD/VREF → 3.3V (Pin 1)")
    print("   - AGND/DGND → GND (Pin 9)")
    print("   - CLK → GPIO 11 (Pin 23)")
    print("   - DOUT → GPIO 9 (Pin 21)")
    print("   - DIN → GPIO 10 (Pin 19)")
    print("   - CS → GPIO 8 (Pin 24)")
    print("   - CH0 → Photoresistor")
    print()
    
    try:
        import board
        import busio
        import adafruit_mcp3xxx.mcp3008 as MCP
        from adafruit_mcp3xxx.analog_in import AnalogIn
        
        # Create SPI bus
        spi = busio.SPI(clock=board.D11, MISO=board.D9, MOSI=board.D10)
        print("✅ SPI bus created")
        
        # Create chip select
        cs = board.D8
        print("✅ Chip select configured")
        
        # Create MCP3008 object
        mcp = MCP.MCP3008(spi, cs)
        print("✅ MCP3008 initialized")
        
        # Create analog input channel
        light_sensor = AnalogIn(mcp, MCP.P0)
        print("✅ Light sensor channel created")
        
        # Read light sensor
        light_value = light_sensor.value
        light_voltage = light_sensor.voltage
        
        print(f"✅ Light Sensor Readings:")
        print(f"   Raw Value: {light_value}")
        print(f"   Voltage: {light_voltage:.3f}V")
        
        # Test with different light conditions
        print("   💡 Cover the photoresistor to test...")
        time.sleep(3)
        
        light_value2 = light_sensor.value
        light_voltage2 = light_sensor.voltage
        
        print(f"   New Raw Value: {light_value2}")
        print(f"   New Voltage: {light_voltage2:.3f}V")
        
        if abs(light_value - light_value2) > 100:
            print("   ✅ Light sensor responding to changes")
        else:
            print("   ⚠️ Light sensor not responding to changes")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        print("   Install with: pip install adafruit-circuitpython-mcp3xxx")
        return False
    except Exception as e:
        print(f"❌ Light sensor error: {e}")
        print("   Check connections and SPI is enabled")
        return False

def test_water_sensor_gpio():
    """Test ultrasonic water level sensor (GPIO 23/24)"""
    print("🔍 Testing Ultrasonic Water Level Sensor (GPIO 23/24)...")
    print("   Make sure ultrasonic sensor is connected:")
    print("   - VCC → 5V (Pin 2)")
    print("   - GND → GND (Pin 6)")
    print("   - TRIG → GPIO 23 (Pin 16)")
    print("   - ECHO → GPIO 24 (Pin 18)")
    print()
    
    try:
        from gpiozero import DistanceSensor
        
        # Create distance sensor
        sensor = DistanceSensor(echo=24, trigger=23, max_distance=1)
        print("✅ Ultrasonic sensor initialized")
        
        # Read distance
        distance = sensor.distance
        distance_cm = distance * 100
        
        print(f"✅ Water Level Reading:")
        print(f"   Distance: {distance_cm:.1f} cm")
        
        # Test with different distances
        print("   💧 Move your hand in front of the sensor to test...")
        time.sleep(3)
        
        distance2 = sensor.distance * 100
        print(f"   New Distance: {distance2:.1f} cm")
        
        if abs(distance_cm - distance2) > 5:
            print("   ✅ Ultrasonic sensor responding to changes")
        else:
            print("   ⚠️ Ultrasonic sensor not responding to changes")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        print("   Install with: pip install gpiozero")
        return False
    except Exception as e:
        print(f"❌ Water sensor error: {e}")
        print("   Check connections and GPIO permissions")
        return False

def test_control_devices():
    """Test control devices (GPIO 18,19,20,21)"""
    print("🔍 Testing Control Devices...")
    print("   Make sure relay module is connected:")
    print("   - VCC → 5V")
    print("   - GND → GND")
    print("   - IN1 → GPIO 18 (Pin 12) - Fogger")
    print("   - IN2 → GPIO 19 (Pin 35) - Fan")
    print("   - IN3 → GPIO 20 (Pin 38) - Heater")
    print("   - IN4 → GPIO 21 (Pin 40) - Lights")
    print()
    
    try:
        from gpiozero import OutputDevice
        
        # Create output devices
        fogger = OutputDevice(18)
        fan = OutputDevice(19)
        heater = OutputDevice(20)
        lights = OutputDevice(21)
        
        print("✅ Control devices initialized")
        
        # Test each device
        devices = [
            (fogger, "Fogger", 18),
            (fan, "Fan", 19),
            (heater, "Heater", 20),
            (lights, "Lights", 21)
        ]
        
        for device, name, pin in devices:
            print(f"   Testing {name} (GPIO {pin})...")
            device.on()
            time.sleep(1)
            device.off()
            print(f"   ✅ {name} tested")
            time.sleep(0.5)
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        print("   Install with: pip install gpiozero")
        return False
    except Exception as e:
        print(f"❌ Control devices error: {e}")
        print("   Check connections and GPIO permissions")
        return False

def test_status_leds():
    """Test status LEDs (GPIO 13,16,26)"""
    print("🔍 Testing Status LEDs...")
    print("   Make sure LEDs are connected with 220Ω resistors:")
    print("   - Green LED → GPIO 26 (Pin 37) → 220Ω → GND")
    print("   - Red LED → GPIO 16 (Pin 36) → 220Ω → GND")
    print("   - Blue LED → GPIO 13 (Pin 33) → 220Ω → GND")
    print()
    
    try:
        from gpiozero import LED
        
        # Create LED objects
        green_led = LED(26)
        red_led = LED(16)
        blue_led = LED(13)
        
        print("✅ Status LEDs initialized")
        
        # Test each LED
        leds = [
            (green_led, "Green", 26),
            (red_led, "Red", 16),
            (blue_led, "Blue", 13)
        ]
        
        for led, name, pin in leds:
            print(f"   Testing {name} LED (GPIO {pin})...")
            led.on()
            time.sleep(1)
            led.off()
            print(f"   ✅ {name} LED tested")
            time.sleep(0.5)
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        print("   Install with: pip install gpiozero")
        return False
    except Exception as e:
        print(f"❌ Status LEDs error: {e}")
        print("   Check connections and GPIO permissions")
        return False

def main():
    """Main test function"""
    print("🧪 Individual Sensor Test Script")
    print("=" * 50)
    print("Run each test to verify your hardware connections")
    print()
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "scd40":
            test_scd40_i2c()
        elif test_name == "light":
            test_light_sensor_spi()
        elif test_name == "water":
            test_water_sensor_gpio()
        elif test_name == "control":
            test_control_devices()
        elif test_name == "leds":
            test_status_leds()
        else:
            print("❌ Unknown test. Available tests:")
            print("   python3 test_sensors.py scd40")
            print("   python3 test_sensors.py light")
            print("   python3 test_sensors.py water")
            print("   python3 test_sensors.py control")
            print("   python3 test_sensors.py leds")
    else:
        print("Usage: python3 test_sensors.py [test_name]")
        print()
        print("Available tests:")
        print("  scd40   - Test SCD40 I2C sensor (GPIO 2/3)")
        print("  light   - Test light sensor via MCP3008 (SPI)")
        print("  water   - Test ultrasonic water sensor (GPIO 23/24)")
        print("  control - Test control devices (GPIO 18,19,20,21)")
        print("  leds    - Test status LEDs (GPIO 13,16,26)")
        print()
        print("Example: python3 test_sensors.py scd40")

if __name__ == '__main__':
    main()