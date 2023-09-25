from bs4 import BeautifulSoup
import requests
from flask import Flask, render_template

'''
Web scraping application that will loop through stocks from Investing.com then display their information
It will identify if we're in a bull, bear or neutral market
It will recommend whether to buy or sell stocks
It will display the top five stocks to buy

'''

app = Flask(__name__)

html_text = requests.get('https://uk.investing.com/equities/').text
soup = BeautifulSoup(html_text, 'lxml')

ftse = requests.get('https://uk.investing.com/indices/uk-100-technical').text
ftse_soup = BeautifulSoup(ftse, 'lxml')

ftse_highs_and_lows = ftse_soup.find(lambda tag: tag.name == "span" and 'Highs/Lows(14)' in tag.text).parent.parent
ftse_buy = ftse_highs_and_lows.find(lambda tag: tag.name == "td" and ('Buy' in tag.text or 'Neutral' in tag.text or 'Sell' in tag.text)).text
if ftse_buy == 'Buy':
    print("We're in a bull market")
elif ftse_buy == 'Sell':
    print("We're in a bear market")
else:
    print("We're in a neutral market")
    
stocks = soup.find_all('td', class_ = 'bold left noWrap elp plusIconTd')

# Create an empty list to store stock information
stock_data = []

# Create a list of stocks to buy
stocks_to_buy = []

for stock in stocks:
    full_stock_information = requests.get('https://uk.investing.com' + stock.a['href']).text
    stock_soup = BeautifulSoup(full_stock_information, 'lxml')

    technical_information = requests.get('https://uk.investing.com' + stock.a['href'] + '-technical').text
    technical_soup = BeautifulSoup(technical_information, 'lxml')

    average_volume = stock_soup.select_one('dd[data-test="avgVolume"]')
    current_volume = stock_soup.select_one('dd[data-test="volume"]')
    relative_strength = technical_soup.find(lambda tag: tag.name == "span" and 'RSI(14)' in tag.text)
    highs_and_lows = technical_soup.find(lambda tag: tag.name == "span" and 'Highs/Lows(14)' in tag.text)
    moving_average = technical_soup.find(lambda tag: tag.name == "span" and 'MA20' in tag.text)

    # Check if the elements were found before extracting data
    if average_volume and current_volume and relative_strength and highs_and_lows and moving_average:
        average_volume = float(average_volume.text.replace(',', ''))
        current_volume = float(current_volume.text.replace(',', ''))
        volume_ratio = current_volume / average_volume

        relative_strength_buy = relative_strength.find(lambda tag: tag.name == "td" and 'Buy' in tag.text)
        highs_and_lows_buy = highs_and_lows.parent.parent.find(lambda tag: tag.name == "td" and 'Buy' in tag.text)
        moving_average_buy = moving_average.parent.parent.find_all(lambda tag: tag.name == "td" and 'Buy' in tag.text)

        stock_name = stock_soup.find('h1').text

        if average_volume * 2 < current_volume and relative_strength_buy and len(moving_average_buy) == 4 and highs_and_lows_buy:
            buy_status = "Buy!"
        else:
            buy_status = "Don't Buy!"

        # Store the stock information in a dictionary
        stock_info = {
            'Stock Name': stock_name,
            'Average Volume': average_volume,
            'Current Volume': current_volume,
            'Volume Ratio': volume_ratio,
            'Buy Status': buy_status
        }

        stock_data.append(stock_info)
        print(stock_info)

for stock in stock_data:
    if stock['Buy Status'] == "Buy!":
        stocks_to_buy.append(stock)

# Sort stock_data by volume_ratio and get the top 5 stocks
top_five_stocks = sorted(stocks_to_buy, key=lambda x: x['Volume Ratio'], reverse=True)[:5]

# Print the top five stocks
for stock in top_five_stocks:
    if buy_status == "Buy!":
        print(f"Stock Name: {stock['Stock Name']}")
        print(f"Average Volume: {stock['Average Volume']}")
        print(f"Current Volume: {stock['Current Volume']}")
        print(f"Volume Ratio: {stock['Volume Ratio']}")
        print(f"Buy Status: {stock['Buy Status']}")
        print()

@app.route('/')
def home():
    # Pass relevant data to the HTML template
    return render_template('index.html', ftse_buy=ftse_buy, stock_data=stock_data, top_five_stocks=top_five_stocks)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
