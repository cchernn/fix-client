# FIX Client Simulation  
Simulation for FIX Client Initiator.  
The following are the objectives of this simulation: 
- Send 1,000 randomized BUY, SELL, SHORT orders for "MSFT", "BAC" and "AAPL" within 5 minutes.  
- Within the same timeframe, initiate random cancel order requests.  
- Calculate the following metrics:  
    - Total Trading Volume (USD).  
    - Profit and Loss (PNL) from the session.  
    - Volume Weighted Average Price (VWAP) for fills of each instrument.  

Summary of the simulation:  
- `client.main` will initiate `SocketInitiator`  
- execute `application.fix_pricing.run`. Simulation steps are detailed accordingly under the `run` function for object `fix_pricing`.  
- save Market Data under `Results.market_data_<timestamp>.csv` and close initiator.  
- process statistics and produce summary file under `Results.summary_<timestamp>.csv`.  

## Installation  
Requirements:  
- Python 3.8 or above. Default = Python 3.8.16 
- [pipenv](https://pypi.org/project/pipenv/) or any other virtualenv control.  

Initiate virtualenv by venv or pipenv.  
``` python  
# venv  
cd your_project_directory  
python -m venv venv  
source venv/bin/activate  

# pipenv  
pipenv shell  
```  

Install necessary packages.  
``` python  
# venv  
pip install -r requirements.txt

# pipenv  
pipenv install -r requirements.txt
```  

Create a `config.cfg` file from config-sample.cfg and fill in the following details:  
```
SocketConnectHost=
SocketConnectPort=
SenderCompID=
TargetCompID=
```  

## Usage  
Edit following configurations in `config.cfg` as needed.  
Run the simulation using the following command:  
``` python  
python client.py
```

FIX message logs will be compiled in `<timestamp>.log` under `Log` folder, and raw data to be compiled in CSV format `market_data_<timestamp>.csv` under `Results` folder.  

Once completed, a summary file `summary_<timestamp>.log` should be generated under `Results` folder after each execution.  

## Example  
Sample outputs can be found under `sample` folder.  
Below is a sample output under `summary_<timestamp>.log`.  

```  
Generating Report for Session <SessionID> - 20231022110744
Total Order Counts:
     NewOrder - AAPL_BUY  : 119
     NewOrder - AAPL_SELL : 102
     NewOrder - AAPL_SHORT: 105
     NewOrder - BAC _BUY  : 141
     NewOrder - BAC _SELL : 110
     NewOrder - BAC _SHORT: 100
     NewOrder - MSFT_BUY  : 137
     NewOrder - MSFT_SELL : 100
     NewOrder - MSFT_SHORT: 86
     Total NewOrder    : 1,000
     Total CancelOrder : 53
Total Trading Volume:
     AAPL : $222,904,884.01
     BAC  : $54,792,688.15
     MSFT : $367,738,501.28
     Total: $645,436,073.44
Profit and Loss (PNL) (diff(Buy/Sell_LastPx - MktPx)):
     AAPL : $567,271.97
     BAC  : $123,640.21
     MSFT : $125,822.18
     Total: $816,734.36
Volume Weighted Average Price (VWAP):
     AAPL : $151.46
     BAC  : $32.53
     MSFT : $239.93
```  

## Sources    
[FIX Protocol Documentation](https://www.onixs.biz/fix-dictionary/4.2/fields_by_tag.html) by ONIXS  
[FIX GitHub sample](https://github.com/darwinex/dwx-fix-connector/tree/master) by darwinex  
[Python Quickfix GitHub Library](https://github.com/quickfix/quickfix/tree/master)  
[Quickfix Engine Documentation](https://quickfixengine.org/c/documentation/)  