# Sensor Setup Guide - BH1750 & Ultrasonic

## Overview

This guide helps you set up and verify your specific sensors:
- **SCD40**: Temperature, Humidity, CO2 (I2C - GPIO 2/3)
- **BH1750**: Light intensity (I2C - GPIO 2/3)
- **Ultrasonic**: Water level (GPIO 23/24)

## Hardware Connections

### SCD40 Sensor (I2C - GPIO 2/3)
```
SCD40 Pin    → Raspberry Pi Pin
VDD          → 3.3V (Pin 1)
GND          → GND (Pin 9)
SDA          → GPIO 2 (Pin 3)
SCL          → GPIO 3 (Pin 5)
```

### BH1750 Light Sensor (I2C - GPIO 2/3)
```
BH1750 Pin   → Raspberry Pi Pin
VCC          → 3.3V (Pin 1)
GND          → GND (Pin 9)
SDA          → GPIO 2 (Pin 3)
SCL          → GPIO 3 (Pin 5)
ADDR         → GND (for address 0x23) or VCC (for address 0x5C)
```

### Ultrasonic Water Level Sensor (GPIO 23/24)
```
Ultrasonic Pin → Raspberry Pi Pin
VCC           → 5V (Pin 2)
GND           → GND (Pin 6)
TRIG          → GPIO 23 (Pin 16)
ECHO          → GPIO 24 (Pin 18)
```

## Step-by-Step Setup

### 1. Enable I2C Interface
```bash
sudo raspi-config
# Navigate to: Interface Options → I2C → Yes
sudo reboot
```

### 2. Install Dependencies
```bash
pip3 install smbus2 adafruit-circuitpython-scd4x gpiozero pymongo
```

### 3. Test I2C Communication
```bash
# Install I2C tools
sudo apt install i2c-tools

# Check I2C devices
i2cdetect -y 1

# Expected output should show:
# - SCD40 at address 0x62
# - BH1750 at address 0x23 (or 0x5C)
```

### 4. Test Individual Sensors

#### Test SCD40
```bash
python3 test_sensors_and_database.py
# This will test SCD40 automatically
```

#### Test BH1750
```python
#!/usr/bin/env python3
import smbus2
import time

# Try both addresses
for addr in [0x23, 0x5C]:
    try:
        bus = smbus2.SMBus(1)
        bus.write_byte(addr, 0x20)  # One-time high res mode
        time.sleep(0.2)
        data = bus.read_i2c_block_data(addr, 0x00, 2)
        light_level = (data[0] << 8 | data[1]) / 1.2
        print(f"BH1750 at 0x{addr:02X}: {light_level:.1f} lux")
        bus.close()
        break
    except:
        continue
```

#### Test Ultrasonic Sensor
```bash
python3 -c "
from gpiozero import DistanceSensor
import time

sensor = DistanceSensor(echo=24, trigger=23, max_distance=1)
for i in range(5):
    distance = sensor.distance * 100
    print(f'Distance: {distance:.1f} cm')
    time.sleep(1)
"
```

## Verification Steps

### 1. Run Comprehensive Test
```bash
python3 test_sensors_and_database.py
```

This will test:
- ✅ SCD40 sensor (Temperature, Humidity, CO2)
- ✅ BH1750 light sensor
- ✅ Ultrasonic water level sensor
- ✅ MongoDB connection
- ✅ Database save functionality
- ✅ Real sensor readings and database save

### 2. Monitor Database in Real-time
```bash
# Monitor real-time sensor data being saved
python3 monitor_database.py monitor

# Show recent readings
python3 monitor_database.py recent 10

# Show database statistics
python3 monitor_database.py stats
```

### 3. Start the Main Application
```bash
python3 app.py
```

Then open your browser to `http://localhost:5000` to see the web dashboard.

## Troubleshooting

### I2C Issues
```bash
# Check if I2C is enabled
ls /dev/i2c*

# Check I2C devices
i2cdetect -y 1

# If no devices found:
sudo raspi-config  # Enable I2C
sudo reboot
```

### BH1750 Not Found
- Check ADDR pin connection (GND = 0x23, VCC = 0x5C)
- Verify power supply (3.3V)
- Check SDA/SCL connections

### Ultrasonic Sensor Issues
- Verify TRIG/ECHO connections
- Check power supply (5V)
- Ensure proper grounding

### Database Issues
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB if not running
sudo systemctl start mongod

# Check MongoDB connection
mongo --eval "db.runCommand('ping')"
```

## Expected Output

### I2C Device Detection
```bash
$ i2cdetect -y 1
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- 23 -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- 62 -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```
- `23`: BH1750 light sensor
- `62`: SCD40 sensor

### Sensor Test Output
```
✅ SCD40 Readings:
   Temperature: 22.5°C
   Humidity: 65.2%
   CO2: 800 ppm

✅ BH1750 Light Reading: 450.2 lux

✅ Water Level Reading:
   Distance: 25.3 cm
```

### Database Monitor Output
```
📊 Reading at 14:30:25:
   🌡️  Temperature: 22.5°C
   💧 Humidity: 65.2%
   🌬️  CO2: 800 ppm
   💡 Light: 450 lux
   💧 Water: 75.0%
   📱 Device: raspberry-pi-01
```

## Success Indicators

✅ **Sensors Working**: You see real sensor readings in the test output

✅ **Database Saving**: The monitor shows new readings being saved every 10 seconds

✅ **Web Dashboard**: You can see real-time data at `http://localhost:5000`

✅ **MongoDB Atlas**: Data syncs to Atlas when internet is available

## Next Steps

1. **Verify all sensors work**: Run `python3 test_sensors_and_database.py`
2. **Monitor database**: Run `python3 monitor_database.py monitor`
3. **Start application**: Run `python3 app.py`
4. **Access dashboard**: Open `http://localhost:5000`

Your Environmental Control System is now ready to monitor and control your environment!