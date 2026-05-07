"""
SmartSense Pro — Flask API Server + MQTT Listener
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3, os, json, threading, time, random
import paho.mqtt.client as mqtt

app = Flask(__name__)
CORS(app)

DB_PATH     = os.path.join(os.path.dirname(__file__), 'smart_building.db')
MQTT_BROKER = 'broker.hivemq.com'
MQTT_PORT   = 1883
MQTT_TOPIC  = 'jennifer/iot/smartsense/all'

room_occupancy    = {'r1': 0, 'r2': 0, 'r3': 0}
last_motion       = {'r1': 0, 'r2': 0, 'r3': 0}
last_counted_time = {'r1': 0.0, 'r2': 0.0, 'r3': 0.0}
MOTION_COOLDOWN   = 3.0

ROOM_MAP = {'r1': 'Room A', 'r2': 'Room B', 'r3': 'Room C'}

def get_device_id(cursor, room_name):
    cursor.execute("""
        SELECT d.device_id FROM Devices d
        JOIN Rooms r ON d.room_id = r.room_id
        WHERE r.room_name = ? LIMIT 1
    """, (room_name,))
    row = cursor.fetchone()
    return row[0] if row else None

def save_reading(room_key, t, h, motion):
    room_name  = ROOM_MAP.get(room_key)
    if not room_name: return
    pir_status = 'Motion Detected' if motion == 1 else 'No Motion Detected'
    occupancy  = room_occupancy[room_key]
    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        dev_id = get_device_id(cursor, room_name)
        if dev_id:
            cursor.execute("""
                INSERT INTO sensor_data (device_id, temperature, humidity, pir_status, occupancy_count)
                VALUES (?, ?, ?, ?, ?)
            """, (dev_id, t, h, pir_status, occupancy))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f'[DB ERROR] {e}')

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)
        print(f'[MQTT] Connected — subscribed to {MQTT_TOPIC}')
    else:
        print(f'[MQTT] Connection failed, rc={rc}')

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except Exception:
        return

    now = time.time()
    for room_key in ROOM_MAP:
        room_data = data.get(room_key)
        if not room_data: continue

        t      = room_data.get('t')
        h      = room_data.get('h')
        motion = int(room_data.get('m', 0))

        # Cooldown-based count — handles ESP32 instant reset pattern
        if motion == 1 and (now - last_counted_time[room_key]) > MOTION_COOLDOWN:
            last_counted_time[room_key] = now
            if room_occupancy[room_key] < 10:
                room_occupancy[room_key] += 1

        last_motion[room_key] = motion
        save_reading(room_key, t, h, motion)

    print(f'[MQTT] Saved | A:{room_occupancy["r1"]}/10  B:{room_occupancy["r2"]}/10  C:{room_occupancy["r3"]}/10')

def start_mqtt():
    client = mqtt.Client(client_id=f'SmartSense_Server_{random.randint(1000,9999)}')
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()

@app.route('/api/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.room_name, s.temperature, s.humidity, s.pir_status, s.occupancy_count, s.timestamp
        FROM sensor_data s
        JOIN Devices d ON s.device_id = d.device_id
        JOIN Rooms r ON d.room_id = r.room_id
        ORDER BY s.timestamp DESC LIMIT 200
    """)
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{'room': r[0], 'temp': r[1], 'humidity': r[2], 'pir_status': r[3], 'occupancy': r[4], 'timestamp': r[5]} for r in rows])

@app.route('/api/history/<room_name>', methods=['GET'])
def get_room_history(room_name):
    full_name = f'Room {room_name.upper()}'
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.room_name, s.temperature, s.humidity, s.pir_status, s.occupancy_count, s.timestamp
        FROM sensor_data s
        JOIN Devices d ON s.device_id = d.device_id
        JOIN Rooms r ON d.room_id = r.room_id
        WHERE r.room_name = ?
        ORDER BY s.timestamp DESC LIMIT 200
    """, (full_name,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return jsonify({'error': f'{full_name} not found'}), 404
    return jsonify([{'room': r[0], 'temp': r[1], 'humidity': r[2], 'pir_status': r[3], 'occupancy': r[4], 'timestamp': r[5]} for r in rows])

@app.route('/api/occupancy', methods=['GET'])
def get_occupancy():
    return jsonify({'Room A': room_occupancy['r1'], 'Room B': room_occupancy['r2'], 'Room C': room_occupancy['r3']})

if __name__ == '__main__':
    print('\n✅ SmartSense Pro — Server starting')
    print(f'   Listening to MQTT: {MQTT_BROKER} → {MQTT_TOPIC}')
    print('   GET  http://localhost:5000/api/history')
    print('   GET  http://localhost:5000/api/history/A  (or B, C)')
    print('   GET  http://localhost:5000/api/occupancy\n')
    threading.Thread(target=start_mqtt, daemon=True).start()
    app.run(debug=False, port=5000)