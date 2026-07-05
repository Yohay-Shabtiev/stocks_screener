# Quickselect Algorithm to find k-th smallest element
from pathlib import Path
import indicators.analysis_utils as an_utils
from datetime import datetime
import pandas as pd
import numpy as np
# from main import current_time
# from cup_handle import detect_cup_and_handle

HISTORICAL_INDICATOR_DIR = Path("historical_data") / "indicator_data"
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# this 
def ath_sma(tickers, daily_dfs):

    output = []
    BB_tickers, BB_dfs = shrinked_BBW(tickers, daily_dfs) 

    if len(tickers) != len(daily_dfs):
        raise ValueError("Lists are of different lengths")

    for ticker, df in zip(BB_tickers, BB_dfs):
        
        last_day = df.iloc[-1]
        sma_max_val = df['SMA_21'].max()
        ema_max_val = df['EMA_5'].tail(55).max()
        
        if last_day['EMA_5'] >= ema_max_val:
            output.append(ticker)

    with open(OUTPUT_DIR / 'ath_sma55.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output


def atr_starts_increase(tickers, daily_dfs):
    output = []

    # shrinked_BBW = find_shrinked_BBW(tickers, daily_dfs)
    # for ticker, df in shrinked_BBW:
    for ticker, df in zip(tickers, daily_dfs, strict=True):
        last_day = df.iloc[-1]
        atr_list = sorted(df[-255:]['ATR'].to_list())
        n = len(atr_list)
        if atr_list[int(n * 0.25)] < last_day['ATR'] < atr_list[int(n * 0.4)]:
            output.append((ticker, df))

    with open(OUTPUT_DIR / "atr_starts_increase.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker, _ in output)
    
    return output


def bbw_from_dec_to_inc(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        
        last_day = df.iloc[-1]

        for i in range(-21, -10):
            bw = df.iloc[i:i + 10]['BandWidth']

            if bw.is_monotonic_decreasing:
                if last_day['BandWidth'] > df.iloc[-2]['BandWidth'] and\
                    last_day['Volume'] > df['Volume'].tail(21).mean():
                
                    output.append(ticker)
                    break

    with open(OUTPUT_DIR / 'bbw_from_dec_to_inc.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output


def crossing_BB(tickers, daily_dfs):

    crossing_up = crossing_upper_BB(tickers, daily_dfs)
    crossing_down = crossing_lower_BB(tickers, daily_dfs)

    return crossing_up, crossing_down

def crossing_upper_BB(tickers):

    output = []

    for ticker in tickers:
        df = pd.read_csv(HISTORICAL_INDICATOR_DIR / f"{ticker}.csv")
        last_day = df.iloc[-1]
        if last_day['High'] > last_day['UpperBand']:
                output.append(ticker)
    
    with open(OUTPUT_DIR / "Crossed_Upper_BB.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output

def crossing_lower_BB(tickers, daily_dfs):

    output = []
    
    for ticker, df in zip(tickers, daily_dfs, strict=True):
        if df.iloc[-1]['Low'] < df.iloc[-1]['LowerBand']:
            output.append(ticker)

    with open(OUTPUT_DIR / "CrossLowerBB.txt", "w") as f:
        f.write("The stocks crossing the lowerBand are:")
        f.writelines(ticker + '\n' for ticker in output)

    return output


def closed_yesterday_gap(tickers, daily_dfs):

    output = []
    
    for i in range(len(tickers)):
        df = daily_dfs[i]
        n = len(df['Close'])

        if df.iloc[n - 1]['Open'] / df.iloc[n - 2]['High'] > 1.01: # the gap is greater than 1%
            if df.iloc[n - 1]['Low'] / df.iloc[n - 2]['High'] < 1.002: # the gap was closed/almost closed today
                output.append(tickers[i])

    with open(OUTPUT_DIR / "Closed_yesterday_gap.txt", "w") as f:
        f.writelines(ticker + "\n" for ticker in output)

    return output


def close_52w_high(tickers, daily_dfs):

    shrinked_bb_tickers = shrinked_BBW(tickers, daily_dfs)
    perfect_smas_tickers, perfect_smas_dfs = perfect_smas(tickers, daily_dfs)
    output = []

    for ticker, df in zip(perfect_smas_tickers, perfect_smas_dfs, strict=True):
        high_52w = max(df.iloc[-240:]["Close"].tolist())
        
        days_change = (high_52w - df.iloc[-1]["Close"]) / high_52w
        if days_change < 0.03 and ticker in shrinked_bb_tickers:
            output.append((ticker, days_change))

    with open(OUTPUT_DIR / "close_52w_high.txt", "w") as f:
        f.writelines(f'{tup[0]} : {tup[1]}\n' for tup in output)


# 4.9
# the beginning of september is seasonly a decreasing time
# QQQ bbW are shrinked, can't break through SMA21
# VIX makes new min points but the RSI is getting stronger
def certainty_stocks_uncertainty_qqq(tickers, daily_dfs, range):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        bbw_25 = df[-range:]['BandWidth'].quantile(0.25)
        atr_25 = df[-range:]['ATR'].quantile(0.25)
        last_day = df.iloc[-1]
        
        if last_day['BandWidth'] < bbw_25 and last_day['ATR'] < atr_25 and\
            last_day['SMA_21'] > last_day['SMA_144']:

            output.append(ticker)
    
    with open(OUTPUT_DIR / 'certainty_stocks_uncertainty_qqq.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output


def change_equal_atr(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        n = df.shape[0]
        if abs(df.iloc[n - 1]['Change%']) / df.iloc[n - 1]['ATR%'] > 0.85:
            output.append(ticker)

    with open(OUTPUT_DIR / "change_equal_atr.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker in output)
    
    return output


def calculate_all_time_highs(ticker, df, days):
    
    output = []

    output.append((df.index[-1 * days], df.iloc[-1 * days]["Close"]))   # start with first value
    if ticker == "MNDY":
        print(df.iloc[-1 * days]["Date"])
    for i in range(df.shape[0] - days, df.shape[0]):
        if df.iloc[i]["Close"] > output[-1][1]:         # compare with last ATH
            output.append((df.index[i], df.iloc[i]["Close"]))
        
    return output


def create_weekly_df(ticker, df):

    weekly_df = pd.DataFrame()
    weeks = match_date_to_week(df)

    for week in weeks.values():
        row = pd.DataFrame({
                'Date': week[-1],  # the last date of the week
                'Close': df.loc[week[-1], 'Close'],  
                'High': max(df.loc[week, 'High']),
                'Low': min(df.loc[week, 'Low']),
                'Open': df.loc[week[0], 'Open'],
                'Volume': df.loc[week, 'Volume'].sum()
            }, index=[0])
        weekly_df = pd.concat([weekly_df, row])

    return weekly_df


# this function converts a daily df to weekly df
    # param tickers - a list of tickers
    # param daily_dfs - a list of dfs
def day_to_week_convertor(tickers, daily_dfs):

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        df_weekly = create_weekly_df(ticker, df)
        df_weekly.to_csv(f"historical_data(weekly)/{ticker}(1w-SOURCE).csv")


# lists is a list of lists where each list contains tuples
def get_intersection(lists: list) -> list:
    
    sets = [set(t[0] for t in lst) for lst in lists] # set of sets each set contain just the tickers
    common_tickers = set.intersection(*sets)

    intersection = [t for lst in lists for t in lst if t[0] in common_tickers]

    return intersection


def golden_cross(all_tickers, daily_dfs):

    tickers = []
    dfs = []

    for ticker, df in zip(all_tickers, daily_dfs, strict=True):
        last_day = df.iloc[-1]
        
        close_above_sma21 = last_day['Close'] > last_day['SMA_21']
        low_bandwidth = last_day['BandWidth'] < df['BandWidth'].mean()
        momentum_condition = last_day['SMA_55'] + last_day['ATR'] >= last_day['SMA_200']

        if close_above_sma21 and low_bandwidth and momentum_condition:
            tickers.append(ticker)
            dfs.append(df)
        
    
    tickers = increasing_emas(tickers, dfs)

    with open(OUTPUT_DIR / 'golden_cross.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in tickers)

    return tickers

def green_candles(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        n = df.shape[0]
        open_values = df['Open'].tolist()
        close_values = df['Close'].tolist()

        if open_values[n - 1] < close_values[n - 1]:
            output.append(ticker)

    with open(OUTPUT_DIR / "green_candles.txt", "w") as f:
        f.writelines(_ + '\n' for _ in output)

    return output








def red_day(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        n = df.shape[0]
        
        if df.iloc[n - 2]['Close'] > df.iloc[n - 1]['Close']:
            output.append(ticker)


    with open(OUTPUT_DIR / "red_day.txt", "w") as f:
        f.writelines(_ + '\n' for _ in output)

    return output






# difference between EMA5 and EMA8 is greater than yesterday
def increasing_emas(tickers, daily_dfs):

    output = []
    output2 = []
    for ticker, df in zip(tickers, daily_dfs, strict=True):
        n = df.shape[0]
        ema5 = df['EMA_5'].tolist()
        ema8 = df['EMA_8'].tolist()
        if (ema5[n - 3] - ema8[n - 3]) > 0:
            if (ema5[n - 1] - ema8[n - 1]) > (ema5[n - 2] - ema8[n - 2]) > (ema5[n - 3] - ema8[n - 3]):
                output.append((ticker, df))
                output2.append(ticker)

    with open(OUTPUT_DIR / "increasing_emas.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker, _ in output)
    
    return output2

def flat_atr(tickers, daily_dfs):

    output = []
    flag = True

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        flag = True
        n = df.shape[0]
        atr = df['ATR%'].tolist()
        for i in range(5):
            if abs(atr[n - i - 1] - atr[n - i - 2]) / atr[n - i - 1] > 0.05:
                flag = False
        if flag:
            output.append((ticker, df))

    with open(OUTPUT_DIR / "flat_atr.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker, _ in output)
    
    return output


def increasing_volume(tickers, daily_dfs):
    
    output = []

    for i in range(len(tickers)):
        df = daily_dfs[i]
        volumes = df['Volume'].tolist() 
        n = len(volumes)

        # if 0 <= current_time.weekday() < 5 and 16 <= current_time.hour < 22:
        if 1.15 * volumes[n - 5] <= volumes[n - 4] and 1.15 * volumes[n - 4] <= volumes[n - 3]:
            output.append(tickers[i])
            
        # elif 0 <= current_time.weekday() < 5 and 22 <= current_time.hour < 23:
        #     if volumes[n - 3] <= volumes[n - 2] and 1.15 * volumes[n - 4] <= volumes[n - 3]:
        #         output.append(tickers[i])

        # else:
        #     if 1.15 * volumes[n - 4] <= volumes[n -3] and 1.15 * volumes[n - 3] <= volumes[n - 2]:
        #         output.append(tickers[i])
        

    with open(OUTPUT_DIR / "increasing_volume.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output



def lower_BB_stablize(tickers, daily_dfs):

    output = []
    for i in range(len(tickers)):

        df = daily_dfs[i]
        n = df.shape[0]

        if abs(df.iloc[n - 1]['LowerBand'] - df.iloc[n - 2]['LowerBand']) / df.iloc[n - 1]['LowerBand'] < 0.005:
            output.append(tickers[i])

    print("stocks getting stable are:")
    return output

def nio_pattern(tickers, daily_dfs):

    output = []
    current_time = datetime.now()
    increasing_volume_tickers = increasing_volume(tickers, daily_dfs)

    for ticker in increasing_volume_tickers:
        df = daily_dfs[tickers.index(ticker)]
        n = len(df['Close'])

        if 0 <= current_time.weekday() < 5 and 16 <= current_time.hour < 22:
            if df.iloc[n - 2]['High'] < df.iloc[n - 3]['High'] and df.iloc[n - 2]['Low'] > df.iloc[n - 3]['Low']:
                output.append(ticker)            
        else:
            if df.iloc[n - 1]['High'] < df.iloc[n - 2]['High'] and df.iloc[n - 21]['Low'] > df.iloc[n - 2]['Low']:
                output.append(ticker)

        with open(OUTPUT_DIR / "nio_pattern.txt", "w") as f:
            f.writelines(ticker + '\n' for ticker in output)

    return output





def match_date_to_week(df):

    dates_per_week = {}
    dates = df.index.to_list()
    
    for date in dates:
        year, week, _ = date.isocalendar()
        key = (year, week)
        dates_per_week.setdefault(key, []).append(date)
    
    return dates_per_week

# LOW BBW IS CONSIDERED BBW LOWER THAN 52WEEK QURTER'S BBW VALUE 
    # RETURN A LIST OF TICKERS WITH LOW BBW
    # PARAM TICKERS - LIST WITH TICKERS STRINGS
    # PARAM DFS - LIST WITH DATAFRAMES THE i DF MATCH THE i TICKER
def shrinked_BBW(tickers, dfs):
    shrinked_BBW_tickers = []
    shrinked_BBW_dfs = []

    for ticker, df in zip(tickers, dfs, strict=True):    
        bandwidth_values = df['BandWidth'].tolist()
        n = len(bandwidth_values)
        bandwidth_values.sort()
        third_index = int(0.35 * n)

        if df.iloc[-1]['Close'] > df.iloc[-1]['SMA_21']:
            if df.iloc[-1]['BandWidth'] > df.iloc[-2]['BandWidth']:
                if df.iloc[-1]['BandWidth'] < bandwidth_values[third_index]:
                    shrinked_BBW_tickers.append(ticker)
                    shrinked_BBW_dfs.append(df)

    with open(OUTPUT_DIR / "Shrinked_BBW.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker in shrinked_BBW_tickers)

    return shrinked_BBW_tickers, shrinked_BBW_dfs


# This function finds the stockes were the upper bb
def wider_BB(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        n = df.shape[0]   
        # if df.iloc[n-1]['Close'] > df.iloc[n-1]['SMA_55'] > df.iloc[n-1]['SMA_200']:
        if df.iloc[n-1]['Volume'] > 0.9 * df.iloc[n-2]['Volume']:
            if df.iloc[n - 1]['BandWidth'] > df.iloc[n - 2]['BandWidth'] > df.iloc[n - 3]['BandWidth']:
                output.append((ticker, df))

        with open(OUTPUT_DIR / "wider_BB.txt", "w") as f:
            f.writelines(ticker + '\n' for ticker, _ in output)
    
    return output



def risk_less_than_atr(tickers, daily_dfs):

    output = []
    for ticker, df in zip(tickers, daily_dfs, strict=True):
        # n = df.shape[0]
        # lowest_2_weeks = min(df[n - 10:]['Low'])
        yesterday_row = df.iloc[-1]
        if yesterday_row['Low'] - yesterday_row['ATR'] < df['Low'].iloc[-21:].min():
            if yesterday_row['Close'] > yesterday_row['SMA_144']: 
                if df.iloc[-5]['SMA_21'] < df.iloc[-1]['SMA_21']: 
                    output.append(ticker)

    with open(OUTPUT_DIR / "risk_less_than_atr.txt", "w") as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output


def price_below_SMA_but_still_SMA_trend(tickers, daily_dfs, sma):
    
    sma_col = "SMA_" + str(sma)
    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        last_day = df.iloc[-1]
        if last_day['SMA_55'] > df.iloc[-55]['SMA_55']:
            if last_day['Close'] < last_day[sma_col] and last_day['Close'] - last_day['ATR'] > last_day['SMA_55']:
                output.append(ticker)

    with open(OUTPUT_DIR / f'{sma}trend_price_below_{sma}.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output


def low_vol_fall(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        day = -2
        counter = 0
        while (df.iloc[day]['Close'] < df.iloc[day - 1]['Close'] and 
                df.iloc[day]['Volume'] < df.iloc[day - 1]['Volume']):
            day -= 1
            counter += 1

        
        if counter >= 2 and df.iloc[-1]['Close'] > df.iloc[-1]['Open']:
            output.append(ticker)

    with open(OUTPUT_DIR / 'low_vol_fall.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output





def perfect_smas(tickers, daily_dfs):
    
    output_tickers = []
    output_dfs = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        last_day = df.iloc[-1]
        if df.iloc[-1]['SMA_21'] > df.iloc[-3]['SMA_21']:
            if last_day['SMA_55'] > last_day['SMA_89'] and last_day['SMA_89'] < last_day['SMA_55'] and\
                last_day['SMA_144'] < last_day['SMA_89']:
            # and last_day['SMA_200'] < last_day['SMA_144']:
            
                output_tickers.append(ticker)
                output_dfs.append(df)

    with open(OUTPUT_DIR / 'perfect_smas.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output_tickers)

    return output_tickers, output_dfs

def recently_high_volume(tickers, daily_dfs, short, long):
    
    ticks = []
    dfs = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        
        short_range_total_volume = df[-1*short:-1]['Volume'].sum()
        long_range_total_volume = df[-1*long:-1]['Volume'].sum()
        if df.iloc[-1]['SMA_55'] > df.iloc[-1]['SMA_89'] > df.iloc[-1]['SMA_144']:
            if short_range_total_volume / long_range_total_volume > short / long:
                ticks.append(ticker)
                dfs.append(df)

    with open(OUTPUT_DIR / 'recently_high_volume.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in ticks)

    return ticks, dfs




def frequent_new_highs(tickers, daily_dfs, days):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        highs = calculate_all_time_highs(ticker, df, days)
        output.append((ticker, len(highs)))

    sorted_data = sorted(output, key=lambda x: x[1], reverse=True)

    with open(OUTPUT_DIR / "most_frequent_ATH.txt", "w") as f:
        f.writelines(f'{x[0]} : {x[1]}\n' for x in sorted_data)
        


def too_volatile(tickers, daily_dfs, days):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        days_high = max(df.iloc[-days:]["Close"].tolist())
        
        days_change = (days_high - df.iloc[-1]["Close"]) / days_high
        if days_change > 0.10:
            output.append((ticker, days_change))

    with open(OUTPUT_DIR / "too_volatile.txt", "w") as f:
        f.writelines(f'{tup[0]} : {tup[1]}\n' for tup in output)




def marubozu_candle(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        for i in range(1, 2):
            if df.iloc[-i]["Close"] > df.iloc[-i]["Open"]: # a green day
                if an_utils.no_wick(df.iloc[-i]["Close"], df.iloc[-i]["High"]) and\
                    an_utils.no_wick(df.iloc[-i]["Open"], df.iloc[-i]["Low"]): # no wicks

                    output.append(ticker)
                    break

    with open(OUTPUT_DIR / f'marubozu_candle.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output
                    
def doji(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):

        last_day = df.iloc[-1]
        sma21_is_decreasing = df['SMA_21'].tail(8).is_monotonic_decreasing
        change_percentage = abs(last_day['Close'] - last_day['Open']) / last_day['Open']
        
        if change_percentage <= 0.0015: # it's a doji candle
            if sma21_is_decreasing and last_day['SMA_21'] > last_day['SMA_200']: # the short trnd is indeed bearish
                output.append(ticker)

    with open(OUTPUT_DIR / 'doji.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output






def write_hits_once(hits, out_path=OUTPUT_DIR / "cup&handle.txt", clear=True, dedupe=True, sort_hits=False):
    """Write all hits to file in a single write (optionally dedupe/sort)."""
    if dedupe:
        # stable de-dup (preserve first-seen order)
        hits = list(dict.fromkeys(hits))
    if sort_hits:
        hits = sorted(hits)

    mode = "w" if clear else "a"
    if not hits and mode == "a":
        return 0
    with open(out_path, mode, encoding="utf-8") as f:
        if hits:
            f.write("\n".join(hits) + "\n")
    return len(hits)

def marubozu_after_doji(tickers, daily_dfs):

    output = []

    for ticker, df in zip(tickers, daily_dfs, strict=True):
        for i in range(2, 22):

            day = df.iloc[-i]
            the_day_before = df.iloc[-(i + 1)]
            
            if (an_utils.is_marubuzo(day) and an_utils.is_doji(the_day_before)) or\
                (an_utils.is_marubuzo(the_day_before) and an_utils.is_doji(day)):
                output.append(ticker)
                break
        
    with open(OUTPUT_DIR / 'marubozu_after_doji.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output

def close_to_lower_BB(tickers, dfs):

    output = []

    if len(tickers) != len(dfs):
        raise ValueError("Lists are of different lengths")

    for ticker, df in zip(tickers, dfs):
        last_day = df.iloc[-1]

        if last_day["Low"] - last_day["LowerBand"] <= last_day["ATR"]:
            max_lower_band = df["LowerBand"].tail(21).max()
            min_lower_band = df["LowerBand"].tail(21).min()
            if max_lower_band - min_lower_band < last_day["ATR"]:
                output.append(ticker)

    with open(OUTPUT_DIR / 'close_to_lower_BB.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output
            

def close_to_21_low(tickers, dfs):

    output = []

    if len(tickers) != len(dfs):
        raise ValueError("Lists are of different lengths")

    for ticker, df in zip(tickers, dfs):
        last_day = df.iloc[-1]
        if last_day["SMA_21"] >  df.iloc[-2]["SMA_21"]:
            min_21 = df["Low"].tail(21).min()
            if last_day["Close"] - last_day["ATR"] <= min_21:
                output.append(ticker)

    with open(OUTPUT_DIR / 'close_to_21_low.txt', 'w') as f:
        f.writelines(ticker + '\n' for ticker in output)

    return output


