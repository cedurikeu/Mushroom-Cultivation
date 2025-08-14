# 🏠 IoT Raspberry Pi Monitoring System

A comprehensive IoT monitoring system that displays real-time sensor data from your Raspberry Pi with MongoDB Atlas cloud storage and local SQLite fallback when WiFi is unavailable.

## ✨ Features

- **🔐 Password Protected Dashboard** - Secure access to your sensor data
- **☁️ MongoDB Atlas Integration** - Cloud storage for your sensor readings
- **💾 Local SQLite Fallback** - Automatic fallback when WiFi is down
- **📊 Real-time Data Display** - Live sensor readings with WebSocket updates
- **📈 Interactive Charts** - Historical data visualization with Chart.js
- **📱 Responsive Design** - Works on desktop, tablet, and mobile devices
- **🔄 Automatic Database Switching** - Seamlessly switches between MongoDB and SQLite

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
MONGODB_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/sensor_db?retryWrites=true&w=majority
SECRET_KEY=your-super-secret-key-here
DASHBOARD_PASSWORD=your-secure-password
```

### 3. Run the Application

```bash
python app.py
```

### 4. Access the Dashboard

1. Open your browser to `http://localhost:5000`
2. Enter your dashboard password (default: `admin123`)
3. View your real-time sensor data!

## 🔧 Configuration

### MongoDB Atlas Setup

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new cluster
3. Create a database user
4. Get your connection string
5. Add it to your `.env` file

### Local SQLite Fallback

The system automatically creates a local SQLite database (`sensor_data.db`) that will be used when:
- MongoDB connection fails
- WiFi is unavailable
- Network issues occur

The system will automatically switch back to MongoDB when the connection is restored.

## 📊 API Endpoints

- `GET /` - Dashboard (requires authentication)
- `GET /login` - Login page
- `GET /logout` - Logout
- `GET /api/current` - Current sensor reading
- `GET /api/latest` - Recent readings (last 10)
- `GET /api/history` - Historical data (last 24 hours)
- `GET /api/status` - Database status

## 🔌 Real-time Updates

The dashboard uses WebSocket connections for real-time updates:
- Sensor data updates every 10 seconds
- Automatic reconnection on connection loss
- Live status indicators

## 📱 Mobile Responsive

The dashboard is fully responsive and works great on:
- 📱 Mobile phones
- 📱 Tablets
- 💻 Desktop computers

## 🛠️ Customization

### Adding New Sensors

To add new sensors, modify the `SensorService.simulate_realistic_data()` method in `app.py`:

```python
def simulate_realistic_data(self):
    # Add your sensor reading logic here
    self.current_data = {
        'temperature': temperature_value,
        'humidity': humidity_value,
        'co2': co2_value,
        'your_new_sensor': new_sensor_value,  # Add this
        'timestamp': datetime.utcnow().isoformat(),
        'device_id': DEVICE_ID
    }
```

### Changing Update Intervals

Modify the `SENSOR_READ_INTERVAL` constant in `app.py`:

```python
SENSOR_READ_INTERVAL = 10  # seconds
```

## 🔒 Security

- Password-protected dashboard access
- Session-based authentication
- CORS protection
- Input validation

## 📈 Database Schema

### MongoDB Collection: `readings`
```json
{
  "_id": "ObjectId",
  "device_id": "raspberry-pi-01",
  "temperature": 24.5,
  "humidity": 65.3,
  "co2": 850,
  "timestamp": "2025-01-13T10:00:00.000Z",
  "server_timestamp": "2025-01-13T10:00:01.123Z"
}
```

### SQLite Table: `readings`
```sql
CREATE TABLE readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    temperature REAL,
    humidity REAL,
    co2 INTEGER,
    timestamp TEXT,
    server_timestamp TEXT
);
```

## 🐛 Troubleshooting

### MongoDB Connection Issues
- Check your connection string in `.env`
- Verify network connectivity
- Check MongoDB Atlas IP whitelist
- The system will automatically fall back to SQLite

### Port Already in Use
```bash
# Kill process using port 5000
sudo lsof -t -i tcp:5000 | xargs kill -9
```

### Permission Issues
```bash
# Make sure you have write permissions for SQLite
chmod 755 .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

If you encounter any issues:
1. Check the console output for error messages
2. Verify your `.env` configuration
3. Check network connectivity
4. Review the troubleshooting section above

---

**Happy Monitoring!** 🎉