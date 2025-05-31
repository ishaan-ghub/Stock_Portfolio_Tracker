import requests
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

table='portfolio'
db="Portfolio.db"

def Create_table():
    conn = sqlite3.connect(db)
    cursor=conn.cursor()
    cursor.execute(f''' CREATE TABLE IF NOT EXISTS {table} (Symbol TEXT PRIMARY KEY, Quantity INTEGER, Current_price REAL, Current_value REAL) ''')

    conn.commit()
    conn.close()

def Fetch_table():
    conn=sqlite3.connect(db)
    cursor=conn.cursor()
    cursor.execute(f'''SELECT * FROM {table}''')
    query=cursor.fetchall()
    return query

class StockPortfolio:
    def __init__(self, api_key):
        self.portfolio = {}
        self.api_key = api_key
        self.Sync_with_db()

    def Sync_with_db(self):
        self.portfolio={}

        for row in Fetch_table():
            symbol,quantity,current_price,net_price=row
            self.portfolio[symbol]={
                'quantity':quantity,
                'current_price':current_price,
                'current_value': net_price
            }

    def add_stock(self, symbol, quantity):        
        if symbol in self.portfolio:
            self.portfolio[symbol]['quantity'] += quantity
            print(f"{quantity} more stocks of {symbol} added successfully!")
        else:
            self.portfolio[symbol] = {'quantity': quantity}

            print(f"{symbol.strip()} added successfully to your portfolio!")
        self.update_portfolio()
        self.Add_Table()

        print("_______________________________________")

    def remove_stock(self, symbol, quantity):
        if symbol not in self.portfolio:
            print("Stock not found in portfolio!")
            print("_______________________________________")
            return
        if self.portfolio[symbol]['quantity'] < quantity:
            print("Error: Not enough stocks to sell.")
            print("_______________________________________")
        else:
            self.portfolio[symbol]['quantity'] -= quantity
            print(f"{quantity} stocks of {symbol.strip()} sold successfully!")

            if self.portfolio[symbol]['quantity']==0:
                del self.portfolio[symbol]

            self.update_portfolio()
            self.Add_Table()
            print("_______________________________________")

    def get_stock_data(self, symbol):
        base_url = 'https://www.alphavantage.co/query'
        function = 'GLOBAL_QUOTE'
        params = {'function': function, 'symbol': symbol, 'apikey': self.api_key}

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            quote = data.get("Global Quote",{})            
            price = quote.get("05. price")

            if price and float(price) > 0:
                return data
            elif 'Note' in data:
                print(f"API Limit Exceeded. Please try again later.")
                print("_______________________________________")
                return None
            else:
                print(f"Error: Unable to get data for {symbol}.")
                print("_______________________________________")
                return None
        except Exception as e:
            print(f"error occured: {e}")
            return None

    def update_portfolio(self):
        for symbol in self.portfolio:
            data = self.get_stock_data(symbol)
            if data:
                try:
                    current_price = float(data['Global Quote']['05. price'])
                    current_value = round(current_price * self.portfolio[symbol]['quantity'],2)
                    self.portfolio[symbol]['current_price'] = current_price
                    self.portfolio[symbol]['current_value'] = current_value

                except KeyError:
                    print(f"Unable to get price for {symbol}")
                    print("_______________________________________")
    
    def Add_Table(self):
        conn=sqlite3.connect(db)
        cursor=conn.cursor()

        for symbol,data in self.portfolio.items():
            cursor.execute(f'''INSERT OR REPLACE INTO {table}(Symbol, Quantity, Current_price, Current_value) VALUES(?, ?, ?, ?)''',(symbol,data['quantity'],data['current_price'],data['current_value']))

        conn.commit()
        conn.close()

    def display_portfolio(self):
        print("Your Portfolio:\n")
        if not Fetch_table():
            print("Your portfolio is empty!")
        else:
            for row in Fetch_table():
                symbol, quantity, current_price, current_value = row
                print(f"Symbol: {symbol}")
                print(f"Quantity: {quantity}")
                print(f"Current Price: {current_price:.2f}")
                print(f"Current Value: {current_value:.2f}")
                print("-----------")
        print("_______________________________________")

if __name__ == "__main__":
    Create_table()
    api_key = os.getenv("API_KEY")
    portfolio = StockPortfolio(api_key)

    while True:
        print("1. Add Stock\n2. Sell Stock\n3. Display Portfolio\n4. End")
        try:
            choice = int(input("Enter your choice (1/2/3/4): "))
        except ValueError:
            print("Invalid input! Please enter a number.")
            continue

        if choice not in (1,2,3,4):
            print("Invalid choice. Please enter a valid option.")
            print("_______________________________________")
            break

        elif choice ==1:
            symbol = input("Enter stock symbol: ").upper()
            validate = portfolio.get_stock_data(symbol)
            if validate:
                quantity = int(input("Enter quantity: "))
                portfolio.add_stock(symbol, quantity)
            else:
                print("Stock symbol not valid")
                print("_______________________________________")

        elif choice == 2:
            if not Fetch_table():
                print("Add a stock first to the portfolio")
                print("_______________________________________")
            else:
                symbol = input("Enter stock symbol to sell: ").upper()
                quantity = int(input("Enter quantity to sell: "))
                portfolio.remove_stock(symbol, quantity)

        elif choice == 3:
            if not Fetch_table():
                print("Your portfolio is empty!")
                print("_______________________________________")
            else:
                portfolio.display_portfolio()

        elif choice == 4:
            print("Program ended!")
            print("_______________________________________")
            break