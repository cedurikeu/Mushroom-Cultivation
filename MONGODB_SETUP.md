# MongoDB-Only Environmental Control System Setup

## Overview

This system now uses MongoDB exclusively for data storage, with the following architecture:

- **Local MongoDB**: Primary database running on the Raspberry Pi
- **MongoDB Atlas**: Cloud database for remote access and backup
- **Offline Operation**: System continues working when internet is down
- **Automatic Sync**: Data syncs to Atlas when internet connection is restored

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sensors &     │    │   Local MongoDB │    │  MongoDB Atlas  │
│   GPIO Control  │───▶│   (Raspberry Pi)│───▶│   (Cloud)       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        ▲
                              │                        │
                              └──────── Sync ──────────┘
```

## Prerequisites

1. **Raspberry Pi** with Raspberry Pi OS
2. **Internet connection** (for initial setup and Atlas sync)
3. **MongoDB Atlas account** (optional, for cloud backup)

## Installation Steps

### 1. Install Local MongoDB

Run the setup script to install MongoDB locally:

```bash
./setup_mongodb.sh
```

This script will:
- Install MongoDB on your Raspberry Pi
- Configure the database for local operation
- Create necessary directories and permissions
- Set up the `sensor_db` database with proper indexes
- Enable MongoDB as a system service

### 2. Configure Environment Variables

Create a `.env` file in your project directory:

```bash
# Required
SECRET_KEY=your-secret-key-here
DASHBOARD_PASSWORD=your-dashboard-password

# Optional - MongoDB Atlas connection
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/sensor_db?retryWrites=true&w=majority
```

### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Start the System

```bash
python3 app.py
```

## How It Works

### Online Mode (Atlas Connected)
- Data is saved to local MongoDB first
- Data is immediately synced to MongoDB Atlas
- You can access data from anywhere via Atlas
- Real-time monitoring and control via web dashboard

### Offline Mode (No Internet)
- Data is saved only to local MongoDB
- System continues operating normally
- All sensor readings and controls work
- Web dashboard remains functional

### Sync Process
- When internet connection is restored, system automatically detects Atlas
- All offline data is synced to Atlas
- No data loss during internet outages
- Sync happens in background without interrupting operation

## Database Schema

### Local MongoDB Collections

```javascript
// readings collection
{
  _id: ObjectId,
  device_id: "raspberry-pi-01",
  temperature: 22.5,
  humidity: 85.2,
  co2: 1200,
  light_intensity: 450,
  water_level: 75.0,
  timestamp: "2024-01-15T10:30:00.000Z",
  server_timestamp: "2024-01-15T10:30:00.000Z",
  synced_to_atlas: true  // Local only - tracks sync status
}
```

### Atlas MongoDB Collections
```javascript
// Same schema as local, but without synced_to_atlas field
{
  _id: ObjectId,
  device_id: "raspberry-pi-01",
  temperature: 22.5,
  humidity: 85.2,
  co2: 1200,
  light_intensity: 450,
  water_level: 75.0,
  timestamp: "2024-01-15T10:30:00.000Z",
  server_timestamp: "2024-01-15T10:30:00.000Z"
}
```

## Monitoring and Management

### Check Database Status

The web dashboard shows:
- **Database Type**: "Local MongoDB" or "MongoDB Atlas"
- **Atlas Status**: Connected/Offline indicator
- **Offline Mode**: Shows when operating without internet

### MongoDB Commands

```bash
# Check MongoDB status
sudo systemctl status mongod

# View MongoDB logs
sudo journalctl -u mongod

# Connect to MongoDB shell
mongo

# Check database
use sensor_db
show collections
db.readings.find().sort({server_timestamp: -1}).limit(5)
```

### Data Backup

#### Local Backup
```bash
# Backup local database
mongodump --db sensor_db --out /backup/$(date +%Y%m%d)

# Restore local database
mongorestore --db sensor_db /backup/20240115/sensor_db/
```

#### Atlas Backup
- Atlas provides automatic backups
- Configure backup schedule in Atlas dashboard
- Export data via Atlas Data Explorer

## Troubleshooting

### MongoDB Won't Start
```bash
# Check if MongoDB is installed
which mongod

# Check service status
sudo systemctl status mongod

# View detailed logs
sudo journalctl -u mongod -f

# Restart MongoDB
sudo systemctl restart mongod
```

### Connection Issues
```bash
# Test local MongoDB connection
mongo --eval "db.runCommand('ping')"

# Check if port 27017 is open
netstat -tlnp | grep 27017

# Check MongoDB configuration
cat /etc/mongod.conf
```

### Sync Issues
- Check internet connection
- Verify Atlas connection string in `.env`
- Check Atlas network access settings
- Review application logs for sync errors

## Performance Optimization

### Local MongoDB
- Indexes are automatically created for optimal query performance
- Data is stored locally for fast access
- No network latency for local operations

### Atlas Sync
- Sync happens in background
- Only unsynced data is transferred
- Automatic retry on connection failures

## Security Considerations

### Local MongoDB
- Bound to localhost only (127.0.0.1)
- No authentication required for local access
- Data stored on local filesystem

### Atlas Security
- Use strong passwords for Atlas accounts
- Enable IP whitelist in Atlas
- Use connection string with proper credentials
- Enable MongoDB Atlas security features

## Migration from SQLite

If you're migrating from the previous SQLite version:

1. **Backup SQLite data**:
   ```bash
   cp sensor_data.db sensor_data_backup.db
   ```

2. **Install MongoDB** using the setup script

3. **Start the new system** - it will use MongoDB from now on

4. **Optional**: Import old SQLite data to MongoDB (requires custom script)

## Benefits of MongoDB-Only Architecture

1. **No Data Loss**: Local storage ensures data persistence
2. **Offline Operation**: System works without internet
3. **Automatic Sync**: Seamless cloud backup when online
4. **Better Performance**: MongoDB is faster than SQLite for this use case
5. **Scalability**: Easy to add more devices or features
6. **Remote Access**: View data from anywhere via Atlas
7. **Simplified Code**: No complex fallback logic

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review MongoDB and application logs
3. Verify network connectivity for Atlas sync
4. Ensure proper permissions and configuration