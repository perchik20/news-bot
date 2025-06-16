import sqlite3
import io

def add_new_user(nickname, chat_id):
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

        if nickname == None:
            nickname = f'user{len(rows)+1}'

        cursor.execute("""
            INSERT INTO users (nickname, chat_id) 
            VALUES (?, ?)
        """, (f'{nickname}', f'{chat_id}'))

        conn.commit()
        conn.close()
    
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    

def add_ticker(ticker, main_url):
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()

        # Добавление записи
        cursor.execute("""
            INSERT INTO tickers (ticker, main_url) 
            VALUES (?, ?)
        """, (f"{ticker}", f'"{main_url}"'))

        conn.commit()
        conn.close()
    
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    
    finally:
        if conn:
            conn.close()
    
def get_ticker():
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tickers")
        rows = cursor.fetchall()
            
        conn.close()
        return rows

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    
    finally:
        if conn:
            conn.close()


def del_ticker(ticker):
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tickers WHERE ticker = ?", (ticker,))
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    
    finally:
        if conn:
            conn.close()

def add_all_in_company_custom(chat_id):
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM tickers')
        rows = cursor.fetchall()
        
        for _, ticker, _ in rows:
            cursor.execute("""
            INSERT OR IGNORE INTO custom_companies_list (chat_id, ticker) 
            VALUES (?, ?)
        """, (chat_id, ticker))

        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    
    finally:
        if conn:
            conn.close()

def add_company_custom(chat_id, ticker):
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()

        # Добавление записи
        cursor.execute("""
        INSERT OR IGNORE INTO custom_companies_list (chat_id, ticker) 
        VALUES (?, ?)
    """, (chat_id, ticker))

        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    
    finally:
        if conn:
            conn.close()
        
def get_company_custom(chat_id):
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM custom_companies_list WHERE chat_id = ?", (f"{chat_id}",))
        rows = cursor.fetchall()

        conn.close()
        return rows

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    
    finally:
        if conn:
            conn.close()

def del_company_custom(chat_id, ticker):
    try:
        conn = sqlite3.connect("new-bot.db")
        cursor = conn.cursor()
        print(chat_id, ticker)
        cursor.execute(f"DELETE FROM custom_companies_list WHERE chat_id = ? AND ticker = ?", (f'{chat_id}', f'{ticker}'))

        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []
    
    finally:
        if conn:
            conn.close()
        
def get_users_by_chatid(ticker):
    try:
        with sqlite3.connect("new-bot.db") as conn:
            cursor = conn.cursor()
            query = """
            SELECT u.chat_id
            FROM custom_companies_list ccl
            JOIN users u ON ccl.chat_id = u.chat_id
            WHERE ccl.ticker = ?
            """
            cursor.execute(query, (ticker,))
            results = cursor.fetchall()
            return [row[0] for row in results]
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []

