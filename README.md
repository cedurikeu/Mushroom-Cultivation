# 🌱 Environmental Control System

A comprehensive web-based environmental monitoring and control system using Raspberry Pi with MongoDB-only architecture for reliable offline operation.

## Features

### 🌡️ Environmental Monitoring
- **Temperature & Humidity**: DHT22 sensor for precise readings
- **CO2 Levels**: MQ-135 or similar sensor for air quality monitoring
- **Light Intensity**: Photoresistor for grow light management
- **Real-time Dashboard**: Live updates via WebSocket

### 🎛️ Automated Controls
- **Fogger System**: Automatic misting based on humidity levels
- **Exhaust Fan**: Air circulation control
- **LED Grow Lights**: Automated lighting schedule
- **Manual Override**: Web-based control interface

### 📊 Data Management
- **MongoDB-Only Architecture**: Local MongoDB with Atlas cloud sync
- **Offline Operation**: Continues working when internet is down
- **Automatic Sync**: Data syncs to Atlas when internet is restored
- **Historical Data**: Charts and tables for trend analysis
- **Data Export**: Easy access to sensor readings

### 🌱 Environmental Control
- **Real-time Monitoring**: Live sensor data and control status
- **Automated Controls**: Smart environmental adjustments
- **Manual Override**: Web-based control interface
- **Status Monitoring**: Visual indicators for system health

## Hardware Requirements

### Raspberry Pi Setup
- Raspberry Pi 4 (recommended) or Pi 3B+
- MicroSD card (32GB+)
- Power supply (5V 3A)

### Sensors
- **DHT22**: Temperature and humidity sensor
- **MCP3008**: 8-channel ADC for analog sensors
- **Photoresistor**: Light intensity measurement
- **MQ-135**: CO2/air quality sensor (or similar)

### Control Hardware
- **Relay Module**: For fogger, fan, and light control
- **12V Fogger/Mister**: Ultrasonic or similar
- **Exhaust Fan**: 12V computer fan or similar
- **LED Grow Lights**: Full spectrum recommended
- **Status LEDs**: Visual system status indicators

### GPIO Pin Configuration
```python
GPIO_CONFIG = {
    # Sensors
    'DHT22_PIN': 4,              # Temperature & Humidity
    'LIGHT_SENSOR_PIN': 0,       # ADC Channel 0
    'CO2_SENSOR_PIN': 1,         # ADC Channel 1
    
    # Controls
    'FOGGER_PIN': 18,            # Fogger relay
    'FAN_PIN': 19,               # Fan control
    'LED_LIGHTS_PIN': 21,        # Grow lights
    
    # Status LEDs
    'STATUS_LED_GREEN': 26,      # System OK
    'STATUS_LED_RED': 16,        # Error
    'STATUS_LED_BLUE': 13,       # WiFi Connected
}
```

## Installation

### 1. System Prerequisites
```bash
# Update Raspberry Pi OS
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-venv git -y

# Install system libraries for GPIO
sudo apt install python3-dev python3-gpiozero -y
```

### 2. Clone Repository
```bash
git clone <your-repo-url>
cd environmental-control-system
```

### 3. Install MongoDB
```bash
# Run the MongoDB setup script
./setup_mongodb.sh
```

This will install and configure MongoDB locally on your Raspberry Pi.

### 4. Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 5. Configuration
```bash
# Create environment file
cp .env.example .env

# Edit configuration
nano .env
```

Update `.env` with your settings:
- `SECRET_KEY`: Your secret key
- `DASHBOARD_PASSWORD`: Dashboard login password
- `MONGODB_URI`: MongoDB Atlas connection string (optional)

### 6. Hardware Connections
Connect sensors and control devices according to the GPIO configuration in `config.py`.

## Usage

### Starting the System
```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python app.py
```

The system will:
1. Initialize GPIO pins and sensors
2. Connect to local MongoDB database
3. Attempt to connect to MongoDB Atlas (if configured)
4. Start the web server on port 5000
5. Automatically open browser to `http://localhost:5000`

### Web Interface
- **Login**: Default password is `admin123` (change in .env)
- **Dashboard**: Real-time sensor readings and controls
- **Database Status**: Shows local MongoDB and Atlas connection status
- **Controls**: Manual override for fogger, fan, and lights
- **Historical Data**: Charts and tables of past readings

### Remote Access
To access from other devices on your network:
```bash
# Find your Pi's IP address
hostname -I

# Access via browser at: http://YOUR_PI_IP:5000
```

## Environmental Control

The system automatically manages environmental conditions:

### Optimal Ranges
- **Temperature**: 18-24°C
- **Humidity**: 80-95%
- **CO2**: 800-1200 ppm
- **Light**: 200-800 lux
- **Water Level**: 20-100%

## Automatic Controls

The system automatically manages:

### Humidity Control
- **Fogger**: Activates when humidity drops below optimal range
- **Fan**: Activates when humidity exceeds optimal range
- **Duration**: Configurable misting cycles

### Light Management
- **Schedule**: 6 AM - 6 PM daily
- **Intensity**: Full spectrum LED grow lights
- **Automatic**: Based on time schedule

### Temperature Regulation
- **Monitoring**: Continuous temperature tracking
- **Alerts**: Visual warnings for out-of-range conditions
- **Future**: Heating element control (configurable)

## Database Configuration

### Local MongoDB (Primary)
- Local storage on Raspberry Pi
- No internet required
- Fast local access
- Automatic data persistence

### MongoDB Atlas (Cloud Sync)
- Cloud-based backup and remote access
- Automatic sync when internet available
- Global accessibility
- Optional - system works offline

## API Endpoints

### Sensor Data
- `GET /api/current` - Current sensor readings
- `GET /api/latest` - Recent readings (last 10)
- `GET /api/history` - Historical data
- `GET /api/status` - System status

### Controls
- `POST /api/control/fogger` - Control fogger
- `POST /api/control/fan` - Control fan speed
- `POST /api/control/lights` - Control grow lights


## Troubleshooting

### GPIO Issues
```bash
# Check GPIO permissions
sudo usermod -a -G gpio $USER

# Restart after group change
sudo reboot
```

### Sensor Readings
- Verify wiring connections
- Check sensor power (3.3V/5V)
- Review GPIO pin assignments
- Monitor system logs

### Database Connection
- Verify MongoDB is running: `sudo systemctl status mongod`
- Check local MongoDB connection: `mongo --eval "db.runCommand('ping')"`
- Verify Atlas URI in .env (optional)
- Check internet connectivity for Atlas sync
- Monitor connection status in dashboard

### Web Access
- Ensure port 5000 is open
- Check firewall settings
- Verify Pi's IP address
- Try localhost:5000 directly on Pi

## Development

### Running in Simulation Mode
If GPIO libraries aren't available, the system runs in simulation mode with realistic sensor data.

### Custom Sensors
Extend the `SensorService` class in `app.py` to add new sensors.

### Custom Controls
Add new control functions in `GPIOControlService` class.

## Safety Considerations

- **Electrical Safety**: Use proper relays for high-voltage devices
- **Moisture Protection**: Protect electronics from humidity
- **Ventilation**: Ensure adequate air circulation
- **Fire Safety**: Monitor heating elements and electrical connections
- **Food Safety**: Use food-grade materials for growing containers

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review system logs for error details