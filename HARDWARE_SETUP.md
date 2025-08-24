# Hardware Setup Guide - Environmental Control System

## Overview

This guide provides step-by-step instructions for connecting all sensors and control devices to your Raspberry Pi for the Environmental Control System.

## Required Components

### Sensors
- **SCD40**: Temperature, Humidity, and CO2 sensor (I2C)
- **Photoresistor**: Light intensity sensor (via MCP3008 ADC)
- **Ultrasonic Sensor**: Water level sensor (GPIO)

### Control Devices
- **Relay Module**: For fogger, fan, and lights control
- **12V Fogger/Mister**: Ultrasonic humidifier
- **12V Exhaust Fan**: Computer fan or similar
- **LED Grow Lights**: Full spectrum grow lights

### Supporting Components
- **MCP3008 ADC**: 8-channel analog-to-digital converter
- **Breadboard**: For prototyping and testing
- **Jumper Wires**: Male-to-female and male-to-male
- **Power Supply**: 12V for fogger, fan, and lights
- **Resistors**: 10kΩ for photoresistor voltage divider

## Pin Configuration

```python
GPIO_CONFIG = {
    # SCD40 I2C Pins (Physical pins)
    'SCD40_SDA_PIN': 2,          # GPIO 2 (Physical pin 3)
    'SCD40_SCL_PIN': 3,          # GPIO 3 (Physical pin 5)
    
    # MCP3008 ADC SPI Pins
    'SPI_CLK': 11,               # GPIO 11 (Physical pin 23)
    'SPI_MISO': 9,               # GPIO 9 (Physical pin 21)
    'SPI_MOSI': 10,              # GPIO 10 (Physical pin 19)
    'SPI_CS': 8,                 # GPIO 8 (Physical pin 24)
    
    # Ultrasonic Water Level Sensor
    'ULTRASONIC_TRIG_PIN': 23,   # GPIO 23 (Physical pin 16)
    'ULTRASONIC_ECHO_PIN': 24,   # GPIO 24 (Physical pin 18)
    
    # Control Pins
    'FOGGER_PIN': 18,            # GPIO 18 (Physical pin 12)
    'FAN_PIN': 19,               # GPIO 19 (Physical pin 35)
    'HEATER_PIN': 20,            # GPIO 20 (Physical pin 38)
    'LED_LIGHTS_PIN': 21,        # GPIO 21 (Physical pin 40)
    
    # Status LED Pins
    'STATUS_LED_GREEN': 26,      # GPIO 26 (Physical pin 37)
    'STATUS_LED_RED': 16,        # GPIO 16 (Physical pin 36)
    'STATUS_LED_BLUE': 13,       # GPIO 13 (Physical pin 33)
}
```

## Step-by-Step Setup

### Step 1: Enable I2C and SPI Interfaces

1. **Open Raspberry Pi Configuration**:
   ```bash
   sudo raspi-config
   ```

2. **Enable I2C**:
   - Navigate to `Interface Options` → `I2C`
   - Select `Yes` to enable I2C
   - Select `Yes` to load I2C kernel module

3. **Enable SPI**:
   - Navigate to `Interface Options` → `SPI`
   - Select `Yes` to enable SPI
   - Select `Yes` to load SPI kernel module

4. **Reboot**:
   ```bash
   sudo reboot
   ```

5. **Verify I2C and SPI**:
   ```bash
   # Check I2C
   ls /dev/i2c*
   i2cdetect -y 1
   
   # Check SPI
   ls /dev/spidev*
   ```

### Step 2: SCD40 Sensor Setup (I2C - GPIO 2/3)

The SCD40 is a high-precision CO2, temperature, and humidity sensor.

#### Hardware Connection

| SCD40 Pin | Raspberry Pi Pin | Description |
|-----------|------------------|-------------|
| VDD       | 3.3V (Pin 1)     | Power supply |
| GND       | GND (Pin 9)      | Ground |
| SDA       | GPIO 2 (Pin 3)   | I2C Data |
| SCL       | GPIO 3 (Pin 5)   | I2C Clock |

