import sqlite3


class Trades:
    def __init__(self, dbname="traders.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        statement = """
        CREATE TABLE IF NOT EXISTS trades (
            owner TEXT, 
            name TEXT,
            buy_mc INTEGER NULL, 
            contract_address TEXT, 
            buy_amount INTEGER NULL
        )
        """
        self.conn.execute(statement)
        self.conn.commit()

    def add(self, owner, name, contract_address, _buy_mc=None, _buy_amount=None):
        try:
            statement = """
            INSERT INTO trades (owner, name, buy_mc, contract_address, buy_amount) 
            VALUES (?, ?, ?, ?, ?)
            """
            args = (owner, name, _buy_mc, contract_address, _buy_amount)
            self.conn.execute(statement, args)
            self.conn.commit()
        except Exception as e:
            return e

    def get_last_ca(self, owner):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT contract_address FROM trades WHERE owner = ? ORDER BY ROWID DESC LIMIT 1
            """, (owner,))
            last_ca = cursor.fetchone()
            return last_ca[0] if last_ca else None
        except Exception as e:
            return e

    def get_buy_mc(self, owner, contract_address):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT buy_mc FROM trades WHERE owner = ? AND contract_address = ? ORDER BY ROWID DESC LIMIT 1
            """, (owner, contract_address))
            buy_mc = cursor.fetchone()
            return buy_mc[0] if buy_mc else None
        except Exception as e:
            return e

    def get_buy_amt(self, owner, contract_address):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT buy_amount FROM trades WHERE owner = ? AND contract_address = ? ORDER BY ROWID DESC LIMIT 1
            """, (owner, contract_address))
            buy_amt = cursor.fetchone()
            return buy_amt[0] if buy_amt else None
        except Exception as e:
            return e

    def update(self, owner, contract_address, name=None, buy_mc=None, buy_amount=None):
        try:
            statement = """
            UPDATE trades 
            SET name=?, buy_mc=?, buy_amount=? 
            WHERE owner=? AND contract_address=?
            """
            args = (name, buy_mc, buy_amount, owner, contract_address)
            self.conn.execute(statement, args)
            self.conn.commit()
            return "Trade updated successfully"
        except Exception as e:
            return e

    def get_all(self, owner):
        statement = """
        SELECT owner, name, buy_mc, contract_address, buy_amount 
        FROM trades 
        WHERE owner = ?
        """
        args = (owner,)
        return [x for x in self.conn.execute(statement, args)]
