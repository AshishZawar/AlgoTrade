import math
import time
from datetime import datetime, timedelta
import pandas as pd
from kiteext import KiteExt

def Zerodha_login():
    global kite
    isConnected = 0
    try:
        kite = KiteExt()

        UserID = "PS6051"
        enctoken = "PvelVR09bRqgwD/sPbVkUB8n8ihHMrC7IIt3Yz7clwuuScE/wtrh3x8bux4wlON6Lau2IwdfOz5+MQQrwNtiYagOwGorIdhiIY7i0Y8ppiBUMHsY2RbYdQ=="

        kite.login_using_enctoken(userid=UserID, enctoken=enctoken, public_token=enctoken)
        Profile = kite.profile()
        print(Profile)
        client_name = Profile.get('user_name')

        isConnected = 1

    except Exception as e:
        print(f"Error : {e}")
        print('Wrong credential')

    return isConnected

# Set the required parameters for the strategy
instrument_token = 260105
ema9_period = 9
ema21_period = 21
profit_target_percentage = 0.2
stop_loss_percentage = 0.1
underlying_symbol = 'BANKNIFTY23518'  # Replace with your desired underlying stock symbol
ce_option_type = 'CE'
pe_option_type = 'PE'


current_time = datetime.now()
end_of_candle = current_time + timedelta(minutes=3) - timedelta(seconds=current_time.second % 3, microseconds=current_time.microsecond)


# Define the strategy function
def run_strategy():
    monitor_trades()

def check_crossover(df):
    # Calculate EMA9 and EMA21
    closes = [candle['close'] for candle in df]
    df['ema9'] = df[closes].ewm(span=ema9_period, adjust=False).mean()
    df['ema21'] = df[closes].ewm(span=ema21_period, adjust=False).mean()

    # Check for crossover
    if df['ema9'].iloc[-1] > df['ema21'].iloc[-1] and df['ema9'].iloc[-2] <= df['ema21'].iloc[-2]:
        return "Buy"
    elif df['ema9'].iloc[-1] < df['ema21'].iloc[-1] and df['ema9'].iloc[-2] >= df['ema21'].iloc[-2]:
        return "Sell"
    else:
        return "Ignore"

def place_order(symbol, transaction_type, quantity):
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_MCX,
            tradingsymbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_NRML
        )
        return order_id
    except Exception as e:
        print('Order placement failed:', str(e))
        return None

def round_ce_strike(price):
    return math.ceil(price / 100) * 100

def round_pe_strike(price):
    return math.floor(price / 100) * 100

def monitor_trades():
    while True:
        print("Checking for next candle: " + str(end_of_candle))

        # Get historical data
        historical_data = kite.historical_data(
            instrument_token,
            from_date=pd.Timestamp.now() - pd.Timedelta(minutes=1800),
            to_date=pd.Timestamp.now(),
            interval='3minute'
        )

        # Create a DataFrame with the historical data
        df = pd.DataFrame(historical_data)
        df = df.set_index('date')

        # Check for crossover
        if check_crossover(df) == "Buy":
            # Place a CE buy order
            print("Cross Over happened")

            # Get the latest price for rounding
            latest_price = df['close'].iloc[-1]
            print(latest_price)

            #ce_strike = round_ce_strike(latest_price)
            #print(ce_strike)

            #instrument_name = underlying_symbol+str(ce_strike)+ce_option_type
            #print(instrument_name)
            #print(kite.ltp(instrument_token)[instrument_name]['last_price'])

            #order_id = place_order(instrument_name, 'BUY', 25)
            order_id = place_order(instrument_token, 'BUY', 1)
            if order_id is not None:
                print('Buy order placed for ' + str(instrument_token) + ':', order_id)

                # Monitor the trade
                while True:
                    # Check for order status
                    order_info = kite.order_history(order_id)
                    if order_info['status'] == 'COMPLETE':

                        # Calculate profit and stop-loss levels
                        entry_price = order_info['average_price']
                        profit_target = entry_price + (entry_price * profit_target_percentage)
                        stop_loss = entry_price - (entry_price * stop_loss_percentage)

                        print('Entry Price:', entry_price)
                        print('Profit Target:', profit_target)
                        print('Stop Loss:', stop_loss)

                        # Monitor the price movement
                        while True:
                            # Get the latest price
                            ltp = kite.ltp(instrument_token)[instrument_token]['last_price']
                            print('Current Price:', ltp)

                            # Check exit conditions
                            if ltp >= profit_target or ltp < stop_loss:
                                # Place a sell order to exit the trade
                                order_id = place_order(instrument_token, 'SELL', 1)
                                if order_id is not None:
                                    print('Sell order placed:', order_id)
                                break

                            #time.sleep(1)  # Wait for 10 seconds before checking again

                    #time.sleep(1)  # Wait for 10 seconds before checking again

        #time.sleep(10)  # Wait for 180 seconds before checking again
        time.sleep((end_of_candle - datetime.now()).total_seconds())

        # Check for crossover
        if check_crossover(df) == "Sell":
            # Place a CE buy order
            print("Cross Down happened")

            # Get the latest price for rounding
            latest_price = df['close'].iloc[-1]
            print(latest_price)

            #ce_strike = round_ce_strike(latest_price)
            #print(ce_strike)

            #instrument_name = underlying_symbol+str(ce_strike)+ce_option_type
            #print(instrument_name)
            #print(kite.ltp(instrument_token)[instrument_name]['last_price'])

            #order_id = place_order(instrument_name, 'BUY', 25)
            order_id = place_order(instrument_token, 'SELL', 1)
            if order_id is not None:
                print('Sell order placed for ' + str(instrument_token) + ':', order_id)

                # Monitor the trade
                while True:
                    # Check for order status
                    order_info = kite.order_history(order_id)
                    if order_info['status'] == 'COMPLETE':

                        # Calculate profit and stop-loss levels
                        entry_price = order_info['average_price']
                        profit_target = entry_price - (entry_price * profit_target_percentage)
                        stop_loss = entry_price + (entry_price * stop_loss_percentage)

                        print('Entry Price:', entry_price)
                        print('Profit Target:', profit_target)
                        print('Stop Loss:', stop_loss)

                        # Monitor the price movement
                        while True:
                            # Get the latest price
                            ltp = kite.ltp(instrument_token)[instrument_token]['last_price']
                            print('Current Price:', ltp)

                            # Check exit conditions
                            if ltp <= profit_target or ltp > stop_loss:
                                # Place a sell order to exit the trade
                                order_id = place_order(instrument_token, 'BUY', 1)
                                if order_id is not None:
                                    print('Buy order placed:', order_id)
                                break

                            #time.sleep(1)  # Wait for 10 seconds before checking again

                    #time.sleep(1)  # Wait for 10 seconds before checking again

        #time.sleep(10)  # Wait for 180 seconds before checking again
        time.sleep((end_of_candle - datetime.now()).total_seconds())

Zerodha_login()
run_strategy()