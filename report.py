import datetime
import pandas as pd
import numpy as np
from helpers import setup_logger, log

def processData(filepath, sessionid, start_timestamp=datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')):
    """
    Generate summary statistics of latest simulation run
    """

    ordType_map = {
        1: "BUY",
        2: "SELL",
        3: "SHORT",
    }

    ### Setting up logger
    logger = setup_logger(
        name="summary",
        log_file=f"Results/summary_{start_timestamp}.log",
        format_str='%(message)s'
    )
    log(logger, f"Generating Report for Session {sessionid} - {start_timestamp}")

    df = pd.read_csv(filepath)
    if df.empty:
        log(logger, f"No Data Found for Session {sessionid} - {start_timestamp}", level="ERROR")
        return
    
    ### Calculating Order Counts
    df_orders = df[(df['type']=='send')]
    df_order_counts = df_orders.groupby(['58', '55', '54']).agg({'11': 'count'})
    log(logger, f"Total Order Counts:")
    total_orders = 0
    total_cancels = 0
    for key, value in df_order_counts.to_dict()['11'].items():
        if key[0] == "NewOrderSingle":
            log(logger, f"{' ':5}NewOrder - {key[1]:4}_{ordType_map[key[2]]:5}: {round(value,0):,}")
            total_orders+=value
        elif key[0] == "OrderCancelRequest":
            total_cancels+=value
    log(logger, f"{' ':5}{'Total NewOrder':18}: {round(total_orders,0):,}")
    log(logger, f"{' ':5}{'Total CancelOrder':18}: {round(total_cancels,0):,}")


    df_traded = df[(df['type']=='receive') & (df['39']!=8)]
    df_traded = df_traded.fillna(0)
    df_traded['value'] = df['31'] * df['32']

    ### (1) Calculating Trading Volume
    trading_volume = df_traded.groupby('55').agg({'value': sum})
    trading_volume_sum = trading_volume.sum()['value']
    log(logger, f"Total Trading Volume:")
    for key, value in trading_volume.to_dict()['value'].items():
        log(logger, f"{' ':5}{key:5}: ${round(value,2):,}")
    log(logger, f"{' ':5}Total: ${round(trading_volume_sum,2):,}")
    
    ### (2) Calculating Profit and Loss (PNL)
        ### Approach1: Sell + Sell Short - Buy
    # def calc_pnl1(group):
    #     values = group.groupby('54')['value'].sum()
    #     return values[2.0] + values[3.0] - values[1.0]
    # pnl = df_traded.groupby('55').apply(calc_pnl1)
    # pnl_sum = pnl.sum()
    # log(logger, f"Profit and Loss (PNL) (Sell + Sell Short - Buy):")
    # for key, value in pnl.to_dict().items():
    #     log(logger, f"{' ':5}{key:5}: ${round(value, 2):,}")
    # log(logger, f"{' ':5}Total: ${round(pnl_sum,2):,}")

        ### Approach2: diff(Buy/Sell_LastPx - MktPx)
        ### Take price difference between execution price and market price (market price currently hardcoded, possibly to be taken from MarketDataRequest)
    mktpx = {
        'MSFT': 240,
        'AAPL': 150,
        'BAC': 32
    }
    pnl2 = df_traded.copy()
    pnl2['mktpx'] = df_traded['55'].map(mktpx)
    pnl2['pnlpx'] = np.where(pnl2['54']==1, pnl2['mktpx'] - pnl2['31'],
                                 np.where(pnl2['54'].isin([2,3]), pnl2['31'] - pnl2['mktpx'], None))
    pnl2['value2'] = pnl2['pnlpx'] * pnl2['32']
    pnl2 = pnl2.groupby('55').agg({'value2': sum})
    pnl_sum2 = pnl2.sum()['value2']
    log(logger, f"Profit and Loss (PNL) (diff(Buy/Sell_LastPx - MktPx)):")
    for key, value in pnl2.to_dict()['value2'].items():
        log(logger, f"{' ':5}{key:5}: ${round(value,2):,}")
    log(logger, f"{' ':5}Total: ${round(pnl_sum2,2):,}")

    ### (3) Calculating Volume Weighted Average Price (VWAP)
    vwap = df_traded.groupby('55').agg({'value': sum, '32': sum})
    vwap['vwap'] = vwap['value'] / vwap['32']
    vwap['vwap'] = vwap['vwap'].fillna(0)
    log(logger, f"Volume Weighted Average Price (VWAP):")
    for key, value in vwap.to_dict()['vwap'].items():
        log(logger, f"{' ':5}{key:5}: ${round(value, 2):,}")

    