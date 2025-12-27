# MQTT Broker Setup Guide

This directory contains the Docker Compose configuration for running an Eclipse Mosquitto MQTT broker with authentication support.

## Quick Start

### 1. Launch the Docker Compose

#### Prerequisites
- Docker and Docker Compose installed on your system
- Port 1883 (MQTT) and 9001 (WebSocket) available

#### Starting the Broker

```bash
cd devsimpy/DEVSKernel/BrokerDEVS/Brokers/mqtt
docker-compose up -d
```

The broker will start in detached mode. To view logs:

```bash
docker-compose logs -f mqtt5
```

#### Stopping the Broker

```bash
docker-compose down
```

---

## Password File Configuration

The Mosquitto broker is configured to use authentication. You must set up a password file before starting the broker.

### Create/Update Password File

#### Using mosquitto_passwd command (Recommended)

1. **Create a new password file with a user:**
   ```bash
   docker run --rm -it -v $(pwd)/config:/mosquitto/config eclipse-mosquitto mosquitto_passwd -c /mosquitto/config/pwfile <username>
   ```
   Replace `<username>` with your desired username (e.g., `devsimpy`).
   
   You will be prompted to enter and confirm a password.

2. **Add additional users to existing password file:**
   ```bash
   docker run --rm -it -v $(pwd)/config:/mosquitto/config eclipse-mosquitto mosquitto_passwd /mosquitto/config/pwfile <new_username>
   ```

#### Manual Password File Creation

If `mosquitto_passwd` is not available, you can create the file manually:

1. **Create the pwfile:**
   ```bash
   touch config/pwfile
   chmod 600 config/pwfile
   ```

2. **Add credentials** (password will be hashed):
   ```bash
   echo "username:password" >> config/pwfile
   ```

   Or use Python to generate a hashed password:
   ```python
   import hashlib
   import base64
   
   username = "devsimpy"
   password = "your_password_here"
   
   # Generate hashed password (Mosquitto uses SHA512)
   salt = os.urandom(16)
   hash_obj = hashlib.pbkdf2_hmac('sha512', password.encode(), salt, 100000)
   hashed = base64.b64encode(salt + hash_obj).decode()
   
   print(f"{username}:{hashed}")
   ```

### File Permissions

The password file must have restricted permissions:

```bash
chmod 600 config/pwfile
```

Mosquitto will not start if the file has overly permissive permissions (must be readable only by owner).

---

## Configuration File

The broker configuration is defined in `config/mosquitto.conf`:

```properties
allow_anonymous false          # Disable anonymous connections
listener 1883                  # MQTT protocol port
listener 9001                  # WebSocket protocol port
protocol websockets            # Enable WebSocket support
persistence true               # Enable message persistence
password_file /mosquitto/config/pwfile  # Path to password file
persistence_file mosquitto.db  # Database filename
persistence_location /mosquitto/data/   # Database location
```

### Customizing Configuration

Edit `config/mosquitto.conf` to modify:
- Listener ports
- Authentication settings
- Persistence options
- Log levels

Changes take effect after restarting the container:

```bash
docker-compose restart mqtt5
```

---

## Directory Structure

```
mqtt/
├── docker-compose.yml          # Docker Compose configuration
├── config/                     # Mosquitto configuration directory
│   ├── mosquitto.conf          # Main configuration file
│   └── pwfile                  # User credentials (auto-generated)
├── data/                       # Persistent data directory
│   └── mosquitto.db            # Message persistence database
├── log/                        # Log directory
│   └── mosquitto.log           # Broker logs
└── README.md                   # This file
```

---

## Connecting to the Broker

### Using Default Credentials

After setting up the password file, use these connection parameters:

**Python (paho-mqtt):**
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.username_pw_set("devsimpy", "your_password")
client.connect("localhost", 1883, 60)
```

**DEVSimPy MQTT Configuration:**
Edit your configuration to use:
```python
MQTT_BROKER_ADDRESS = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = "devsimpy"
MQTT_PASSWORD = "your_password"
```

### Test Connection

```bash
# Using mosquitto_pub/mosquitto_sub
mosquitto_pub -h localhost -u devsimpy -P your_password -t test/topic -m "Hello MQTT"
mosquitto_sub -h localhost -u devsimpy -P your_password -t test/topic
```

---

## Troubleshooting

### Broker fails to start
- **Check permissions**: `chmod 600 config/pwfile`
- **Verify port availability**: `netstat -an | grep 1883`
- **View logs**: `docker-compose logs mqtt5`

### Authentication fails
- **Verify credentials**: Check `config/pwfile` exists and is readable
- **Reset password**: Delete `pwfile` and recreate with new credentials
- **Check configuration**: Ensure `password_file` path in `mosquitto.conf` is correct

### Persistence not working
- **Check permissions**: `ls -la data/`
- **Verify location**: `persistence_location` in `mosquitto.conf` must be writable

### Port already in use
- **Change ports in docker-compose.yml**: Modify port mappings
- **Kill existing process**: `lsof -i :1883` then `kill -9 <PID>`

---

## Advanced: Anonymous Access (Development Only)

To enable anonymous access for testing:

1. Edit `config/mosquitto.conf`:
   ```properties
   allow_anonymous true
   ```

2. Restart the broker:
   ```bash
   docker-compose restart mqtt5
   ```

⚠️ **Note**: This disables authentication and should only be used for development/testing.

---

## Resources

- [Eclipse Mosquitto Documentation](https://mosquitto.org/)
- [Mosquitto Configuration Manual](https://mosquitto.org/man/mosquitto-conf-5.html)
- [Docker Hub - Eclipse Mosquitto](https://hub.docker.com/_/eclipse-mosquitto)
- [paho-mqtt Python Client](https://github.com/eclipse/paho.mqtt.python)

