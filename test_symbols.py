# test_symbols.py
import yfinance as yf

# Test stocks
print("=" * 50)
print("TESTING STOCK SYMBOLS")
print("=" * 50)

stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']
for symbol in stocks:
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            print(f"✅ {symbol}: Works! Latest price: ${data['Close'].iloc[-1]:.2f}")
        else:
            print(f"❌ {symbol}: No data returned")
    except Exception as e:
        print(f"❌ {symbol}: Error - {str(e)[:50]}")

print("\n" + "=" * 50)
print("TESTING CRYPTO SYMBOLS")
print("=" * 50)

cryptos = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'ADA-USD', 
           'XRP-USD', 'BNB-USD', 'USDC-USD', 'USDT-USD']
for symbol in cryptos:
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            print(f"✅ {symbol}: Works! Latest price: ${data['Close'].iloc[-1]:.2f}")
        else:
            print(f"❌ {symbol}: No data returned")
    except Exception as e:
        print(f"❌ {symbol}: Error - {str(e)[:50]}")