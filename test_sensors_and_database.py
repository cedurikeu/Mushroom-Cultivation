#!/usr/bin/env python3
"""
Comprehensive Sensor and Database Test Script
Tests all sensors and verifies data is being saved to MongoDB
"""

import time
import json
from datetime import datetime
from pymongo import MongoClient

def test_scd40_sensor():
    """Test SCD40 sensor (I2C - GPIO 2/3)"""
    print("🔍 Testing SCD40 Sensor (I2C - GPIO 2/3)...")
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

def test_bh1750_sensor():
    """Test BH1750 light sensor (I2C)"""
    print("🔍 Testing BH1750 Light Sensor (I2C)...")
    print("   Make sure BH1750 is connected:")
    print("   - VCC → 3.3V")
    print("   - GND → GND")
    print("   - SDA → GPIO 2 (Pin 3)")
    print("   - SCL → GPIO 3 (Pin 5)")
    print()
    
    try:
        import smbus2
        
        # Try both possible addresses
        addresses = [0x23, 0x5C]
        bh1750 = None
        
        for addr in addresses:
            try:
                bus = smbus2.SMBus(1)
                # Try to read from the address
                bus.read_byte_data(addr, 0x00)
                bus.close()
                
                # If successful, create BH1750 object
                class BH1750:
                    def __init__(self, bus_number=1):
                        self.bus = smbus2.SMBus(bus_number)
                        self.address = addr
                    
                    def read_light_level(self):
                        self.bus.write_byte(self.address, 0x20)  # One-time high res mode
                        time.sleep(0.2)
                        data = self.bus.read_i2c_block_data(self.address, 0x00, 2)
                        light_level = (data[0] << 8 | data[1]) / 1.2
                        return round(light_level, 1)
                    
                    def close(self):
                        if self.bus:
                            self.bus.close()
                
                bh1750 = BH1750()
                print(f"✅ BH1750 found at address 0x{addr:02X}")
                break
                
            except Exception:
                continue
        
        if bh1750:
            # Read light level
            light_lux = bh1750.read_light_level()
            print(f"✅ BH1750 Light Reading: {light_lux:.1f} lux")
            
            # Test with different light conditions
            print("   💡 Cover the sensor to test...")
            time.sleep(3)
            
            light_lux2 = bh1750.read_light_level()
            print(f"   New Light Reading: {light_lux2:.1f} lux")
            
            if abs(light_lux - light_lux2) > 10:
                print("   ✅ BH1750 responding to light changes")
            else:
                print("   ⚠️ BH1750 not responding to light changes")
            
            bh1750.close()
            return True
        else:
            print("❌ BH1750 not found on I2C bus")
            print("   Check connections and try different address")
            return False
            
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        print("   Install with: pip install smbus2")
        return False
    except Exception as e:
        print(f"❌ BH1750 error: {e}")
        print("   Check connections and I2C is enabled")
        return False

def test_ultrasonic_sensor():
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

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB Connection...")
    print()
    
    try:
        # Test local MongoDB
        local_client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        local_db = local_client.sensor_db
        
        # Test connection
        local_client.server_info()
        print("✅ Local MongoDB connected")
        
        # Check if readings collection exists
        collections = local_db.list_collection_names()
        if 'readings' in collections:
            print("✅ Readings collection exists")
            
            # Count documents
            count = local_db.readings.count_documents({})
            print(f"✅ Found {count} readings in database")
            
            # Get latest reading
            latest = local_db.readings.find_one({}, sort=[('server_timestamp', -1)])
            if latest:
                print(f"✅ Latest reading: {latest.get('timestamp', 'N/A')}")
                print(f"   Temperature: {latest.get('temperature', 'N/A')}°C")
                print(f"   Humidity: {latest.get('humidity', 'N/A')}%")
                print(f"   CO2: {latest.get('co2', 'N/A')} ppm")
                print(f"   Light: {latest.get('light_intensity', 'N/A')} lux")
                print(f"   Water: {latest.get('water_level', 'N/A')}%")
            else:
                print("⚠️ No readings found in database")
        else:
            print("⚠️ Readings collection not found")
        
        local_client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        print("   Make sure MongoDB is running: sudo systemctl status mongod")
        return False

