import sqlite3


"""
This class is responsible for saving User Data on Database

"""

class User:
    
    def __init__(self, dbname = "users.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)


    def setup(self):
        statement1 = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, chatid INTEGER UNIQUE, mnemonics TEXT UNIQUE, wallet TEXT UNIQUE, slippage FLOAT DEFAULT 0.2 )"
        self.conn.execute(statement1)
        self.conn.commit()


    def add_user(self, username_, mnemonics, wallet):
        statement = "INSERT OR IGNORE INTO users (chatid, mnemonics, wallet) VALUES (?, ?, ?)"
        args = (username_, mnemonics, wallet)
        self.conn.execute(statement, args)
        self.conn.commit()
    

    def update_slippage(self, amount, userid):
        statement = "UPDATE users SET slippage = ? WHERE chatid = ?"
        args = (amount, userid)
        self.conn.execute(statement, args)
        self.conn.commit()
        
        
        
    def get_slippage(self, owner):
        statement = "SELECT slippage FROM users WHERE chatid = ?"
        args = (owner,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    
    
    def get_wallet(self, owner):
        statement = "SELECT wallet FROM users WHERE chatid = ?"
        args = (owner,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    
    
    
    def get_mnemonics(self, owner):
        statement = "SELECT mnemonics FROM users WHERE chatid = ?"
        args = (owner,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None


    def get_users(self):
        statement = "SELECT chatid FROM users"
        return [x[0] for x in self.conn.execute(statement)]



class Trade:
    
    def __init__(self, dbname="trades.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)
        
    def setup(self):
        statement = "CREATE TABLE IF NOT EXISTS trades (owner TEXT, buy_mc INTEGER NULL, sell_mc INTEGER NULL, contract_address TEXT, pnl INTEGER NULL, buy_amount INTEGER NULL, token_balance INTEGER NULL)"
        self.conn.execute(statement)
        self.conn.commit()
        
        
    def add_trade(self, owner, contract_address, _buy_mc=None, _sell_mc=None, _pnl=None, _buy_amount=None, _token_balance=None):
        try:
            statement = "INSERT INTO trades (owner, buy_mc, sell_mc, contract_address, pnl, buy_amount, token_balance) VALUES (?, ?, ?, ?, ?, ?, ?)"
            args = (owner, _buy_mc, _sell_mc, contract_address, _pnl, _buy_amount, _token_balance)
            self.conn.execute(statement, args)
            self.conn.commit()
        except Exception as e:
            return e
    
    def retrieve_last_ca(self, owner):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT contract_address FROM trades WHERE owner = ? ORDER BY ROWID DESC LIMIT 1''', (owner,))
            last_ca = cursor.fetchone()
            if last_ca:
                return last_ca[0]
            else:
                return None
        except Exception as e:
            return e
        
    def retrieve_last_buycap(self, owner):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT buy_mc FROM trades WHERE owner = ? ORDER BY ROWID DESC LIMIT 1''', (owner,))
            last_buy_mc = cursor.fetchone()
            if last_buy_mc:
                return last_buy_mc[0]
            else:
                return None
        except Exception as e:
            return e
        
    
    def retrieve_token_bal(self, owner):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT token_balance FROM trades WHERE owner = ? ORDER BY ROWID DESC LIMIT 1''', (owner,))
            last_tok_bal = cursor.fetchone()
            if last_tok_bal:
                return last_tok_bal[0]
            else:
                return None
        except Exception as e:
            return e
        
        
    def retrieve_buyamt(self, owner):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT buy_amount FROM trades WHERE owner = ? ORDER BY ROWID DESC LIMIT 1''', (owner,))
            last_tok_bal = cursor.fetchone()
            if last_tok_bal:
                return last_tok_bal[0]
            else:
                return None
        except Exception as e:
            return e

    def update_trade(self, owner, contract_address, buy_mc=None, sell_mc=None, pnl=None, buy_amount=None, token_balance=None):
        try:
            statement = "UPDATE trades SET buy_mc=?, sell_mc=?, pnl=?, buy_amount=?, token_balance=? WHERE owner=? AND contract_address=?"
            args = (buy_mc, sell_mc, pnl, buy_amount, token_balance, owner, contract_address)
            self.conn.execute(statement, args)
            self.conn.commit()
            return "Trade updated successfully"
        except Exception as e:
            return e

    
    def get_all_trades(self, owner):
        statement = "SELECT owner, buy_mc, sell_mc, contract_address, pnl, buy_amount, token_balance FROM trades WHERE owner = (?)"
        args = (owner, )
        return [x for x in self.conn.execute(statement, args)]
    
    
    
    def delete_last_ca(self, owner):
        try:
            # Create a cursor object from the connection
            cursor = self.conn.cursor()
            
            # Execute SQL query to retrieve the last contract address for the given owner
            cursor.execute('''SELECT contract_address FROM trades WHERE owner = ? ORDER BY ROWID DESC LIMIT 1''', (owner,))
            
            # Fetch the result of the query
            last_ca = cursor.fetchone()
            
            if last_ca:
                # Extract the contract address from the fetched result
                last_ca = last_ca[0]

                # Delete the last entry with the retrieved contract address
                cursor.execute('''DELETE FROM trades WHERE contract_address = ?''', (last_ca,))
                self.conn.commit()  # Commit the changes to the database
                print("Last entry deleted successfully.")
            else:
                print("No entries found for the specified owner.")
        except Exception as e:
            print("An error occurred:", e)
    
    
    def delete_all_trades(self, owner):
        try:
            statement = "DELETE FROM trades WHERE owner = ? " 
            args = (owner, )
            self.conn.execute(statement, args)
            self.conn.commit()
            
        except Exception as e:
            print(e)
            
            
            
class UserData:
    
    def __init__(self, dbname = "userdata.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)


    def setup(self):
        statement1 = """CREATE TABLE IF NOT EXISTS userdata (id INTEGER PRIMARY KEY, chatid INTEGER UNIQUE,
                            wallet TEXT UNIQUE, referrer INTEGER , referrals INTEGER DEFAULT 0,
                            referrals_vol FLOAT DEFAULT 0.0, trading_vol FLOAT DEFAULT 0.0 )"""
                            
        self.conn.execute(statement1)
        self.conn.commit()


    def add_user(self, username_, wallet, referrer):
        statement = "INSERT OR IGNORE INTO userdata (chatid, wallet, referrer) VALUES (?, ?, ?)"
        args = (username_, wallet,referrer)
        self.conn.execute(statement, args)
        self.conn.commit()
        
        
    def update_referrals(self, amount, userid):
        statement = "UPDATE userdata SET referrals = ? WHERE chatid = ?"
        args = (amount, userid)
        self.conn.execute(statement, args)
        self.conn.commit()
        
        
        
    def get_referrals(self, owner):
        statement = "SELECT referrals FROM userdata WHERE chatid = ?"
        args = (owner,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    
    
    
    def update_referrals_vol(self, amount, userid):
        statement = "UPDATE userdata SET referrals_vol = ? WHERE chatid = ?"
        args = (amount, userid)
        self.conn.execute(statement, args)
        self.conn.commit()
        
        
        
    def get_referrals_vol(self, owner):
        statement = "SELECT referrals_vol FROM userdata WHERE chatid = ?"
        args = (owner,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    
    
    def update_trading_vol(self, amount, userid):
        statement = "UPDATE userdata SET trading_vol = ? WHERE chatid = ?"
        args = (amount, userid)
        self.conn.execute(statement, args)
        self.conn.commit()
        
        
        
    def get_trading_vol(self, owner):
        statement = "SELECT trading_vol FROM userdata WHERE chatid = ?"
        args = (owner,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    
    
    def get_referrer(self, owner):
        statement = "SELECT referrer FROM userdata WHERE chatid = ?"
        args = (owner,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    
    
    def get_users(self):
        statement = "SELECT chatid, wallet, referrer, referrals, referrals_vol, trading_vol FROM userdata"
        return [x for x in self.conn.execute(statement)]
    
    
    
class Bridge:
    
    def __init__(self, dbname="bridge.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def setup(self):
        statement1 = """CREATE TABLE IF NOT EXISTS bridge (
                            id INTEGER PRIMARY KEY,
                            chatid INTEGER UNIQUE,
                            txid TEXT DEFAULT 'YES',
                            amount FLOAT DEFAULT 0.0
                        )"""
        self.conn.execute(statement1)
        self.conn.commit()

    def add_user(self, chatid):
        statement = "INSERT OR IGNORE INTO bridge (chatid) VALUES (?)"
        args = (chatid,)
        self.conn.execute(statement, args)
        self.conn.commit()

    def update_txid(self, txid, userid):
        statement = "UPDATE bridge SET txid = ? WHERE chatid = ?"
        args = (txid, userid)
        self.conn.execute(statement, args)
        self.conn.commit()

    def get_txid(self, userid):
        statement = "SELECT txid FROM bridge WHERE chatid = ?"
        args = (userid,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

    def update_amount(self, amount, userid):
        statement = "UPDATE bridge SET amount = ? WHERE chatid = ?"
        args = (amount, userid)
        self.conn.execute(statement, args)
        self.conn.commit()

    def get_amount(self, userid):
        statement = "SELECT amount FROM bridge WHERE chatid = ?"
        args = (userid,)
        cursor = self.conn.execute(statement, args)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

    def del_user(self, userid):
        statement = "DELETE FROM bridge WHERE chatid = ?"
        args = (userid,)
        self.conn.execute(statement, args)
        self.conn.commit()
    
    
    
class Airdrop:
    def __init__(self, db_name="airdrop.db"):
        self.connection = sqlite3.connect(db_name, check_same_thread= False)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                address TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def add_user(self, user_id, address):
        """Add a new user with their address."""
        self.cursor.execute("INSERT INTO users (user_id, address) VALUES (?, ?)", (user_id, address))
        self.connection.commit()

    def get_address(self, user_id):
        """Get the address of a user by their ID."""
        self.cursor.execute("SELECT address FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else "User ID not found."

    def delete_user(self, user_id):
        """Delete a user by their ID."""
        self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.connection.commit()
        return f"User {user_id} deleted." if self.cursor.rowcount > 0 else "User ID not found."

    def __del__(self):
        """Close the database connection when the instance is destroyed."""
        self.connection.close()