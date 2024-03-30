import sqlite3
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.create_database()

    def create_database(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            # Create APIKeys table if it doesn't exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS APIKeys (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                apiKey TEXT UNIQUE,
                                tokenAmount INTEGER DEFAULT 0
                            )''')
            # Create Transactions table if it doesn't exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                apiKey TEXT,
                                transactionType TEXT,
                                amount INTEGER,
                                date TEXT,
                                other TEXT
                            )''')
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error:", e)

    def add_api_key(self, api_key):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO APIKeys (apiKey) VALUES (?)", (api_key,))
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error:", e)

    def update_token_amount(self, api_key, amount):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE APIKeys SET tokenAmount = tokenAmount + ? WHERE apiKey = ?", (amount, api_key))
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error:", e)

    def add_transaction(self, api_key, transaction_type, amount, other=None):
        try:
            cursor = self.conn.cursor()
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO Transactions (apiKey, transactionType, amount, date, other) VALUES (?, ?, ?, ?, ?)",
                           (api_key, str(transaction_type), amount, date, other))
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error:", e)

    def get_token_amount(self, api_key):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT tokenAmount FROM APIKeys WHERE apiKey = ?", (api_key,))
            result = cursor.fetchone()
            if result:
                return int(result[0])
            else:
                return None
        except sqlite3.Error as e:
            print("Error:", e)
            return None

    def close_connection(self):
        if self.conn:
            self.conn.close()