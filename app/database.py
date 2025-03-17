# database.py
import sqlite3
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")

DB_NAME = os.getenv('DB_NAME')

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                duration TEXT,
                time TEXT,
                class_name TEXT,
                last_name TEXT,
                first_name TEXT,
                phone TEXT,
                room_number TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()

def save_booking(data):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE date = ? AND time = ? AND class_name = ? AND status = 'pending'
        """, (data['date'], data['time'], data['class_name']))
        
        if cursor.fetchone()[0] > 0:
            logging.warning("Запись с таким временем уже существует, не сохраняем!")
            return False

        cursor.execute("""
            INSERT INTO bookings (
                user_id, date, duration, time, class_name, last_name, first_name, phone, room_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['user_id'], data['date'], data['duration'], data['time'],
            data['class_name'], data['last_name'], data['first_name'],
            data['phone'], data['room_number']
        ))
        conn.commit()
        
    return True

def get_user_bookings(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, time, class_name FROM bookings WHERE user_id = ? AND status = 'pending'", (user_id,))
        return cursor.fetchall()
    
def cancel_booking(booking_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET status = 'canceled' WHERE id = ?", (booking_id,))
        conn.commit()

def get_today_bookings():
    today = datetime.today().strftime('%Y-%d-%m')
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Убрана проверка на приоритетные user_id
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE date = ? AND status = 'pending'
            ORDER BY id
        """, (today,))
        return cursor.fetchall()

def update_booking_status(booking_id, status):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        conn.commit()

def is_time_slot_taken(date, time_slot, class_name):
    logging.info(f"Проверка времени: дата={date}, время={time_slot}, класс={class_name}")
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        try:
            date_obj = datetime.strptime(date, "%Y-%d-%m")
            date = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            logging.error(f"Некорректный формат даты: {date}")
            return False

        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE date = ? AND time = ? AND class_name = ? AND status = 'pending'
        """, (date, time_slot, class_name))

        result = cursor.fetchone()[0]
        logging.info(f"Найдено совпадений: {result}")
        
        return result > 0