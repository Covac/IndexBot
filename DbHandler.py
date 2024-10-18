import sqlite3
from datetime import datetime, timezone#,UTC UTC caused crashes on fly for some reason, reverting back to UrcNow
#Maybe raise errors so that we know when something goes wrong?

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
            # Create Orders table if it doesn't exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS Orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    apiKey TEXT,
                    sessionKey TEXT,
                    paymentAddress TEXT,
                    dateStart TEXT,
                    dateEnd TEXT,
                    txAmount INTEGER,
                    status TEXT,
                    other TEXT
                )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS Addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paymentAddress TEXT,
                    pskJSON TEXT,
                    pvkJSON TEXT
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
            cursor.execute("UPDATE APIKeys SET tokenAmount = tokenAmount + ? WHERE apiKey = ?", (amount, api_key,))
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error:", e)

    def add_transaction(self, api_key, transaction_type, amount, other='UNDEF'):
        try:
            cursor = self.conn.cursor()
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO Transactions (apiKey, transactionType, amount, date, other) VALUES (?, ?, ?, ?, ?)",
                           (api_key, str(transaction_type), amount, date, other,))
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
        
    def add_order(self, api_key, session_key, paymentAddr, other='not specified'):
        try:
            cursor = self.conn.cursor()
            date_start = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            status = "PENDING"  # You can set the initial status here
            cursor.execute("INSERT INTO Orders (apiKey, sessionKey, paymentAddress, dateStart, status, other) VALUES (?, ?, ?, ?, ?, ?)",
                           (api_key, session_key, paymentAddr, date_start, status, other,))
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error:", e)

    def add_payment_address(self, address, psk_json, pvk_json):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Addresses (paymentAddress, pskJSON, pvkJSON) VALUES (?, ?, ?)",
                           (address, psk_json, pvk_json,))
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error:", e)

    def check_order_exists(self,session_key):#this is pretty much sanity check function
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM Orders WHERE sessionKey=?)",(session_key,))
            result = cursor.fetchone()
            #just to be sure we do it stupid way, also these should 100% be ints
            if result[0] == 1:
                return True
            elif result[0] == 0:
                return False
            else:
                raise(RuntimeError,'Unexpected return from database!')
        except sqlite3.Error as e:
            print("Error:", e)

    def check_apikey_exists(self,apiKey):#this is pretty much sanity check function
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM APIKeys WHERE apiKey=?)",(apiKey,))
            result = cursor.fetchone()
            #just to be sure we do it stupid way, also these should 100% be ints
            if result[0] == 1:
                return True
            elif result[0] == 0:
                return False
            else:
                raise(RuntimeError,'Unexpected return from database!')
        except sqlite3.Error as e:
            print("Error:", e)

    def get_apikey_addr_from_order(self,session_key):
        try:
            cursor = self.conn.cursor()
            r = cursor.execute("SELECT apiKey, paymentAddress, status FROM Orders WHERE sessionKey=?",(session_key,))
            order_data_minimal = r.fetchone()
            return order_data_minimal[0], order_data_minimal[1], order_data_minimal[2]
        except sqlite3.Error as e:
            print("Error:", e)

    def get_payment_addrs(self):
        try:
            cursor = self.conn.cursor()
            r = cursor.execute("SELECT * FROM Addresses")
            data = r.fetchall()
            usable = []
            for d in data:
                id,addr,psk,pvk = d
                prepare = {'id':id,'addr':addr,'psk':psk,'pvk':pvk}
                usable.append(prepare)
            return usable #now we have nice and structured addresses
        except sqlite3.Error as e:
            print("Error:", e)

    def confirm_order(self, txAmount, status, apiKey, sessionKey, other='IP not specified'):
        try:
            cursor = self.conn.cursor()
            date_end = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""UPDATE Orders SET dateEnd=?, txAmount=?, status=?, other=? WHERE apiKey=? AND sessionKey=?""", (date_end,txAmount,status,other,apiKey,sessionKey,))
        except sqlite3.Error as e:
            print("Error:", e)
    
    def show_table(self,TABLE,returnValues = False):
        try:
            cursor = self.conn.cursor()
            for row in cursor.execute(f"SELECT * FROM {TABLE}"):#I know its unsafe but it gave me errors for no reason
                print(row)
        except sqlite3.Error as e:
            print("Error:", e)

    def show_tables(self):
        try:
            cursor = self.conn.cursor()
            r = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            print(r.fetchall())
        except sqlite3.Error as e:
            print("Error:", e)

    def close_connection(self):
        if self.conn:
            self.conn.close()

def get_db():#for ssh
    db = DatabaseHandler('data.db')
    print("use db.METHOD()")
    print(dir(db))
    print("Tables: ")
    db.show_tables()
    return db
