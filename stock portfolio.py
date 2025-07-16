import tkinter as tk
from tkinter import messagebox, ttk
import requests
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

table = 'portfolio'
db = "Portfolio.db"

def Create_table():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f''' CREATE TABLE IF NOT EXISTS {table} (
        Symbol TEXT PRIMARY KEY,
        Quantity INTEGER,
        Current_price REAL,
        Current_value REAL) ''')
    conn.commit()
    conn.close()

def Fetch_table():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(f'''SELECT * FROM {table}''')
    query = cursor.fetchall()
    conn.close()
    return query

class StockPortfolio:
    def __init__(self, api_key):
        self.portfolio = {}
        self.api_key = api_key
        self.Sync_with_db()

    def Sync_with_db(self):
        self.portfolio = {}
        for row in Fetch_table():
            symbol, quantity, current_price, net_price = row
            self.portfolio[symbol] = {
                'quantity': quantity,
                'current_price': current_price,
                'current_value': net_price
            }

    def get_stock_data(self, symbol):
        base_url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            quote = data.get("Global Quote", {})
            price = quote.get("05. price")

            if price and float(price) > 0:
                return float(price)
            elif 'Note' in data:
                return "limit"
            else:
                return None
        except:
            return None

    def update_portfolio(self):
        for symbol in self.portfolio:
            price = self.get_stock_data(symbol)
            if isinstance(price, float):
                current_value = round(price * self.portfolio[symbol]['quantity'], 2)
                self.portfolio[symbol]['current_price'] = price
                self.portfolio[symbol]['current_value'] = current_value

    def Add_Table(self):
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        for symbol, data in self.portfolio.items():
            cursor.execute(f'''INSERT OR REPLACE INTO {table}
                (Symbol, Quantity, Current_price, Current_value)
                VALUES (?, ?, ?, ?)''',
                (symbol, data['quantity'], data['current_price'], data['current_value']))
        conn.commit()
        conn.close()

    def add_stock(self, symbol, quantity):
        symbol = symbol.upper()
        price = self.get_stock_data(symbol)
        if price == "limit":
            return "API limit"
        elif not price:
            return "invalid"
        
        if symbol in self.portfolio:
            self.portfolio[symbol]['quantity'] += quantity
        else:
            self.portfolio[symbol] = {'quantity': quantity}

        self.update_portfolio()
        self.Add_Table()
        return "added"

    def remove_stock(self, symbol, quantity):
        symbol = symbol.upper()
        if symbol not in self.portfolio:
            return "not found"
        elif self.portfolio[symbol]['quantity'] < quantity:
            return "not enough"
        else:
            self.portfolio[symbol]['quantity'] -= quantity
            if self.portfolio[symbol]['quantity'] == 0:
                del self.portfolio[symbol]
            self.update_portfolio()
            self.Add_Table()
            return "sold"

# GUI code
class PortfolioApp:
    def __init__(self, root, portfolio_obj):
        self.root = root
        self.portfolio = portfolio_obj
        self.root.title("Stock Portfolio")
        self.root.geometry("600x400")

        # Tabs
        tab_control = ttk.Notebook(root)
        self.add_tab = ttk.Frame(tab_control)
        self.sell_tab = ttk.Frame(tab_control)
        self.view_tab = ttk.Frame(tab_control)

        tab_control.add(self.add_tab, text="Add Stock")
        tab_control.add(self.sell_tab, text="Sell Stock")
        tab_control.add(self.view_tab, text="View Portfolio")
        tab_control.pack(expand=1, fill="both")

        self.create_add_tab()
        self.create_sell_tab()
        self.create_view_tab()

    def create_add_tab(self):
        tk.Label(self.add_tab, text="Symbol:").pack(pady=5)
        self.add_symbol = tk.Entry(self.add_tab)
        self.add_symbol.pack(pady=5)

        tk.Label(self.add_tab, text="Quantity:").pack(pady=5)
        self.add_quantity = tk.Entry(self.add_tab)
        self.add_quantity.pack(pady=5)

        tk.Button(self.add_tab, text="Add Stock", command=self.handle_add).pack(pady=10)

    def handle_add(self):
        symbol = self.add_symbol.get().strip().upper()
        try:
            quantity = int(self.add_quantity.get().strip())
        except:
            messagebox.showerror("Error", "Enter a valid quantity")
            return

        result = self.portfolio.add_stock(symbol, quantity)
        if result == "added":
            messagebox.showinfo("Sucesss!",f"Congratulations {quantity} stocks of {symbol} added successfully.")
        elif result == "invalid":
            messagebox.showerror("Invalid","Enter a valid symbol!")
        elif result == "API limit":
            messagebox.showwarning("API limit exceeded, try again later")
        self.refresh_table()

    def create_sell_tab(self):
        tk.Label(self.sell_tab, text="Symbol:").pack(pady=5)
        self.sell_symbol = tk.Entry(self.sell_tab)
        self.sell_symbol.pack(pady=5)

        tk.Label(self.sell_tab, text="Quantity:").pack(pady=5)
        self.sell_quantity = tk.Entry(self.sell_tab)
        self.sell_quantity.pack(pady=5)

        tk.Button(self.sell_tab, text="Sell Stock", command=self.handle_sell).pack(pady=10)

    def handle_sell(self):
        symbol = self.sell_symbol.get().strip().upper()
        try:
            quantity = int(self.sell_quantity.get().strip())
        except:
            messagebox.showerror("invalid quantity","Please enter a valid quantity")
            return

        result = self.portfolio.remove_stock(symbol, quantity)
        if result == "not found":
            messagebox.showerror("not found", f"{symbol} not found in portfolio")
        elif result == "not enough":
            messagebox.showerror("Insufficient stocks","You don't have enough stocks to sell")
        else:
            messagebox.showinfo("Success",f"Well done, {quantity} stocks of {symbol} sold successfully!")
        self.refresh_table()

    def create_view_tab(self):
        self.tree = ttk.Treeview(self.view_tab, columns=('Symbol', 'Quantity', 'Price', 'Value'), show='headings')
        for col in ('Symbol', 'Quantity', 'Price', 'Value'):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)
        self.refresh_table()

    def refresh_table(self):
        self.portfolio.Sync_with_db()
        self.portfolio.update_portfolio()
        self.portfolio.Add_Table()

        for i in self.tree.get_children():
            self.tree.delete(i)

        for row in Fetch_table():
            self.tree.insert('', 'end', values=row)

if __name__ == "__main__":
    Create_table()
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Missing API_KEY in .env file")
    else:
        portfolio = StockPortfolio(api_key)
        root = tk.Tk()
        app = PortfolioApp(root, portfolio)
        root.mainloop()