#### Connection Diagram
```
SCD40 Sensor
┌─────────┐
│ VDD ────┼─── 3.3V (Pin 1)
│ GND ────┼─── GND (Pin 9)
│ SDA ────┼─── GPIO 2 (Pin 3)
│ SCL ────┼─── GPIO 3 (Pin 5)
└─────────┘
```

#### Testing SCD40
```bash
# Install I2C tools
sudo apt install i2c-tools

# Detect I2C devices
i2cdetect -y 1

# Expected output should show device at address 0x62
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 70: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

### Step 3: MCP3008 ADC Setup (SPI - GPIO 8,9,10,11)

The MCP3008 is an 8-channel ADC that converts analog signals to digital for the light sensor.

#### Hardware Connection

| MCP3008 Pin | Raspberry Pi Pin | Description |
|-------------|------------------|-------------|
| VDD         | 3.3V (Pin 1)     | Power supply |
| VREF        | 3.3V (Pin 1)     | Reference voltage |
| AGND        | GND (Pin 9)      | Analog ground |
| DGND        | GND (Pin 9)      | Digital ground |
| CLK         | GPIO 11 (Pin 23) | SPI Clock |
| DOUT        | GPIO 9 (Pin 21)  | SPI MISO |
| DIN         | GPIO 10 (Pin 19) | SPI MOSI |
| CS/SHDN     | GPIO 8 (Pin 24)  | SPI Chip Select |
| CH0         | Photoresistor    | Light sensor input |

#### Connection Diagram
```
MCP3008 ADC
┌─────────────┐
│ VDD ────────┼─── 3.3V (Pin 1)
│ VREF ───────┼─── 3.3V (Pin 1)
│ AGND ───────┼─── GND (Pin 9)
│ DGND ───────┼─── GND (Pin 9)
│ CLK ────────┼─── GPIO 11 (Pin 23)
│ DOUT ───────┼─── GPIO 9 (Pin 21)
│ DIN ────────┼─── GPIO 10 (Pin 19)
│ CS/SHDN ────┼─── GPIO 8 (Pin 24)
│ CH0 ────────┼─── Photoresistor
└─────────────┘
```

### Step 4: Light Sensor Setup (Photoresistor via MCP3008)

#### Hardware Connection

| Component | Connection | Description |
|-----------|------------|-------------|
| Photoresistor | MCP3008 CH0 | Light sensor input |
| 10kΩ Resistor | Voltage divider | Pull-down resistor |
| 3.3V | Power supply | Sensor power |

#### Circuit Diagram
```
3.3V ──── Photoresistor ──── MCP3008 CH0 ──── 10kΩ Resistor ──── GND
```

#### Testing Light Sensor
```python
# Test script for light sensor
import time
import board
import busio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# Create SPI bus
spi = busio.SPI(clock=board.D11, MISO=board.D9, MOSI=board.D10)

# Create chip select
cs = board.D8

# Create MCP3008 object
mcp = MCP.MCP3008(spi, cs)

# Create analog input channel
light_sensor = AnalogIn(mcp, MCP.P0)

while True:
    # Read light sensor
    light_value = light_sensor.value
    light_voltage = light_sensor.voltage
    
    print(f"Light Value: {light_value}, Voltage: {light_voltage:.3f}V")
    time.sleep(1)
```

### Step 5: Water Level Sensor Setup (Ultrasonic - GPIO 23/24)

#### Hardware Connection

| Ultrasonic Pin | Raspberry Pi Pin | Description |
|----------------|------------------|-------------|
| VCC           | 5V (Pin 2)       | Power supply |
| GND           | GND (Pin 6)      | Ground |
| TRIG          | GPIO 23 (Pin 16) | Trigger signal |
| ECHO          | GPIO 24 (Pin 18) | Echo signal |

#### Connection Diagram
```
Ultrasonic Sensor (HC-SR04)
┌─────────────┐
│ VCC ────────┼─── 5V (Pin 2)
│ GND ────────┼─── GND (Pin 6)
│ TRIG ───────┼─── GPIO 23 (Pin 16)
│ ECHO ───────┼─── GPIO 24 (Pin 18)
└─────────────┘
```

#### Testing Ultrasonic Sensor
```python
# Test script for ultrasonic sensor
from gpiozero import DistanceSensor
import time

# Create distance sensor
sensor = DistanceSensor(echo=24, trigger=23, max_distance=1)

