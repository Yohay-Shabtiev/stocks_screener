sma_periods = [21, 55, 89, 144, 200]
ema_periods = [5, 8]
all_time_highs = []

all_tickers = [
 'AAPL', 
 'ABBV', 'ABNB', 'ABT', 'ADBE', 'ADI', 'ADM', 'ADP', 'ADSK', 'AFL',
 'AFRM', 'AIG', 'ALGN', 'ALK', 'ALL', 'AMAT', 'AMD', 'AMGN', 'AMT', 'AMZN',
 'AON', 'APD', 'APP', 'ARKK', 'ARKW', 'ARM', 'ASML', 'AVGO', 'AXON', 'AXP',
 'AZN', 'BA', 'BABA', 'BAX', 'BDX', 'BG', 'BIIB', 'BK', 'BKNG', 'BKR',
 'BMY', 'BRK-B', 'BSX', 'BWA', 'BX', 'BXP', 'BYND', 'C', 'CAG', 'CAT', 'CB',
 'CBOE', 'CCI', 'CCL', 'CDNS', 'CEG', 'CELH', 'CHD', 'CHRW', 'CHTR', 'CI',
 'CINF', 'CL', 'CLX', 'CMCSA', 'CME', 'CMG', 'COF', 'COIN', 'COP', 'COST',
 'CPB', 'CPRT', 'CRL', 'CRM', 'CRWD', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CVNA',
 'CVS', 'CVX', 'D', 'DAL', 'DDOG', 'DE', 'DECK', 'DHR', 'DIS', 'DKNG',
 'DLTR', 'DOCU', 'DOW', 'DPZ', 'DUK', 'DXC', 'DXCM', 'EBAY', 'ECL', 'ED',
 'EFX', 'EL', 'EOG', 'ES', 'ETN', 'ETR', 'EVRG', 'EXC', 'EXPE', 'EXR', 'F',
 'FANG', 'FAST', 'FHN', 'FIS', 'FIVE', 'FTNT', 'FTV', 'GD', 'GE',
 'GEHC', 'GFS', 'GILD', 'GIS', 'GOOG', 'GOOGL', 'GPN', 'GRMN', 'GS',
 'HALO', 'HAS', 'HCA', 'HD', 'HDB', 'HIG', 'HII', 'HOG', 'HON',
 'HOOD', 'HPE', 'HPQ', 'HRB', 'HST', 'HUM', 'IBM', 'ICE', 'IDXX', 'IEX',
 'ILMN', 'INOD', 'INTC', 'INTU', 'IP', 'IPG', 'ISRG', 'JCI', 'JNJ', 'JPM',
 'KDP', 'KHC', 'KLAC', 'KMB', 'KMX', 'KO', 'LDOS', 'LHX', 'LII', 'LIN',
 'LLY', 'LMND', 'LMT', 'LNC', 'LRCX', 'LULU', 'LUMN', 'LUV', 'LVS', 'LYB',
 'M', 'MA', 'MAR', 'MC', 'MCD', 'MCHP', 'MCK', 'MCO', 'MDB', 'MDLZ',
 'MDT', 'MELI', 'MET', 'META', 'MKTX', 'MMM', 'MNDY', 'MNST', 'MO', 'MP',
 'MPWR', 'MRK', 'MRNA', 'MRVL', 'MS', 'MSCI', 'MSFT', 'MSI', 'MTCH', 'MU',
 'MUR', 'NEE', 'NEM', 'NET', 'NEU', 'NFLX', 'NIO', 'NKE', 'NOC', 'NOW',
 'NSC', 'NTAP', 'NTR', 'NVDA', 'NVR', 'NXPI', 'O', 'ODFL', 'OKTA', 'OMC',
 'ON', 'ORCL', 'ORLY', 'OXY', 'PANW', 'PAYX', 'PCAR', 'PDD', 'PEG', 'PEP',
 'PFE', 'PG', 'PGR', 'PINS', 'PKG', 'PLD', 'PLNT', 'PLTR', 'PNC', 'PPL',
 'PRU', 'PSX', 'PTC', 'PYPL', 'QCOM', 'RACE', 'RBLX', 'RCL', 'REGN', 'RIVN', 'ROK',
 'ROL', 'ROP', 'ROST', 'RTX', 'SBUX', 'SCHW', 'SE', 'SEDG', 'SGML', 'SHOP',
 'SHW', 'SLB', 'SMCI', 'SNAP', 'SNPS', 'SNY', 'SO', 'SOFI', 'SPG', 'SPGI',
 'SPOT', 'SRE', 'STLD', 'STT', 'STX', 'STZ', 'SWK', 'SWKS', 'SYF', 'SYY',
 'T', 'TBLA', 'TEAM', 'TEM', 'TFC', 'TGT', 'TJX', 'TMO', 'TMUS', 'TRMB',
 'TROW', 'TRV', 'TSCO', 'TSLA', 'TSN', 'TTD', 'TTWO', 'TXN', 'U', 'UBER',
 'ULTA', 'UNH', 'UNP', 'UPS', 'V', 'VFC', 'VLO', 'VRSK', 'VRTX', 'VSCO',
 'VTRS', 'VZ', 'WDAY', 'WDC', 'WEC', 'WELL', 'WFC', 'WIX', 'WM', 'WMB',
 'WMT', 'WRB', 'WY', 'XEL', 'XOM', 'XYZ', 'ZBH', 'ZBRA', 'ZG', 'ZS', 'ZTS'

# #  'FL', "BAC",
 ]


