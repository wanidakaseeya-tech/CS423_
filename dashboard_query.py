import sqlite3

def get_dashboard_data():
    conn = sqlite3.connect('smart_building.db')
    cursor = conn.cursor()

    query = """
    SELECT 
        r.room_name, 
        s.temperature, 
        s.humidity, 
        s.pir_status, 
        s.occupancy_count
    FROM Rooms r
    JOIN Devices d ON r.room_id = d.room_id
    JOIN sensor_data s ON d.device_id = s.device_id
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"{'ROOM':<10} | {'TEMP (°C)':<10} | {'HUMID (%)':<10} | {'PIR STATUS'}")
    print("-" * 55)
    for row in rows:
        print(f"{row[0]:<10} | {row[1]:<10} | {row[2]:<10} | {row[3]} ({row[4]}/10)")

    conn.close()

if __name__ == "__main__":
    get_dashboard_data()