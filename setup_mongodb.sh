#!/bin/bash

# MongoDB Setup Script for Raspberry Pi Environmental Control System
# This script installs MongoDB locally for offline operation

echo "🍄 Setting up MongoDB for Environmental Control System"
echo "======================================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  This script is designed for Raspberry Pi"
    echo "   For other systems, please install MongoDB manually"
    exit 1
fi

# Check if MongoDB is already installed
if command -v mongod &> /dev/null; then
    echo "✅ MongoDB is already installed"
    echo "   Version: $(mongod --version | head -n 1)"
else
    echo "📦 Installing MongoDB..."
    
    # Add MongoDB GPG key
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
    
    # Add MongoDB repository
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
    
    # Update package list
    sudo apt-get update
    
    # Install MongoDB
    sudo apt-get install -y mongodb-org
    
    echo "✅ MongoDB installed successfully"
fi

# Create data directory
echo "📁 Setting up data directory..."
sudo mkdir -p /data/db
sudo chown -R $USER:$USER /data/db

# Create MongoDB configuration
echo "⚙️  Creating MongoDB configuration..."
sudo tee /etc/mongod.conf > /dev/null <<EOF
# MongoDB configuration for Environmental Control System
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

storage:
  dbPath: /data/db
  journal:
    enabled: true

processManagement:
  timeZoneInfo: /usr/share/zoneinfo

net:
  port: 27017
  bindIp: 127.0.0.1

operationProfiling:
  slowOpThresholdMs: 100

security:
  authorization: disabled
EOF

# Create log directory
sudo mkdir -p /var/log/mongodb
sudo chown -R $USER:$USER /var/log/mongodb

# Enable and start MongoDB service
echo "🚀 Starting MongoDB service..."
sudo systemctl enable mongod
sudo systemctl start mongod

# Wait for MongoDB to start
echo "⏳ Waiting for MongoDB to start..."
sleep 5

# Check if MongoDB is running
if sudo systemctl is-active --quiet mongod; then
    echo "✅ MongoDB is running"
else
    echo "❌ MongoDB failed to start"
    echo "   Check logs: sudo journalctl -u mongod"
    exit 1
fi

# Test MongoDB connection
echo "🔍 Testing MongoDB connection..."
if mongo --eval "db.runCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB connection test successful"
else
    echo "❌ MongoDB connection test failed"
    exit 1
fi

# Create database and collection
echo "🗄️  Setting up database..."
mongo --eval "
use sensor_db
db.createCollection('readings')
db.readings.createIndex({device_id: 1, server_timestamp: -1})
db.readings.createIndex({server_timestamp: -1})
print('Database and collections created successfully')
"

echo ""
echo "🎉 MongoDB setup completed successfully!"
echo ""
echo "📊 Database Information:"
echo "   - Database: sensor_db"
echo "   - Collection: readings"
echo "   - Port: 27017"
echo "   - Local connection: mongodb://localhost:27017"
echo ""
echo "🔧 Useful commands:"
echo "   - Start MongoDB: sudo systemctl start mongod"
echo "   - Stop MongoDB: sudo systemctl stop mongod"
echo "   - Check status: sudo systemctl status mongod"
echo "   - View logs: sudo journalctl -u mongod"
echo "   - Connect to MongoDB: mongo"
echo ""
echo "🌐 Your Environmental Control System will now:"
echo "   - Use local MongoDB for data storage"
echo "   - Sync with MongoDB Atlas when internet is available"
echo "   - Continue operating offline when internet is down"
echo ""
echo "🚀 You can now start your Environmental Control System!"