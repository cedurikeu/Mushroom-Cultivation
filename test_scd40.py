#!/usr/bin/env python3
"""
Test script for SCD40 sensor
Verifies sensor connection and reads data
"""

import time
import board
import busio
import adafruit_scd4x

def test_scd40():
    print("🧪 Testing SCD40 sensor connection...")
    print("📍 Expected connections:")
    print("  - Pin 1 (3.3V) → SCD40 VDD")
    print("  - Pin 3 (GPIO 2) → SCD40 SDA") 
    print("  - Pin 5 (GPIO 3) → SCD40 SCL")
    print("  - Pin 9 (GND) → SCD40 GND")
    print()
    
    try:
        # Initialize I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        print("✅ I2C bus initialized")
        
        # Initialize SCD40
        scd40 = adafruit_scd4x.SCD4X(i2c)
        print("✅ SCD40 sensor object created")
        
        # Start periodic measurement
        print("🔄 Starting periodic measurement...")
        scd40.start_periodic_measurement()
        
        print("⏳ Waiting for first measurement (5 seconds)...")
        time.sleep(5)
        
        # Read sensor data
        for i in range(10):
            if scd40.data_ready:
                temp = scd40.temperature
                humidity = scd40.relative_humidity
                co2 = scd40.CO2
                
                print(f"📊 Reading {i+1}:")
                print(f"  🌡️  Temperature: {temp:.1f}°C")
                print(f"  💧 Humidity: {humidity:.1f}%")
                print(f"  🌬️  CO2: {co2:.0f} ppm")
                print()
            else:
                print(f"⏳ Reading {i+1}: Data not ready, waiting...")
            
            time.sleep(2)
        
        print("✅ SCD40 test completed successfully!")
        
    except Exception as e:
        print(f"❌ SCD40 test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check wiring connections")
        print("  2. Verify I2C is enabled: sudo raspi-config → Interface Options → I2C")
        print("  3. Check I2C devices: i2cdetect -y 1")
        print("  4. SCD40 should appear at address 0x62")

if __name__ == '__main__':
    test_scd40()