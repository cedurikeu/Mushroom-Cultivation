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
import random
import math

# Import GPIO and sensor libraries
try:
    import RPi.GPIO as GPIO
    import adafruit_dht
    import board
    import digitalio
    import busio
    import adafruit_mcp3xxx.mcp3008 as MCP
    from adafruit_mcp3xxx.analog_in import AnalogIn
    GPIO_AVAILABLE = True
except ImportError:
    print("⚠️ GPIO libraries not available - running in simulation mode")
    GPIO_AVAILABLE = False

# Import configuration
from config import GPIO_CONFIG, MUSHROOM_CONFIG, GROWTH_PHASES, SENSOR_CONFIG

# Load environment variables
load_dotenv()

# Constants
DEVICE_ID = "mushroom-control-01"
SENSOR_READ_INTERVAL = SENSOR_CONFIG['read_interval']
ALERT_THRESHOLDS = MUSHROOM_CONFIG['alert_thresholds']
OPTIMAL_RANGES = MUSHROOM_CONFIG['optimal_ranges']

# Current mushroom growth phase
CURRENT_PHASE = 'pinning'  # Default phase

# Initialize Flask
app = Flask(__name__)
CORS(app)
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-here'),
    'MONGO_URI': os.getenv('MONGODB_URI'),
    'DASHBOARD_PASSWORD': os.getenv('DASHBOARD_PASSWORD', 'admin123')  # Change this!
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
                    mushroom_phase TEXT,
                    mushroom_status TEXT,
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
                    INSERT INTO readings (device_id, temperature, humidity, co2, light_intensity, mushroom_phase, mushroom_status, timestamp, server_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['device_id'],
                    data['temperature'],
                    data['humidity'],
                    data.get('co2', 400),
                    data.get('light_intensity', 0),
                    data.get('mushroom_phase', 'fruiting'),
                    data.get('mushroom_status', 'unknown'),
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
        
        if GPIO_AVAILABLE:
            self.setup_gpio()
        
    def setup_gpio(self):
        """Initialize GPIO pins"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup control pins as outputs
            GPIO.setup(GPIO_CONFIG['FOGGER_PIN'], GPIO.OUT)
            GPIO.setup(GPIO_CONFIG['FAN_PIN'], GPIO.OUT)
            GPIO.setup(GPIO_CONFIG['HEATER_PIN'], GPIO.OUT)
            GPIO.setup(GPIO_CONFIG['LED_LIGHTS_PIN'], GPIO.OUT)
            
            # Setup status LED pins
            GPIO.setup(GPIO_CONFIG['STATUS_LED_GREEN'], GPIO.OUT)
            GPIO.setup(GPIO_CONFIG['STATUS_LED_RED'], GPIO.OUT)
            GPIO.setup(GPIO_CONFIG['STATUS_LED_BLUE'], GPIO.OUT)
            
            # Initialize all outputs to OFF
            GPIO.output(GPIO_CONFIG['FOGGER_PIN'], GPIO.LOW)
            GPIO.output(GPIO_CONFIG['FAN_PIN'], GPIO.LOW)
            GPIO.output(GPIO_CONFIG['HEATER_PIN'], GPIO.LOW)
            GPIO.output(GPIO_CONFIG['LED_LIGHTS_PIN'], GPIO.LOW)
            
            # Set status LED to green (system OK)
            GPIO.output(GPIO_CONFIG['STATUS_LED_GREEN'], GPIO.HIGH)
            GPIO.output(GPIO_CONFIG['STATUS_LED_RED'], GPIO.LOW)
            GPIO.output(GPIO_CONFIG['STATUS_LED_BLUE'], GPIO.LOW)
            
            print("✅ GPIO initialized successfully")
        except Exception as e:
            print(f"❌ GPIO setup error: {e}")
    
    def control_fogger(self, activate=True, duration=None):
        """Control the fogger"""
        if not GPIO_AVAILABLE:
            print(f"🌫️ Fogger {'ON' if activate else 'OFF'} (simulation)")
            self.fogger_active = activate
            return
            
        try:
            if activate:
                GPIO.output(GPIO_CONFIG['FOGGER_PIN'], GPIO.HIGH)
                self.fogger_active = True
                print("🌫️ Fogger activated")
                
                if duration:
                    # Auto-turn off after duration
                    threading.Timer(duration, self.control_fogger, [False]).start()
            else:
                GPIO.output(GPIO_CONFIG['FOGGER_PIN'], GPIO.LOW)
                self.fogger_active = False
                print("🌫️ Fogger deactivated")
        except Exception as e:
            print(f"❌ Fogger control error: {e}")
    
    def control_fan(self, speed_percent=0):
        """Control exhaust fan speed (0-100%)"""
        if not GPIO_AVAILABLE:
            print(f"🌬️ Fan speed: {speed_percent}% (simulation)")
            self.fan_speed = speed_percent
            return
            
        try:
            if speed_percent > 0:
                GPIO.output(GPIO_CONFIG['FAN_PIN'], GPIO.HIGH)
                # In real implementation, you'd use PWM for speed control
                # pwm = GPIO.PWM(GPIO_CONFIG['FAN_PIN'], 1000)
                # pwm.start(speed_percent)
            else:
                GPIO.output(GPIO_CONFIG['FAN_PIN'], GPIO.LOW)
            
            self.fan_speed = speed_percent
            print(f"🌬️ Fan speed set to {speed_percent}%")
        except Exception as e:
            print(f"❌ Fan control error: {e}")
    
    def control_lights(self, activate=True):
        """Control LED grow lights"""
        if not GPIO_AVAILABLE:
            print(f"💡 Lights {'ON' if activate else 'OFF'} (simulation)")
            self.lights_active = activate
            return
            
        try:
            GPIO.output(GPIO_CONFIG['LED_LIGHTS_PIN'], GPIO.HIGH if activate else GPIO.LOW)
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
        self.simulation_time = 0
        self.current_data = {
            'temperature': 0,
            'humidity': 0,
            'co2': 400,
            'light_intensity': 0,
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': DEVICE_ID,
            'mushroom_phase': CURRENT_PHASE,
            'mushroom_status': 'healthy'
        }
        
        if GPIO_AVAILABLE:
            self.setup_sensors()
        
    def setup_sensors(self):
        """Initialize sensors"""
        try:
            # DHT22 temperature/humidity sensor
            self.dht = adafruit_dht.DHT22(getattr(board, f'D{GPIO_CONFIG["DHT22_PIN"]}'))
            
            # SPI setup for MCP3008 ADC
            spi = busio.SPI(clock=getattr(board, f'D{GPIO_CONFIG["SPI_CLK"]}'),
                          MISO=getattr(board, f'D{GPIO_CONFIG["SPI_MISO"]}'),
                          MOSI=getattr(board, f'D{GPIO_CONFIG["SPI_MOSI"]}'))
            cs = digitalio.DigitalInOut(getattr(board, f'D{GPIO_CONFIG["SPI_CS"]}'))
            
            self.mcp = MCP.MCP3008(spi, cs)
            self.light_sensor = AnalogIn(self.mcp, MCP.P0)  # Channel 0 for light
            self.co2_sensor = AnalogIn(self.mcp, MCP.P1)    # Channel 1 for CO2
            
            print("✅ Sensors initialized successfully")
        except Exception as e:
            print(f"❌ Sensor setup error: {e}")
            self.dht = None
            self.mcp = None
    
    def read_real_sensors(self):
        """Read data from actual GPIO sensors"""
        data = self.current_data.copy()
        
        try:
            # Read DHT22 (temperature & humidity)
            if hasattr(self, 'dht') and self.dht:
                temp = self.dht.temperature
                humidity = self.dht.humidity
                
                if temp is not None and humidity is not None:
                    data['temperature'] = round(temp + SENSOR_CONFIG['calibration_offsets']['temperature'], 1)
                    data['humidity'] = round(humidity + SENSOR_CONFIG['calibration_offsets']['humidity'], 1)
            
            # Read light sensor (photoresistor via ADC)
            if hasattr(self, 'light_sensor') and self.light_sensor:
                light_voltage = self.light_sensor.voltage
                # Convert voltage to light intensity (0-1000 range)
                light_intensity = int((light_voltage / 3.3) * 1000)
                data['light_intensity'] = light_intensity + SENSOR_CONFIG['calibration_offsets']['light_intensity']
            
            # Read CO2 sensor (MQ-135 or similar via ADC)
            if hasattr(self, 'co2_sensor') and self.co2_sensor:
                co2_voltage = self.co2_sensor.voltage
                # Convert voltage to CO2 ppm (simplified conversion)
                co2_ppm = int(400 + (co2_voltage / 3.3) * 1000)
                data['co2'] = co2_ppm + SENSOR_CONFIG['calibration_offsets']['co2']
            
        except Exception as e:
            print(f"❌ Sensor reading error: {e}")
        
        return data
    
    def simulate_realistic_data(self):
        """Create realistic sensor simulation for mushroom growing"""
        self.simulation_time += SENSOR_READ_INTERVAL
        
        # Get optimal ranges for current phase
        phase_config = GROWTH_PHASES.get(CURRENT_PHASE, GROWTH_PHASES['fruiting'])
        
        # Temperature simulation based on mushroom growth phase
        temp_min, temp_max = phase_config['temp_range']
        temp_base = (temp_min + temp_max) / 2
        temp_variation = random.uniform(-1.0, 1.0)
        temperature = temp_base + temp_variation
        
        # Humidity simulation based on mushroom growth phase
        humidity_min, humidity_max = phase_config['humidity_range']
        humidity_base = (humidity_min + humidity_max) / 2
        humidity_variation = random.uniform(-5, 5)
        humidity = max(50, min(98, humidity_base + humidity_variation))
        
        # CO2 simulation
        co2_base = random.choice([800, 900, 1000, 1100])
        co2_variation = random.uniform(-100, 150)
        co2 = max(400, co2_base + co2_variation)
        
        # Light intensity simulation
        hour = datetime.now().hour
        if phase_config['light_needed'] and 6 <= hour <= 18:
            light_base = 500
            light_variation = random.uniform(-100, 100)
        else:
            light_base = 50
            light_variation = random.uniform(-20, 20)
        light_intensity = max(0, light_base + light_variation)
        
        # Determine mushroom status based on conditions
        mushroom_status = self.determine_mushroom_status(temperature, humidity, co2, light_intensity)
        
        self.current_data = {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'co2': int(co2),
            'light_intensity': int(light_intensity),
            'timestamp': datetime.utcnow().isoformat(),
            'device_id': DEVICE_ID,
            'mushroom_phase': CURRENT_PHASE,
            'mushroom_status': mushroom_status
        }
        
        return self.current_data
    
    def determine_mushroom_status(self, temp, humidity, co2, light):
        """Determine mushroom health status based on environmental conditions"""
        phase_config = GROWTH_PHASES.get(CURRENT_PHASE, GROWTH_PHASES['fruiting'])
        
        # Check if conditions are within optimal ranges
        temp_min, temp_max = phase_config['temp_range']
        humidity_min, humidity_max = phase_config['humidity_range']
        
        issues = []
        
        if temp < temp_min - 2 or temp > temp_max + 2:
            issues.append('temperature')
        if humidity < humidity_min - 10 or humidity > humidity_max + 5:
            issues.append('humidity')
        if co2 < 600 or co2 > 1500:
            issues.append('co2')
        if phase_config['light_needed'] and light < 200:
            issues.append('light')
        
        if not issues:
            return 'optimal'
        elif len(issues) == 1:
            return 'good'
        elif len(issues) == 2:
            return 'warning'
        else:
            return 'critical'
    
    def get_sensor_data(self):
        """Get current sensor data (real or simulated)"""
        if GPIO_AVAILABLE and hasattr(self, 'dht'):
            return self.read_real_sensors()
        else:
            return self.simulate_realistic_data()

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
        'mushroom_phase': CURRENT_PHASE,
        'controls': control_status,
        'gpio_available': GPIO_AVAILABLE
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

@app.route('/api/phase', methods=['POST'])
@require_auth
def set_mushroom_phase():
    global CURRENT_PHASE
    data = request.get_json()
    new_phase = data.get('phase')
    
    if new_phase in GROWTH_PHASES:
        CURRENT_PHASE = new_phase
        return jsonify({
            'success': True,
            'current_phase': CURRENT_PHASE,
            'phase_config': GROWTH_PHASES[CURRENT_PHASE],
            'message': f"Mushroom phase set to {GROWTH_PHASES[CURRENT_PHASE]['name']}"
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid phase specified'
        }), 400

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
            # Get sensor data (real or simulated)
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
            status_emoji = {'optimal': '🟢', 'good': '🟡', 'warning': '🟠', 'critical': '🔴'}
            emoji = status_emoji.get(sensor_data['mushroom_status'], '⚪')
            print(f"📊 {emoji} T: {sensor_data['temperature']}°C, H: {sensor_data['humidity']}%, CO2: {sensor_data['co2']}ppm, Light: {sensor_data['light_intensity']}, Status: {sensor_data['mushroom_status']}")
            
            time.sleep(SENSOR_READ_INTERVAL)
            
        except Exception as e:
            print(f"⚠️ Sensor monitor error: {e}")
            time.sleep(5)

def auto_control_environment(sensor_data):
    """Automatically control environment based on sensor readings"""
    try:
        phase_config = GROWTH_PHASES.get(CURRENT_PHASE, GROWTH_PHASES['fruiting'])
        temp = sensor_data['temperature']
        humidity = sensor_data['humidity']
        
        # Auto-fogger control based on humidity
        humidity_min, humidity_max = phase_config['humidity_range']
        if humidity < humidity_min - 5 and not gpio_control.fogger_active:
            gpio_control.control_fogger(True, MUSHROOM_CONFIG['control_settings']['fogger_duration'])
        
        # Auto-fan control based on humidity (too high)
        if humidity > humidity_max + 5 and gpio_control.fan_speed < 50:
            gpio_control.control_fan(50)
        elif humidity <= humidity_max and gpio_control.fan_speed > 0:
            gpio_control.control_fan(0)
        
        # Auto-light control based on time and growth phase
        current_hour = datetime.now().hour
        light_schedule = MUSHROOM_CONFIG['control_settings']['light_schedule']
        should_lights_be_on = (phase_config['light_needed'] and 
                              light_schedule['on_hour'] <= current_hour < light_schedule['off_hour'])
        
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
    print("🍄 Starting Mushroom Environmental Control System")
    print(f"📊 Database: {'MongoDB' if db_service.use_mongo else 'SQLite'}")
    print(f"🔌 GPIO: {'Available' if GPIO_AVAILABLE else 'Simulation Mode'}")
    print(f"🌱 Current Phase: {GROWTH_PHASES[CURRENT_PHASE]['name']}")
    
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
        if GPIO_AVAILABLE:
            GPIO.cleanup()
    except Exception as e:
        print(f"❌ Server error: {e}")
        if GPIO_AVAILABLE:
            GPIO.cleanup()

if __name__ == '__main__':
    main()