# # NASDAQ-listed tickers
# nasdaq_tickers = [
#     "AAPL", "ADBE", "ADI", "ADSK", "AFRM", "ALGN", "AMAT", "AMD", "AMGN", "AMZN",
#     "APP", "ARKK", "ARKW", "ASML", "AVGO", "BIIB", "BKNG", "CDNS", "CELH",
#     "CHTR", "CMCSA", "COST", "CRWD", "CSCO", "CTAS", "CTSH", "DDOG", "DOCU", "DXCM",
#     "EBAY", "EXPE", "FAST", "FTNT", "GILD", "GOOG", "GOOGL", "HAS", "HON", "HOOD",
#     "IDXX", "ILMN", "INTC", "INTU", "ISRG", "KLAC", "LRCX", "LULU", "MCHP", "MDB",
#     "MDLZ", "META", "MNST", "MRNA", "MRVL", "MSFT", "MTCH", "MU", "NFLX", "NKE",
#     "NVDA", "NXPI", "OKTA", "ORLY", "PANW", "PAYX", "PEP", "PINS", "PLTR", "PYPL",
#     "QCOM", "RBLX", "ROST", "SBUX", "SNPS", "SNAP", "SOFI", "TEAM", "TSLA", "TTD",
#     "TTWO", "TXN", "UBER", "ULTA", "VRSK", "VRTX", "WDAY", "WDC", "WIX", "ZS", "ZTS",
#     "ARM", "MNDY", "BKR", "INOD", "DPZ",
# ]

# NYSE-listed tickers
nyse_tickers = [
    "ABBV", "ABNB", "ABT", "ADM", "ADP", "AFL", "AIG", "ALK", "ALL", "AON", "APD",
    "AXP", "AZN", "BA", "BABA", "BAX", "BDX", "BG", "BK", "BMY", "BSX", "BWA",
    "BX", "BXP", "C", "CAG", "CAT", "CB", "CBOE", "CCI", "CCL", "CEG", "CHD", "CHRW",
    "CI", "CINF", "CL", "CLX", "CME", "CMG", "COF", "COP", "CPB", "CPRT", "CRL",
    "CRM", "CSX", "CVNA", "CVS", "CVX", "D", "DAL", "DE", "DECK", 
      "DHR", "DIS",
    "DKNG", "DLTR", "DOW", "DUK", "DXC", "ECL", "ED", "EFX", "EL", "EOG", "ES",
    "ETN", "ETR", "EVRG", "EXC", "EXR", "F", "FANG", "FHN", "FIS", "FIVE", "FL", "FTV",
    "GD", "GE", "GEHC", "GFS", "GIS", "GPN", "GRMN", 
    "GS", "HALO", "HCA", "HD", "HDB",
    "HIG", "HII", "HOG", "HPE", "HPQ", "HRB", "HST", "HUM", "IBM", "ICE", "IEX",
    "IP", "IPG", "JCI", "JNJ", "JPM", "KDP", "KHC", "KMB", "KMX", "KO", "LDOS",
    "LHX", "LII", "LIN", "LLY", "LMND", "LMT", "LNC", "LUMN", "LUV", "LVS", "LYB", "M",
    "MA", "MAR", "MC", "MCD", "MCK", "MCO", "MDT", "MELI", "MET", "MKTX", "MMM",
    "MO", "MP", "MPWR", "MRK", "MS", "MSCI", "MSI", "MUR", "NEE", "NEM", "NET",
    "NEU", "NIO", "NOC", "NOW", "NSC", "NTAP", "NTR", "NVR", "O", "ODFL", "OMC", "ON",
    "ORCL", "OXY", "PAYX", "PCAR", "PDD", "PEG", "PFE", "PG", "PGR", "PKG", "PLD",
    "PLNT", "PNC", "PPL", "PRU", "PSX", "PTC", "RCL", "REGN", "RIVN", "ROK", "ROL",
    "ROP", "RTX", "SCHW", "SE", "SEDG", "SGML", "SHOP", "SHW", "SLB", "SMCI", "SNY",
    "SO", "SPG", "SPGI", "SPOT", "SRE", "STLD", "STT", "STX", "STZ", "SWK", "SWKS",
    "SYF", "SYY", "T", "TBLA", "TFC", "TGT", "TJX", "TMO", "TMUS", "TRMB", "TROW", "XYZ", 
    "TRV", "TSCO", "TSN", "UNH", "UNP", "UPS", "V", "VFC", "VLO", "VSCO", "VTRS", "VZ",
    "WEC", "WELL", "WFC", "WM", "WMB", "WMT", "WRB", "WY", "XEL", "XOM", "ZBH", "ZBRA", "ZG"
]


IV_tickers = [
    "AAPL",
    "ABBV",
    "AMD",
    "AMZN",
    "AVGO",
    "BRK-B",
    "COST",
    "GOOG",
    "GOOGL",
    "HD",
    "JNJ",
    "JPM",
    "LLY",
    "MA",
    "META",
    "MSFT",
    "NFLX",
    "NVDA",
    "ORCL",
    "PLTR",
    "TSLA",
    "V",
    "WMT",
    "XOM"
]
