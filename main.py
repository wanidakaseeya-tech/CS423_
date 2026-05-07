import sqlite3

def get_current_status():
    """ฟังก์ชันสำหรับดึงสถานะล่าสุดของทุกห้องมาดู"""
    conn = sqlite3.connect('smart_building.db')
    cursor = conn.cursor()
    
    query = """
    SELECT r.room_name, s.temperature, s.humidity, s.pir_status
    FROM Rooms r
    JOIN Devices d ON r.room_id = d.room_id
    JOIN sensor_data s ON d.device_id = s.device_id
    """
    cursor.execute(query)
    for row in cursor.fetchall():
        print(f"ห้อง: {row[0]} | อุณหภูมิ: {row[1]}°C | ความชื้น: {row[2]}% | สถานะ: {row[3]}")
    conn.close()

# เรียกใช้เพื่อดูข้อมูลปัจจุบัน
if __name__ == "__main__":
    get_current_status()