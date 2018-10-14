#!/home/jonathansoll/Documents/Projects/quantstrat_backtester/venv_quanstrat_backtester/bin/python3

import pyodbc
import pandas as pd

server = 'firstserverjs.database.windows.net'
database = 'securities_master'
username = 'JSoll'
password = 'Emjosa139'
driver= '{ODBC Driver 17 for SQL Server}'
conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

symbol_data = {}
symbol_list = ['AAPL', 'MSFT']

query_str = """
    SELECT
        [Date] = dp.date
        , [Adj_Close] = dp.closeAdj
    FROM SimFin.daily_price dp (nolock)
    JOIN SimFin.general_company_data gcd (nolock) ON dp.simId = gcd.simId
    WHERE
        ticker = '%s'
"""

comb_index = None
for s in symbol_list: # for each and every symbol we care about
    symbol_data[s] = pd.read_sql(sql=query_str % s, con=conn, index_col='Date')

    # combine the index to pad forward values
    if comb_index is None: # if it's the first symbol, set the index to the dates of the first symbol
        comb_index = symbol_data[s].index
    else: # if it's not the first symbol, combine the dates of all of the symbols
        comb_index = comb_index.union(symbol_data[s].index)
    print(symbol_data[s].tail())
    print(len(symbol_data[s]))
    print('comb_index length = ', len(comb_index))
    print('')

    # Reindex the dataframes
for s in symbol_list:
    symbol_data[s] = symbol_data[s].reindex(index=comb_index)#.iterrows()

for s in symbol_list:
    print(symbol_data[s].tail())
    print(len(symbol_data[s]))
    print('comb_index length = ', len(comb_index))
    print('')

conn.close()
