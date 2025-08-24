#!/usr/bin/env python3
"""
Test script for ultrasonic water level sensor
Uses GPIO Zero DistanceSensor
"""

import time
from gpiozero import DistanceSensor

def test_ultrasonic():
    print("🧪 Testing Ultrasonic Water Level Sensor...")
    print("📍 Expected connections:")
    print("  - Trigger → GPIO 23")
    print("  - Echo → GPIO 24") 
    print("  - VCC → 5V (Pin 2 or 4)")
    print("  - GND → Ground (Pin 6, 9, 14, 20, 25, 30, 34, 39)")
    print()
    
    try:
        # Initialize ultrasonic sensor
        water_sensor = DistanceSensor(echo=24, trigger=23, max_distance=1)
        print("✅ Ultrasonic sensor initialized")
        
        print("📏 Taking distance measurements...")
        print("   (Place sensor above water reservoir)")
        print()
        
        for i in range(10):
            try:
                distance_m = water_sensor.distance
                distance_cm = distance_m * 100
                
                # Calculate water level percentage (example calculation)
                # Assuming reservoir is 30cm deep and sensor is 35cm above bottom
                sensor_height = 35  # cm above bottom
                max_water_depth = 30  # cm
                min_water_depth = 5   # cm
                
                water_depth = sensor_height - distance_cm
                water_depth = max(0, min(max_water_depth, water_depth))
                
                if water_depth <= min_water_depth:
                    water_percentage = 0.0
                else:
                    water_percentage = ((water_depth - min_water_depth) / (max_water_depth - min_water_depth)) * 100
                
                print(f"📊 Reading {i+1}:")
                print(f"  📏 Distance: {distance_cm:.1f} cm")
                print(f"  🌊 Water depth: {water_depth:.1f} cm")
                print(f"  💧 Water level: {water_percentage:.1f}%")
                
                if water_percentage < 15:
                    print("  🚨 LOW WATER ALERT!")
                elif water_percentage < 30:
                    print("  ⚠️  Water level warning")
                else:
                    print("  ✅ Water level OK")
                print()
                
            except Exception as e:
                print(f"❌ Reading {i+1} failed: {e}")
            
            time.sleep(2)
        
        print("✅ Ultrasonic sensor test completed!")
        
    except Exception as e:
        print(f"❌ Ultrasonic sensor test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check wiring connections")
        print("  2. Verify GPIO pins 23 and 24 are not used by other devices")
        print("  3. Ensure sensor has proper 5V power supply")
        print("  4. Check for loose connections")

if __name__ == '__main__':
    test_ultrasonic()