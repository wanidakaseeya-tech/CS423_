import sqlite3

def setup_smart_sense():
    conn = sqlite3.connect('smart_building.db')
    cursor = conn.cursor()

    # ลบตารางเก่า
    cursor.execute("DROP TABLE IF EXISTS sensor_data")
    cursor.execute("DROP TABLE IF EXISTS Devices")
    cursor.execute("DROP TABLE IF EXISTS Rooms")

    # 1. ตารางห้อง (ตามหน้าจอมี A, B, C)
    cursor.execute("CREATE TABLE Rooms (room_id INTEGER PRIMARY KEY, room_name TEXT, floor INTEGER)")
    
    # 2. ตารางอุปกรณ์ (อ้างอิง PIR และ DHT22 ตามภาพ)
    cursor.execute("""
    CREATE TABLE Devices (
        device_id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_name TEXT,
        device_type TEXT,
        room_id INTEGER,
        FOREIGN KEY (room_id) REFERENCES Rooms(room_id)
    )
    """)

    # 3. ตารางข้อมูลเซนเซอร์ (เก็บค่า Temp, Humid และ PIR Status)
    cursor.execute("""
    CREATE TABLE sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        temperature REAL,
        humidity INTEGER,
        pir_status TEXT, -- 'No Motion Detected' หรือ 'Motion Detected'
        occupancy_count INTEGER, -- เช่น (0/10)
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES Devices(device_id)
    )
    """)

    # --- เพิ่มข้อมูลให้เหมือนในภาพ Dashboard ---
    
    # เพิ่มห้อง
    rooms = [(1, 'Room A', 1), (2, 'Room B', 1), (3, 'Room C', 1)]
    cursor.executemany("INSERT INTO Rooms VALUES (?, ?, ?)", rooms)

    # เพิ่มอุปกรณ์ให้แต่ละห้อง
    devices = [
        ('DHT22-A', 'Multi-Sensor', 1),
        ('DHT22-B', 'Multi-Sensor', 2),
        ('DHT22-C', 'Multi-Sensor', 3)
    ]
    cursor.executemany("INSERT INTO Devices (device_name, device_type, room_id) VALUES (?, ?, ?)", devices)

    # เพิ่มข้อมูลเซนเซอร์ให้ตรงตามหน้าจอเป๊ะๆ
    sensor_readings = [
        (1, 23.5, 28, 'No Motion Detected', 0), # Room A
        (2, 24.4, 82, 'No Motion Detected', 0), # Room B
        (3, 25.2, 85, 'No Motion Detected', 0)  # Room C
    ]
    cursor.executemany("""
    INSERT INTO sensor_data (device_id, temperature, humidity, pir_status, occupancy_count) 
    VALUES (?, ?, ?, ?, ?)""", sensor_readings)

    conn.commit()
    conn.close()
    print("✅ ฐานข้อมูลถูกตั้งค่าตามหน้าจอ SmartSense Pro เรียบร้อยแล้ว!")

if __name__ == "__main__":
    setup_smart_sense()