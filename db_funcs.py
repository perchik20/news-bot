import sqlite3

def add_ticker(ticker, main_url):
    conn = sqlite3.connect("new-bot.db")
    cursor = conn.cursor()

    # Добавление записи
    cursor.execute("""
        INSERT INTO tickers (ticker, main_url) 
        VALUES (?, ?)
    """, (f"{ticker}", f'"{main_url}"'))

    conn.commit()
    conn.close()
    
def get_ticker():
    conn = sqlite3.connect("new-bot.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tickers")
    rows = cursor.fetchall()

    for row in rows:
        print(row)
        
    conn.close()
    return rows


def del_ticker(ticker):
    print(ticker)
    conn = sqlite3.connect("new-bot.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tickers WHERE ticker = ?", (ticker,))
    conn.commit()
    conn.close()
