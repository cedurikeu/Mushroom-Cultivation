#!/usr/bin/env python3
"""
Simple test script to verify the database functionality
"""
import sqlite3
import json
from datetime import datetime

def check_sqlite_data():
    """Check data in SQLite database"""
    try:
        conn = sqlite3.connect('sensor_data.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM readings")
        count = cursor.fetchone()[0]
        print(f"📊 Total readings in SQLite: {count}")
        
        # Get latest 5 readings
        cursor.execute("""
            SELECT device_id, temperature, humidity, co2, timestamp, server_timestamp 
            FROM readings 
            ORDER BY server_timestamp DESC 
            LIMIT 5
        """)
        
        readings = cursor.fetchall()
        print("\n🔄 Latest 5 readings:")
        print("-" * 80)
        for reading in readings:
            device_id, temp, humidity, co2, timestamp, server_timestamp = reading
            print(f"Device: {device_id}")
            print(f"  Temperature: {temp}°C")
            print(f"  Humidity: {humidity}%")
            print(f"  CO2: {co2} ppm")
            print(f"  Timestamp: {timestamp}")
            print(f"  Server Timestamp: {server_timestamp}")
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking SQLite data: {e}")

def test_api_response():
    """Test API response format"""
    import requests
    
    try:
        # Test if server is running
        response = requests.get('http://localhost:5000/login', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responsive")
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to server: {e}")

if __name__ == "__main__":
    print("🧪 Testing IoT Monitoring System")
    print("=" * 50)
    
    check_sqlite_data()
    print("\n" + "=" * 50)
    test_api_response()
    
    print("\n✨ Test completed!")