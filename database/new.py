import sqlite3

class Trade:
    def __init__(self, database='trades.sqlite'):
        self.conn = sqlite3.connect(database)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                contract_address TEXT NOT NULL,
                name TEXT NOT NULL,
                buy_mc REAL,
                buy_amt REAL
            )
        """)
        self.conn.commit()

    def insert_trade(self, owner, contract_address, name):
        self.cursor.execute("""
            INSERT INTO trades (owner, contract_address, name)
            VALUES (?, ?, ?)
        """, (owner, contract_address, name))
        self.conn.commit()

    def get_name(self, contract_address, owner):
        self.cursor.execute("""
            SELECT name FROM trades
            WHERE contract_address = ? AND owner = ?
        """, (contract_address, owner))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_last_contract_address(self, owner):
        self.cursor.execute("""
            SELECT contract_address FROM trades
            WHERE owner = ?
            ORDER BY id DESC
            LIMIT 1
        """, (owner,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_buy_mc(self, contract_address, owner):
        self.cursor.execute("""
            SELECT buy_mc FROM trades
            WHERE contract_address = ? AND owner = ?
        """, (contract_address, owner))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_trade(self, contract_address, owner, buy_mc=None, buy_amt=None):
        update_query = "UPDATE trades SET "
        params = []

        if buy_mc is not None:
            update_query += "buy_mc = ?, "
            params.append(buy_mc)

        if buy_amt is not None:
            update_query += "buy_amt = ?, "
            params.append(buy_amt)

        update_query = update_query.rstrip(", ") + " WHERE contract_address = ? AND owner = ?"
        params.extend([contract_address, owner])

        self.cursor.execute(update_query, params)
        self.conn.commit()

    def __del__(self):
        self.conn.close()
