import os
import sqlite3
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from pymongo import MongoClient

# Import GPIO and sensor libraries
from gpiozero import DistanceSensor, LED, OutputDevice
import adafruit_scd4x
import board
import busio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# Import configuration
from config import GPIO_CONFIG, MUSHROOM_CONFIG, SENSOR_CONFIG

# Load environment variables
load_dotenv()

# Constants
DEVICE_ID = "raspberry-pi-01"
SENSOR_READ_INTERVAL = SENSOR_CONFIG['read_interval']
ALERT_THRESHOLDS = MUSHROOM_CONFIG['alert_thresholds']
OPTIMAL_RANGES = MUSHROOM_CONFIG['optimal_ranges']

# Initialize Flask
app = Flask(__name__)
CORS(app)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'pentaplets'),
    'MONGO_URI': os.getenv('MONGODB_URI'),
    'DASHBOARD_PASSWORD': os.getenv('DASHBOARD_PASSWORD', 'pentaplets')
})

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False
)

# ========================
# AUTHENTICATION
# ========================
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ========================
# DATABASE SERVICE
# ========================
class DatabaseService:
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.sqlite_conn = None
        self.use_mongo = True
        self.setup_databases()
        
    def setup_databases(self):
        # Setup MongoDB
        self.connect_mongodb()
        
        # Setup SQLite fallback
        self.setup_sqlite()
        
    def connect_mongodb(self):
        try:
            if app.config['MONGO_URI']:
                self.mongo_client = MongoClient(app.config['MONGO_URI'], serverSelectionTimeoutMS=5000)
                self.mongo_db = self.mongo_client.sensor_db
                # Test connection
                self.mongo_client.server_info()
                self.use_mongo = True
                print("✅ MongoDB connected")
                return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.use_mongo = False
            self.mongo_db = None
            return False
            
    def setup_sqlite(self):
        try:
            self.sqlite_conn = sqlite3.connect('sensor_data.db', check_same_thread=False)
            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    temperature REAL,
                    humidity REAL,
                    co2 INTEGER,
                    light_intensity INTEGER,
                    water_level REAL,
                    timestamp TEXT,
                    server_timestamp TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE,
                    config_data TEXT,
                    updated_at TEXT
                )
            ''')
            self.sqlite_conn.commit()
            print("✅ SQLite database initialized")
        except Exception as e:
            print(f"❌ SQLite setup failed: {e}")

    def save_reading(self, data):
        # Try MongoDB first, fallback to SQLite
        if self.use_mongo and self.mongo_db:
            try:
                data['server_timestamp'] = datetime.utcnow()
                result = self.mongo_db.readings.insert_one(data)
                print(f"📦 Saved to MongoDB: {result.inserted_id}")
                return result.inserted_id
            except Exception as e:
                print(f"📦 MongoDB save error, switching to SQLite: {e}")
                self.use_mongo = False
                
        # SQLite fallback
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    INSERT INTO readings (device_id, temperature, humidity, co2, light_intensity, water_level, timestamp, server_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['device_id'],
                    data['temperature'],
                    data['humidity'],
                    data.get('co2', 400),
                    data.get('light_intensity', 0),
                    data.get('water_level', 50.0),
                    data['timestamp'],
                    datetime.utcnow().isoformat()
                ))
                self.sqlite_conn.commit()
                print(f"📦 Saved to SQLite: {cursor.lastrowid}")
                return cursor.lastrowid
            except Exception as e:
                print(f"📦 SQLite save error: {e}")
                return None

    def get_latest_readings(self, limit=10):
        # Try MongoDB first, fallback to SQLite
        if self.use_mongo and self.mongo_db:
            try:
                cursor = self.mongo_db.readings.find({
                    'device_id': DEVICE_ID
                }).sort('server_timestamp', -1).limit(limit)
                
                readings = []
                for doc in cursor:
                    doc['_id'] = str(doc['_id'])
                    if isinstance(doc.get('server_timestamp'), datetime):
                        doc['server_timestamp'] = doc['server_timestamp'].isoformat()
                    readings.append(doc)
                
                print(f"📊 Retrieved {len(readings)} readings from MongoDB")
                return readings
            except Exception as e:
                print(f"📦 MongoDB read error, switching to SQLite: {e}")
                self.use_mongo = False
                
        # SQLite fallback
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    SELECT * FROM readings 
                    WHERE device_id = ? 
                    ORDER BY server_timestamp DESC 
                    LIMIT ?
                ''', (DEVICE_ID, limit))
                
                columns = [description[0] for description in cursor.description]
                readings = [dict(zip(columns, row)) for row in cursor.fetchall()]
                print(f"📊 Retrieved {len(readings)} readings from SQLite")
                return readings
            except Exception as e:
                print(f"📦 SQLite read error: {e}")
                return []
                
        return []

    def get_historical_data(self, hours=24, limit=500):
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Try MongoDB first, fallback to SQLite
        if self.use_mongo and self.mongo_db:
            try:
                cursor = self.mongo_db.readings.find({
                    'server_timestamp': {'$gte': time_threshold},
                    'device_id': DEVICE_ID
                }).sort('server_timestamp', -1).limit(limit)
                
                readings = []
                for doc in cursor:
                    doc['_id'] = str(doc['_id'])
                    if isinstance(doc.get('server_timestamp'), datetime):
                        doc['server_timestamp'] = doc['server_timestamp'].isoformat()
                    readings.append(doc)
                
                return readings
            except Exception as e:
                print(f"📦 MongoDB historical read error: {e}")
                self.use_mongo = False
                
        # SQLite fallback
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    SELECT * FROM readings 
                    WHERE device_id = ? AND server_timestamp >= ?
                    ORDER BY server_timestamp DESC 
                    LIMIT ?
                ''', (DEVICE_ID, time_threshold.isoformat(), limit))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            except Exception as e:
                print(f"📦 SQLite historical read error: {e}")
                return []
                
        return []

# Initialize DB service
db_service = DatabaseService()

# ========================
# GPIO CONTROL SERVICE
# ========================
class GPIOControlService:
    def __init__(self):
        self.fogger_active = False
        self.fan_speed = 0
        self.heater_active = False
        self.lights_active = False
        self.setup_gpio()
        
    def setup_gpio(self):
        """Initialize GPIO pins using GPIO Zero"""
        try:
            # Setup control devices using GPIO Zero
            self.fogger = OutputDevice(GPIO_CONFIG['FOGGER_PIN'])
            self.fan = OutputDevice(GPIO_CONFIG['FAN_PIN'])
            self.heater = OutputDevice(GPIO_CONFIG['HEATER_PIN'])
            self.lights = OutputDevice(GPIO_CONFIG['LED_LIGHTS_PIN'])
            
            # Setup status LEDs
            self.status_led_green = LED(GPIO_CONFIG['STATUS_LED_GREEN'])
            self.status_led_red = LED(GPIO_CONFIG['STATUS_LED_RED'])
            self.status_led_blue = LED(GPIO_CONFIG['STATUS_LED_BLUE'])
            
            # Initialize all outputs to OFF
            self.fogger.off()
            self.fan.off()
            self.heater.off()
            self.lights.off()
            
            # Set status LED to green (system OK)
            self.status_led_green.on()
            self.status_led_red.off()
            self.status_led_blue.off()
            
            print("✅ GPIO Zero devices initialized successfully")
        except Exception as e:
            print(f"❌ GPIO setup error: {e}")
    
    def control_fogger(self, activate=True, duration=None):
        """Control the fogger"""
        try:
            if activate:
                self.fogger.on()
                self.fogger_active = True
                print("🌫️ Fogger activated")
                
                if duration:
                    # Auto-turn off after duration
                    threading.Timer(duration, self.control_fogger, [False]).start()
            else:
                self.fogger.off()
                self.fogger_active = False
                print("🌫️ Fogger deactivated")
        except Exception as e:
            print(f"❌ Fogger control error: {e}")
    
    def control_fan(self, speed_percent=0):
        """Control exhaust fan speed (0-100%)"""
        try:
            if speed_percent > 0:
                self.fan.on()
            else:
                self.fan.off()
            
            self.fan_speed = speed_percent
            print(f"🌬️ Fan speed set to {speed_percent}%")
        except Exception as e:
            print(f"❌ Fan control error: {e}")
    
    def control_lights(self, activate=True):
        """Control LED grow lights"""
        try:
            if activate:
                self.lights.on()
            else:
                self.lights.off()
            self.lights_active = activate
            print(f"💡 Lights {'activated' if activate else 'deactivated'}")
        except Exception as e:
            print(f"❌ Light control error: {e}")
    
    def get_control_status(self):
        """Get current control status"""
        return {
            'fogger_active': self.fogger_active,
            'fan_speed': self.fan_speed,
            'heater_active': self.heater_active,
            'lights_active': self.lights_active
        }

# ========================
# SENSOR SERVICE
# ========================
class SensorService:
    def __init__(self):
        self.current_data = {
            'temperature': 0,
            'humidity': 0,
            'co2': 400,
            'light_intensity': 0,
            'water_level': 50.0,
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': DEVICE_ID
        }
        self.setup_sensors()
        
    def setup_sensors(self):
        """Initialize sensors"""
        try:
            # I2C setup for SCD40 sensor (pins 3=SDA, 5=SCL)
            i2c = busio.I2C(board.SCL, board.SDA)
            self.scd40 = adafruit_scd4x.SCD4X(i2c)
            print("🔄 Starting SCD40 periodic measurement...")
            self.scd40.start_periodic_measurement()
            
            # SPI setup for MCP3008 ADC (for light sensor)
            spi = busio.SPI(clock=getattr(board, f'D{GPIO_CONFIG["SPI_CLK"]}'),
                          MISO=getattr(board, f'D{GPIO_CONFIG["SPI_MISO"]}'),
                          MOSI=getattr(board, f'D{GPIO_CONFIG["SPI_MOSI"]}'))
            cs = getattr(board, f'D{GPIO_CONFIG["SPI_CS"]}')
            
            self.mcp = MCP.MCP3008(spi, cs)
            self.light_sensor = AnalogIn(self.mcp, MCP.P0)  # Channel 0 for light
            
            # Setup ultrasonic sensor using GPIO Zero
            self.water_sensor = DistanceSensor(
                echo=GPIO_CONFIG['ULTRASONIC_ECHO_PIN'], 
                trigger=GPIO_CONFIG['ULTRASONIC_TRIG_PIN'],
                max_distance=1  # 1 meter max range
            )
            
            print("✅ Sensors initialized successfully")
            print("  - SCD40 (Temperature, Humidity, CO2) on I2C")
            print("  - Light sensor via MCP3008 ADC")
            print("  - Ultrasonic water level sensor (GPIO Zero)")
        except Exception as e:
            print(f"❌ Sensor setup error: {e}")
            self.scd40 = None
            self.mcp = None
            self.water_sensor = None
    
    def read_ultrasonic_distance(self):
        """Read distance from ultrasonic sensor in cm using GPIO Zero"""
        try:
            if hasattr(self, 'water_sensor') and self.water_sensor:
                # GPIO Zero DistanceSensor returns distance in meters
                distance_m = self.water_sensor.distance
                distance_cm = distance_m * 100  # Convert to centimeters
                return round(distance_cm, 2)
            else:
                return None
        except Exception as e:
            print(f"❌ Ultrasonic sensor error: {e}")
            return None
    
    def calculate_water_level_percentage(self, distance_cm):
        """Convert ultrasonic distance to water level percentage"""
        if distance_cm is None:
            return 50.0  # Default value if sensor fails
        
        reservoir_config = SENSOR_CONFIG['reservoir_config']
        sensor_height = reservoir_config['sensor_height_cm']
        max_depth = reservoir_config['max_depth_cm']
        min_depth = reservoir_config['min_depth_cm']
        
        # Calculate water depth
        water_depth = sensor_height - distance_cm
        
        # Clamp to valid range
        water_depth = max(0, min(max_depth, water_depth))
        
        # Convert to percentage (0% = empty, 100% = full)
        if water_depth <= min_depth:
            return 0.0
        else:
            percentage = ((water_depth - min_depth) / (max_depth - min_depth)) * 100
            return round(percentage, 1)
    
    def read_sensors(self):
        """Read data from actual GPIO sensors"""
        data = self.current_data.copy()
        
        try:
            # Read SCD40 (temperature, humidity, CO2)
            if hasattr(self, 'scd40') and self.scd40:
                if self.scd40.data_ready:
                    temp = self.scd40.temperature
                    humidity = self.scd40.relative_humidity
                    co2 = self.scd40.CO2
                    
                    if temp is not None and humidity is not None and co2 is not None:
                        data['temperature'] = round(temp + SENSOR_CONFIG['calibration_offsets']['temperature'], 1)
                        data['humidity'] = round(humidity + SENSOR_CONFIG['calibration_offsets']['humidity'], 1)
                        data['co2'] = int(co2 + SENSOR_CONFIG['calibration_offsets']['co2'])
                        print(f"📡 SCD40 readings: T={temp:.1f}°C, H={humidity:.1f}%, CO2={co2}ppm")
            
            # Read light sensor (photoresistor via ADC)
            if hasattr(self, 'light_sensor') and self.light_sensor:
                light_voltage = self.light_sensor.voltage
                # Convert voltage to light intensity (0-1000 range)
                light_intensity = int((light_voltage / 3.3) * 1000)
                data['light_intensity'] = light_intensity + SENSOR_CONFIG['calibration_offsets']['light_intensity']
            
            # Read water level via ultrasonic sensor
            distance = self.read_ultrasonic_distance()
            if distance is not None:
                water_level = self.calculate_water_level_percentage(distance)
                data['water_level'] = water_level + SENSOR_CONFIG['calibration_offsets']['water_level']
                print(f"💧 Water level: {distance:.1f}cm distance = {water_level:.1f}%")
            
            # Update timestamp
            data['timestamp'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            print(f"❌ Sensor reading error: {e}")
        
        return data
    
    def get_sensor_data(self):
        """Get current sensor data"""
        return self.read_sensors()

# Initialize services
sensor_service = SensorService()
gpio_control = GPIOControlService()

# ========================
# WEB ROUTES
# ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == app.config['DASHBOARD_PASSWORD']:
            session['authenticated'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/current')
@require_auth
def get_current():
    return jsonify(sensor_service.current_data)

@app.route('/api/latest')
@require_auth
def get_latest():
    readings = db_service.get_latest_readings(limit=10)
    return jsonify(readings)

@app.route('/api/history')
@require_auth
def get_history():
    hours = request.args.get('hours', 24, type=int)
    readings = db_service.get_historical_data(hours)
    return jsonify(readings)

@app.route('/api/status')
@require_auth
def get_status():
    control_status = gpio_control.get_control_status()
    return jsonify({
        'database': 'MongoDB' if db_service.use_mongo else 'SQLite',
        'connected': db_service.use_mongo or db_service.sqlite_conn is not None,
        'device_id': DEVICE_ID,
        'controls': control_status
    })

@app.route('/api/control/fogger', methods=['POST'])
@require_auth
def control_fogger():
    data = request.get_json()
    activate = data.get('activate', False)
    duration = data.get('duration', MUSHROOM_CONFIG['control_settings']['fogger_duration'])
    
    gpio_control.control_fogger(activate, duration if activate else None)
    
    return jsonify({
        'success': True,
        'fogger_active': gpio_control.fogger_active,
        'message': f"Fogger {'activated' if activate else 'deactivated'}"
    })

@app.route('/api/control/fan', methods=['POST'])
@require_auth
def control_fan():
    data = request.get_json()
    speed = data.get('speed', 0)
    
    gpio_control.control_fan(speed)
    
    return jsonify({
        'success': True,
        'fan_speed': gpio_control.fan_speed,
        'message': f"Fan speed set to {speed}%"
    })

@app.route('/api/control/lights', methods=['POST'])
@require_auth
def control_lights():
    data = request.get_json()
    activate = data.get('activate', False)
    
    gpio_control.control_lights(activate)
    
    return jsonify({
        'success': True,
        'lights_active': gpio_control.lights_active,
        'message': f"Lights {'activated' if activate else 'deactivated'}"
    })

# SocketIO Handlers
@socketio.on('connect')
def handle_connect():
    if 'authenticated' in session:
        emit('sensor_update', sensor_service.current_data)
        emit('status_update', {
            'database': 'MongoDB' if db_service.use_mongo else 'SQLite',
            'connected': True
        })

@socketio.on('request_data')
def handle_data_request():
    if 'authenticated' in session:
        emit('sensor_update', sensor_service.current_data)

# ========================
# BACKGROUND TASKS
# ========================
def sensor_monitor():
    """Background task to read sensor data and save to database"""
    while True:
        try:
            # Get sensor data
            sensor_data = sensor_service.get_sensor_data()
            
            # Auto-control based on conditions
            auto_control_environment(sensor_data)
            
            # Save to database (MongoDB or SQLite fallback)
            db_service.save_reading(sensor_data)
            
            # Emit real-time update to connected clients
            control_status = gpio_control.get_control_status()
            update_data = {
                **sensor_data,
                'controls': control_status
            }
            socketio.emit('sensor_update', update_data)
            
            # Log current values
            print(f"📊 T: {sensor_data['temperature']}°C, H: {sensor_data['humidity']}%, CO2: {sensor_data['co2']}ppm, Light: {sensor_data['light_intensity']}, Water: {sensor_data['water_level']}%")
            
            time.sleep(SENSOR_READ_INTERVAL)
            
        except Exception as e:
            print(f"⚠️ Sensor monitor error: {e}")
            time.sleep(5)

def auto_control_environment(sensor_data):
    """Automatically control environment based on sensor readings"""
    try:
        temp = sensor_data['temperature']
        humidity = sensor_data['humidity']
        water_level = sensor_data.get('water_level', 50.0)
        
        # Check water level first - disable fogger if water is too low
        if water_level < 15:
            if gpio_control.fogger_active:
                gpio_control.control_fogger(False)
                print("🚨 Low water level detected - Fogger disabled!")
        
        # Auto-fogger control based on humidity (only if water level is sufficient)
        humidity_min = OPTIMAL_RANGES['humidity']['min']
        humidity_max = OPTIMAL_RANGES['humidity']['max']
        if (humidity < humidity_min - 5 and not gpio_control.fogger_active and water_level > 20):
            gpio_control.control_fogger(True, MUSHROOM_CONFIG['control_settings']['fogger_duration'])
        
        # Auto-fan control based on humidity (too high)
        if humidity > humidity_max + 5 and gpio_control.fan_speed < 50:
            gpio_control.control_fan(50)
        elif humidity <= humidity_max and gpio_control.fan_speed > 0:
            gpio_control.control_fan(0)
        
        # Auto-light control based on time
        current_hour = datetime.now().hour
        light_schedule = MUSHROOM_CONFIG['control_settings']['light_schedule']
        should_lights_be_on = (light_schedule['on_hour'] <= current_hour < light_schedule['off_hour'])
        
        if should_lights_be_on != gpio_control.lights_active:
            gpio_control.control_lights(should_lights_be_on)
            
    except Exception as e:
        print(f"⚠️ Auto-control error: {e}")

def database_health_monitor():
    """Monitor database connections and switch between MongoDB and SQLite"""
    while True:
        try:
            # Try to reconnect to MongoDB if we're using SQLite
            if not db_service.use_mongo:
                if db_service.connect_mongodb():
                    print("🔄 Switched back to MongoDB")
                    
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"⚠️ Database monitor error: {e}")
            time.sleep(30)

# ========================
# MAIN APPLICATION
# ========================
def main():
    print("🍄 Starting Environmental Control System")
    print(f"📊 Database: {'MongoDB' if db_service.use_mongo else 'SQLite'}")
    print(f"🔌 GPIO: Available")
    
    # Start background threads
    threading.Thread(target=sensor_monitor, daemon=True).start()
    threading.Thread(target=database_health_monitor, daemon=True).start()
    
    # Auto-open browser
    def open_browser():
        time.sleep(2)  # Wait for server to start
        webbrowser.open('http://localhost:5000')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start web server
    try:
        print("🌐 Web server running at http://localhost:5000")
        print("🔐 Default password: admin123 (change in .env file)")
        print("🌍 Opening browser automatically...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("🛑 Server stopped")
        print("🧹 GPIO Zero will automatically cleanup")
    except Exception as e:
        print(f"❌ Server error: {e}")
        print("🧹 GPIO Zero will automatically cleanup")

if __name__ == '__main__':
    main()