while True:
    # Read distance
    distance = sensor.distance
    distance_cm = distance * 100
    
    print(f"Distance: {distance_cm:.2f} cm")
    time.sleep(1)
```

### Step 6: Control Devices Setup

#### Relay Module Connection

| Relay Channel | Raspberry Pi Pin | Device |
|---------------|------------------|--------|
| Channel 1     | GPIO 18 (Pin 12) | Fogger |
| Channel 2     | GPIO 19 (Pin 35) | Fan |
| Channel 3     | GPIO 20 (Pin 38) | Heater |
| Channel 4     | GPIO 21 (Pin 40) | LED Lights |

#### Power Supply Setup
```
12V Power Supply
├── Relay Module (5V logic, 12V switching)
├── 12V Fogger/Mister
├── 12V Exhaust Fan
└── 12V LED Grow Lights
```

#### Testing Control Devices
```python
# Test script for control devices
from gpiozero import OutputDevice
import time

# Create output devices
fogger = OutputDevice(18)
fan = OutputDevice(19)
heater = OutputDevice(20)
lights = OutputDevice(21)

# Test each device
devices = [fogger, fan, heater, lights]
names = ['Fogger', 'Fan', 'Heater', 'Lights']

for device, name in zip(devices, names):
    print(f"Testing {name}...")
    device.on()
    time.sleep(2)
    device.off()
    time.sleep(1)
```

### Step 7: Status LEDs Setup

#### Hardware Connection

| LED | Raspberry Pi Pin | Description |
|-----|------------------|-------------|
| Green | GPIO 26 (Pin 37) | System OK |
| Red   | GPIO 16 (Pin 36) | System Error |
| Blue  | GPIO 13 (Pin 33) | WiFi Connected |

#### Connection Diagram
```
Status LEDs (with 220Ω resistors)
┌─────────────┐
│ Green LED ──┼─── GPIO 26 (Pin 37) ──── 220Ω ──── GND
│ Red LED ────┼─── GPIO 16 (Pin 36) ──── 220Ω ──── GND
│ Blue LED ───┼─── GPIO 13 (Pin 33) ──── 220Ω ──── GND
└─────────────┘
```

## Complete Wiring Diagram

```
Raspberry Pi 4
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  3.3V ──── SCD40 VDD ──── MCP3008 VDD/VREF             │
│  5V ────── Ultrasonic VCC ──── Relay Module VCC        │
│  GND ───── SCD40 GND ──── MCP3008 AGND/DGND            │
│           └─── Ultrasonic GND ──── Relay Module GND    │
│                                                         │
│  GPIO 2 ──── SCD40 SDA (I2C Data)                      │
│  GPIO 3 ──── SCD40 SCL (I2C Clock)                     │
│                                                         │
│  GPIO 8 ──── MCP3008 CS (SPI Chip Select)              │
│  GPIO 9 ──── MCP3008 DOUT (SPI MISO)                   │
│  GPIO 10 ─── MCP3008 DIN (SPI MOSI)                    │
│  GPIO 11 ─── MCP3008 CLK (SPI Clock)                   │
│                                                         │
│  GPIO 16 ─── Red LED ──── 220Ω ──── GND                │
│  GPIO 18 ─── Relay 1 (Fogger)                          │
│  GPIO 19 ─── Relay 2 (Fan)                             │
│  GPIO 20 ─── Relay 3 (Heater)                          │
│  GPIO 21 ─── Relay 4 (LED Lights)                      │
│  GPIO 23 ─── Ultrasonic TRIG                           │
│  GPIO 24 ─── Ultrasonic ECHO                           │
│  GPIO 26 ─── Green LED ──── 220Ω ──── GND              │
│  GPIO 13 ─── Blue LED ──── 220Ω ──── GND               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Testing and Verification

### 1. Test I2C Communication
```bash
# Check I2C devices
i2cdetect -y 1

# Expected: Device at address 0x62 (SCD40)
```

### 2. Test SPI Communication
```bash
# Check SPI devices
ls /dev/spidev*

# Expected: /dev/spidev0.0
```

