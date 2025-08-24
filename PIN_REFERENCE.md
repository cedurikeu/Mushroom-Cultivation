# Pin Reference Card - Environmental Control System

## Quick Reference

### SCD40 Sensor (I2C - GPIO 2/3)
```
SCD40 Pin    → Raspberry Pi Pin
VDD          → 3.3V (Pin 1)
GND          → GND (Pin 9)
SDA          → GPIO 2 (Pin 3)
SCL          → GPIO 3 (Pin 5)
```

### MCP3008 ADC (SPI - GPIO 8,9,10,11)
```
MCP3008 Pin  → Raspberry Pi Pin
VDD/VREF     → 3.3V (Pin 1)
AGND/DGND    → GND (Pin 9)
CLK          → GPIO 11 (Pin 23)
DOUT         → GPIO 9 (Pin 21)
DIN          → GPIO 10 (Pin 19)
CS/SHDN      → GPIO 8 (Pin 24)
CH0          → Photoresistor
```

### Light Sensor Circuit
```
3.3V ──── Photoresistor ──── MCP3008 CH0 ──── 10kΩ Resistor ──── GND
```

### Ultrasonic Water Sensor (GPIO 23/24)
```
Ultrasonic Pin → Raspberry Pi Pin
VCC           → 5V (Pin 2)
GND           → GND (Pin 6)
TRIG          → GPIO 23 (Pin 16)
ECHO          → GPIO 24 (Pin 18)
```

### Control Devices (GPIO 18,19,20,21)
```
Relay Channel → Raspberry Pi Pin → Device
Channel 1     → GPIO 18 (Pin 12) → Fogger
Channel 2     → GPIO 19 (Pin 35) → Fan
Channel 3     → GPIO 20 (Pin 38) → Heater
Channel 4     → GPIO 21 (Pin 40) → LED Lights
```

### Status LEDs (GPIO 13,16,26)
```
LED Color → Raspberry Pi Pin → Resistor → GND
Green     → GPIO 26 (Pin 37) → 220Ω    → GND
Red       → GPIO 16 (Pin 36) → 220Ω    → GND
Blue      → GPIO 13 (Pin 33) → 220Ω    → GND
```

## Complete Pin Map

| Raspberry Pi Pin | GPIO | Function | Device |
|------------------|------|----------|--------|
| Pin 1  | 3.3V | Power | SCD40 VDD, MCP3008 VDD/VREF |
| Pin 2  | 5V | Power | Ultrasonic VCC, Relay Module VCC |
| Pin 3  | GPIO 2 | I2C SDA | SCD40 SDA |
| Pin 5  | GPIO 3 | I2C SCL | SCD40 SCL |
| Pin 6  | GND | Ground | Ultrasonic GND |
| Pin 9  | GND | Ground | SCD40 GND, MCP3008 AGND/DGND |
| Pin 12 | GPIO 18 | Output | Relay 1 (Fogger) |
| Pin 16 | GPIO 23 | Output | Ultrasonic TRIG |
| Pin 18 | GPIO 24 | Input | Ultrasonic ECHO |
| Pin 19 | GPIO 10 | SPI MOSI | MCP3008 DIN |
| Pin 21 | GPIO 9 | SPI MISO | MCP3008 DOUT |
| Pin 23 | GPIO 11 | SPI CLK | MCP3008 CLK |
| Pin 24 | GPIO 8 | SPI CS | MCP3008 CS |
| Pin 33 | GPIO 13 | Output | Blue LED |
| Pin 35 | GPIO 19 | Output | Relay 2 (Fan) |
| Pin 36 | GPIO 16 | Output | Red LED |
| Pin 37 | GPIO 26 | Output | Green LED |
| Pin 38 | GPIO 20 | Output | Relay 3 (Heater) |
| Pin 40 | GPIO 21 | Output | Relay 4 (Lights) |

## Testing Commands

### Enable Interfaces
```bash
sudo raspi-config
# Interface Options → I2C → Yes
# Interface Options → SPI → Yes
sudo reboot
```

### Test I2C
```bash
sudo apt install i2c-tools
i2cdetect -y 1
# Should show device at 0x62
```

### Test SPI
```bash
ls /dev/spidev*
# Should show /dev/spidev0.0
```

### Test Individual Sensors
```bash
python3 test_sensors.py scd40    # Test SCD40
python3 test_sensors.py light    # Test light sensor
python3 test_sensors.py water    # Test water sensor
python3 test_sensors.py control  # Test control devices
python3 test_sensors.py leds     # Test status LEDs
```

## Troubleshooting

### I2C Issues
- Check I2C is enabled: `sudo raspi-config`
- Verify connections: `i2cdetect -y 1`
- Check power supply (3.3V)

### SPI Issues
- Check SPI is enabled: `sudo raspi-config`
- Verify MCP3008 connections
- Check voltage levels (3.3V)

### GPIO Issues
- Add user to gpio group: `sudo usermod -a -G gpio $USER`
- Reboot: `sudo reboot`
- Check permissions: `ls -l /dev/gpiomem`

### Power Issues
- Use separate 12V power supply for relays
- Ensure proper grounding
- Check voltage levels (3.3V for sensors, 5V for relays)

## Quick Setup Checklist

- [ ] Enable I2C and SPI in raspi-config
- [ ] Connect SCD40 to GPIO 2/3 (I2C)
- [ ] Connect MCP3008 to GPIO 8,9,10,11 (SPI)
- [ ] Connect photoresistor to MCP3008 CH0
- [ ] Connect ultrasonic sensor to GPIO 23/24
- [ ] Connect relay module to GPIO 18,19,20,21
- [ ] Connect status LEDs to GPIO 13,16,26
- [ ] Test each sensor individually
- [ ] Install MongoDB: `./setup_mongodb.sh`
- [ ] Start system: `python3 app.py`