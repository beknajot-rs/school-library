import sqlite3
import os

# Use /tmp for Vercel's serverless environment, otherwise use local directory
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/library.db'
else:
    DB_PATH = 'library.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create Settings Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            school_address TEXT,
            principal_name TEXT,
            standard_loan_days INTEGER DEFAULT 14
        )
    ''')
    
    # Default settings if none exist
    c.execute('SELECT COUNT(*) FROM settings')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO settings (school_name, school_address, principal_name, standard_loan_days)
            VALUES (?, ?, ?, ?)
        ''', ('Maktab Kutubxonasi', 'Manzil', 'Direktor', 14))

    # Create Classes Table for settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Create Categories Table for settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Create Books Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_number TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT,
            grade_level TEXT,
            total_copies INTEGER NOT NULL,
            publisher TEXT,
            publish_year TEXT,
            isbn TEXT,
            notes TEXT,
            status TEXT DEFAULT 'Yaxshi'
        )
    ''')
    
    # Create Students Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            grade_level TEXT NOT NULL,
            parent_phone TEXT,
            status TEXT DEFAULT 'Faol'
        )
    ''')
    
    # Create Loans Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status TEXT DEFAULT 'Faol',
            returned_condition TEXT,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