### 3. Test All Sensors
```python
#!/usr/bin/env python3
"""
Complete sensor test script
"""

import time
import board
import busio
import adafruit_scd4x
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from gpiozero import DistanceSensor, LED

def test_scd40():
    """Test SCD40 sensor"""
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        scd40 = adafruit_scd4x.SCD4X(i2c)
        scd40.start_periodic_measurement()
        
        print("✅ SCD40 initialized")
        
        # Wait for first reading
        time.sleep(5)
        
        if scd40.data_ready:
            temp = scd40.temperature
            humidity = scd40.relative_humidity
            co2 = scd40.CO2
            
            print(f"📡 SCD40: T={temp:.1f}°C, H={humidity:.1f}%, CO2={co2}ppm")
            return True
        else:
            print("❌ SCD40 data not ready")
            return False
            
    except Exception as e:
        print(f"❌ SCD40 error: {e}")
        return False

def test_light_sensor():
    """Test light sensor via MCP3008"""
    try:
        spi = busio.SPI(clock=board.D11, MISO=board.D9, MOSI=board.D10)
        cs = board.D8
        mcp = MCP.MCP3008(spi, cs)
        light_sensor = AnalogIn(mcp, MCP.P0)
        
        light_value = light_sensor.value
        light_voltage = light_sensor.voltage
        
        print(f"💡 Light: {light_value}, {light_voltage:.3f}V")
        return True
        
    except Exception as e:
        print(f"❌ Light sensor error: {e}")
        return False

def test_water_sensor():
    """Test ultrasonic water level sensor"""
    try:
        sensor = DistanceSensor(echo=24, trigger=23, max_distance=1)
        distance = sensor.distance * 100
        
        print(f"💧 Water level: {distance:.1f}cm")
        return True
        
    except Exception as e:
        print(f"❌ Water sensor error: {e}")
        return False

def test_control_devices():
    """Test control devices"""
    try:
        from gpiozero import OutputDevice
        
        fogger = OutputDevice(18)
        fan = OutputDevice(19)
        lights = OutputDevice(21)
        
        print("🎛️ Testing control devices...")
        
        # Test each device briefly
        for device, name in [(fogger, "Fogger"), (fan, "Fan"), (lights, "Lights")]:
            device.on()
            time.sleep(0.5)
            device.off()
            print(f"✅ {name} tested")
        
        return True
        
    except Exception as e:
        print(f"❌ Control devices error: {e}")
        return False

def test_status_leds():
    """Test status LEDs"""
    try:
        green_led = LED(26)
        red_led = LED(16)
        blue_led = LED(13)
        
        print("💡 Testing status LEDs...")
        
        for led, name in [(green_led, "Green"), (red_led, "Red"), (blue_led, "Blue")]:
            led.on()
            time.sleep(0.5)
            led.off()
            print(f"✅ {name} LED tested")
        
        return True
        
    except Exception as e:
        print(f"❌ Status LEDs error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing all sensors and devices...")
    print("=" * 50)
    
    tests = [
        ("SCD40 Sensor", test_scd40),
        ("Light Sensor", test_light_sensor),
        ("Water Sensor", test_water_sensor),
        ("Control Devices", test_control_devices),
        ("Status LEDs", test_status_leds)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Hardware setup is complete.")
    else:
        print("❌ Some tests failed. Check connections and try again.")

if __name__ == '__main__':
    main()
```

## Troubleshooting

### Common Issues

1. **I2C Device Not Found**:
   - Check I2C is enabled: `sudo raspi-config`
   - Verify connections: `i2cdetect -y 1`
   - Check power supply to SCD40

2. **SPI Communication Error**:
   - Check SPI is enabled: `sudo raspi-config`
   - Verify MCP3008 connections
   - Check voltage levels (3.3V)

3. **Ultrasonic Sensor Issues**:
   - Verify TRIG and ECHO connections
   - Check power supply (5V)
   - Ensure proper grounding

4. **Control Devices Not Working**:
   - Check relay module power supply
   - Verify GPIO connections
   - Test with simple GPIO test script

### GPIO Permissions
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Reboot to apply changes
sudo reboot
```

## Next Steps

1. **Run the test script** to verify all sensors work
2. **Install MongoDB** using the setup script
3. **Configure the environment** file
4. **Start the Environmental Control System**

Your hardware setup is now complete and ready for the Environmental Control System!