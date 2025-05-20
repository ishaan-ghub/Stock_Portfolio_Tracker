import requests
from dotenv import load_dotenv
import os

load_dotenv()

class StockPortfolio:
    def __init__(self, api_key):
        self.portfolio = {}
        self.api_key = api_key

    def add_stock(self, symbol, quantity):
        if symbol in self.portfolio:
            self.portfolio[symbol]['quantity'] += quantity
        else:
            self.portfolio[symbol] = {'quantity': quantity}
        print(f"{symbol.strip()} addded successfully to your portfolio!")
        print("_______________________________________")

    def remove_stock(self, symbol, quantity):
        if symbol not in self.portfolio:
           print("Error: Stock not found in portfolio.")
        else:
            if self.portfolio[symbol]['quantity'] < quantity:
                print("Error: Not enough stocks to sell.")
                print("_______________________________________")
            else:
                self.portfolio[symbol]['quantity'] -= quantity
                print(f"{quantity.strip()} stocks of {symbol.strip()} sold successfully!")
                print("_______________________________________")


    def get_stock_data(self, symbol):
        base_url = 'https://www.alphavantage.co/query'
        function = 'GLOBAL_QUOTE'
        params = {'function': function, 'symbol': symbol, 'apikey': self.api_key}

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            quote = data.get("Global Quote",{})
            
            price = quote["05. price"]
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
        except:
            return None

    def update_portfolio(self):
        for symbol in self.portfolio:
            data = self.get_stock_data(symbol)
            if data:
                try:
                    current_price = float(data['Global Quote']['05. price'])
                    current_value = current_price * self.portfolio[symbol]['quantity']
                    self.portfolio[symbol]['current_price'] = current_price
                    self.portfolio[symbol]['current_value'] = current_value
                except KeyError:
                    print(f"Unable to get price for {symbol}")
                    print("_______________________________________")

    def display_portfolio(self):
        print("Your Portfolio:\n")
        for symbol, details in self.portfolio.items():
            print(f"Symbol: {symbol}")
            print(f"Quantity: {details['quantity']}")
            if 'current_price' in details:
                print(f"Current Price: {details['current_price']:.2f}")
                print(f"Total Value: {details['current_value']:.2f}")
                print("-----------")
        print("_______________________________________")

if __name__ == "__main__":
    api_key = os.getenv("API_KEY")
    portfolio = StockPortfolio(api_key)

    while True:
        print("1. Add Stock\n2. Sell Stock\n3. Display Portfolio\n4. End")
        choice = input("Enter your choice (1/2/3/4): ")

        if choice not in '1234':
            print("Invalid choice. Please enter a valid option.")
            print("_______________________________________")
            break

        elif choice == '1':
            symbol = input("Enter stock symbol: ").upper()
            validate = portfolio.get_stock_data(symbol)
            if validate:
                quantity = int(input("Enter quantity: "))
                portfolio.add_stock(symbol, quantity)
            else:
                print("Stock symbol not valid")
                print("_______________________________________")

        elif choice == '2':
            if not portfolio.portfolio:
                print("Add a stock first to the portfolio")
                print("_______________________________________")
            else:
                symbol = input("Enter stock symbol to sell: ").upper()
                quantity = int(input("Enter quantity to sell: "))
                portfolio.remove_stock(symbol, quantity)

        elif choice == '3':
            if not portfolio.portfolio:
                print("Your portfolio is empty!")
                print("_______________________________________")
            else:
                portfolio.update_portfolio()
                portfolio.display_portfolio()

        elif choice == '4':
            print("Program ended!")
            print("_______________________________________")
            break