def test_sensor_data_save():
    """Test saving sensor data to database"""
    print("🔍 Testing Sensor Data Save to Database...")
    print()
    
    try:
        # Create test data
        test_data = {
            'device_id': 'raspberry-pi-01',
            'temperature': 22.5,
            'humidity': 65.2,
            'co2': 800,
            'light_intensity': 450,
            'water_level': 75.0,
            'timestamp': datetime.utcnow().isoformat(),
            'server_timestamp': datetime.utcnow(),
            'test_reading': True
        }
        
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client.sensor_db
        
        # Insert test data
        result = db.readings.insert_one(test_data)
        print(f"✅ Test data saved with ID: {result.inserted_id}")
        
        # Verify data was saved
        saved_data = db.readings.find_one({'_id': result.inserted_id})
        if saved_data:
            print("✅ Data verified in database")
            print(f"   Temperature: {saved_data['temperature']}°C")
            print(f"   Humidity: {saved_data['humidity']}%")
            print(f"   Light: {saved_data['light_intensity']} lux")
        else:
            print("❌ Data not found in database")
        
        # Clean up test data
        db.readings.delete_one({'_id': result.inserted_id})
        print("✅ Test data cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Database save test error: {e}")
        return False

def test_real_sensor_readings():
    """Test reading from actual sensors and saving to database"""
    print("🔍 Testing Real Sensor Readings and Database Save...")
    print()
    
    try:
        # Import sensor classes
        from app import SensorService, DatabaseService
        
        # Initialize services
        sensor_service = SensorService()
        db_service = DatabaseService()
        
        print("✅ Services initialized")
        
        # Read sensor data
        sensor_data = sensor_service.get_sensor_data()
        print("✅ Sensor data read:")
        print(f"   Temperature: {sensor_data['temperature']}°C")
        print(f"   Humidity: {sensor_data['humidity']}%")
        print(f"   CO2: {sensor_data['co2']} ppm")
        print(f"   Light: {sensor_data['light_intensity']} lux")
        print(f"   Water: {sensor_data['water_level']}%")
        
        # Save to database
        result_id = db_service.save_reading(sensor_data)
        if result_id:
            print(f"✅ Data saved to database with ID: {result_id}")
            
            # Verify in database
            client = MongoClient('mongodb://localhost:27017/')
            db = client.sensor_db
            saved_data = db.readings.find_one({'_id': result_id})
            if saved_data:
                print("✅ Data verified in database")
            else:
                print("❌ Data not found in database")
            client.close()
        else:
            print("❌ Failed to save data to database")
        
        return True
        
    except Exception as e:
        print(f"❌ Real sensor test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Comprehensive Sensor and Database Test")
    print("=" * 60)
    print("This script will test all sensors and database functionality")
    print()
    
    tests = [
        ("SCD40 Sensor", test_scd40_sensor),
        ("BH1750 Light Sensor", test_bh1750_sensor),
        ("Ultrasonic Water Sensor", test_ultrasonic_sensor),
        ("MongoDB Connection", test_mongodb_connection),
        ("Database Save Test", test_sensor_data_save),
        ("Real Sensor Readings", test_real_sensor_readings)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        if test_func():
            passed += 1
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Your system is ready.")
        print("\n🎯 Next steps:")
        print("   1. Start the main application: python3 app.py")
        print("   2. Open browser to http://localhost:5000")
        print("   3. Monitor sensor readings in real-time")
    else:
        print("❌ Some tests failed. Check the issues above.")
        print("\n🔧 Troubleshooting:")
        print("   - Check sensor connections")
        print("   - Verify I2C is enabled: sudo raspi-config")
        print("   - Check MongoDB is running: sudo systemctl status mongod")
        print("   - Check GPIO permissions: sudo usermod -a -G gpio $USER")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    exit(main())