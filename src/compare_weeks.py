"""Compare two weekly scan output files.

Usage:
    python src/compare_weeks.py                                       # auto-finds the two most recent week*.txt files in outputs/
    python src/compare_weeks.py outputs/2026week25.txt outputs/2026week26.txt
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

import pandas as pd

INDICATOR_DIR = Path('historical_data') / 'indicator_data'

SECTOR_NAMES = {
    'XLK':  'Technology',
    'XLF':  'Financials',
    'XLE':  'Energy',
    'XLV':  'Health Care',
    'XLI':  'Industrials',
    'XLY':  'Consumer Disc.',
    'XLP':  'Consumer Staples',
    'XLU':  'Utilities',
    'XLRE': 'Real Estate',
    'XLB':  'Materials',
    'XLC':  'Comm. Services',
}


def parse_file(path: Path) -> tuple[dict, dict]:
    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    return _parse_sector_table(lines), _parse_stock_signals(lines)


def _parse_sector_table(lines: list[str]) -> dict:
    result = {}
    in_table = False
    for line in lines:
        if 'Ticker' in line and 'Sector' in line and 'vs SPX' in line:
            in_table = True
            continue
        if not in_table:
            continue
        if re.match(r'\s*-{4,}\s*$', line):
            if result:
                break
            continue
        m = re.match(r'\s*(XL\w+)\s+\S', line)
        if m:
            etf = m.group(1)
            pcts = re.findall(r'([+-]?\d+\.\d+)%', line)
            result[etf] = {
                '1W':     float(pcts[0]) if len(pcts) > 0 else None,
                'vs_spx': float(pcts[1]) if len(pcts) > 1 else None,
            }
    return result


def _parse_stock_signals(lines: list[str]) -> dict:
    result: dict = {}
    current_etf = None
    current_cat = None

    for line in lines:
        m = re.match(r'\s+(XL\w+)\s+.+ETF\s*->', line)
        if m:
            current_etf = m.group(1)
            result[current_etf] = {'DCA': [], 'Delayed': []}
            current_cat = None
            continue

        if current_etf is None:
            continue

        if re.search(r'\[DCA\s*-', line):
            current_cat = 'DCA'
            continue
        if re.search(r'\[Delayed\s*-', line):
            current_cat = 'Delayed'
            continue

        if current_cat is None:
            continue

        if re.match(r'\s*[-=]{4,}', line) or not line.strip():
            continue
        if 'Ticker' in line and 'vs ETF' in line:
            continue

        m = re.match(r'\s+([A-Z]+)\s+', line)
        if m:
            result[current_etf][current_cat].append(m.group(1))

    return result


def _fmt(val: float | None) -> str:
    if val is None:
        return 'n/a'
    sign = '+' if val >= 0 else ''
    return f'{sign}{val:.2f}%'


def compare(path_a: Path, path_b: Path) -> None:
    label_a = path_a.stem
    label_b = path_b.stem

    sec_a, stocks_a = parse_file(path_a)
    sec_b, stocks_b = parse_file(path_b)

    # ── Sector 1W comparison ──────────────────────────────────────────────────
    all_etfs = sorted(set(sec_a) | set(sec_b))
    rows = []
    for etf in all_etfs:
        va  = sec_a.get(etf, {}).get('1W')
        vb  = sec_b.get(etf, {}).get('1W')
        vsa = sec_a.get(etf, {}).get('vs_spx')
        vsb = sec_b.get(etf, {}).get('vs_spx')
        chg = (vb - va) if (va is not None and vb is not None) else None
        rows.append((etf, va, vb, chg, vsa, vsb))
    rows.sort(key=lambda r: (r[3] is None, -(r[3] or 0)))

    W = 9
    print('\n' + '=' * 84)
    print(f"  SECTOR 1W PERFORMANCE   {label_a}  ->  {label_b}")
    print('=' * 84)
    print(f"  {'ETF':<6}  {'Sector':<22}  {label_a:>{W}}  {label_b:>{W}}  {'Change':>{W}}  {'vSPX '+label_a[-2:]:>{W}}  {'vSPX '+label_b[-2:]:>{W}}")
    print('  ' + '-' * 80)
    for etf, va, vb, chg, vsa, vsb in rows:
        name = SECTOR_NAMES.get(etf, etf)
        ba   = '>' if (vsa is not None and vsa > 0) else ' '
        bb   = '>' if (vsb is not None and vsb > 0) else ' '
        arrow = ('+' if chg > 0 else '-') if chg is not None else ' '
        print(f"  {etf:<6}  {name:<22}  {_fmt(va):>{W}}  {_fmt(vb):>{W}}  {arrow}{_fmt(chg):>{W}}  {ba}{_fmt(vsa):>{W-1}}  {bb}{_fmt(vsb):>{W-1}}")

    # ── Stock signal changes ───────────────────────────────────────────────────
    all_etfs2 = sorted(set(stocks_a) | set(stocks_b))

    print('\n' + '=' * 84)
    print(f"  STOCK SIGNAL CHANGES   {label_a}  ->  {label_b}")
    print('=' * 84)

    for etf in all_etfs2:
        sa = stocks_a.get(etf, {'DCA': [], 'Delayed': []})
        sb = stocks_b.get(etf, {'DCA': [], 'Delayed': []})

        dca_a = set(sa['DCA'])
        dca_b = set(sb['DCA'])
        del_a = set(sa['Delayed'])
        del_b = set(sb['Delayed'])

        graduated = sorted(del_a & dca_b)               # Delayed -> DCA
        weakened  = sorted(dca_a & del_b)               # DCA -> Delayed
        dca_cont  = sorted(dca_a & dca_b)               # DCA in both
        dca_new   = sorted(dca_b - dca_a - del_a)       # brand new DCA
        dca_drop  = sorted((dca_a - dca_b) - del_b)     # left DCA entirely
        del_cont  = sorted((del_a & del_b) - dca_a)     # Delayed in both
        del_new   = sorted((del_b - del_a) - dca_a)     # brand new Delayed
        del_drop  = sorted((del_a - del_b) - dca_b)     # left Delayed entirely

        if not any([graduated, weakened, dca_cont, dca_new, dca_drop,
                    del_cont, del_new, del_drop]):
            continue

        name = SECTOR_NAMES.get(etf, etf)
        print(f"\n  {etf}  {name}")
        print('  ' + '-' * 60)

        def _row(sym: str, label: str, tickers: list[str]) -> None:
            if tickers:
                print(f"  {sym} {label:<24} {', '.join(tickers)}")

        _row('^', 'Graduated (->DCA):',    graduated)
        _row('v', 'Weakened (->Delayed):',  weakened)
        _row(' ', 'DCA continued:',         dca_cont)
        _row('+', 'DCA new:',               dca_new)
        _row('-', 'DCA dropped:',           dca_drop)
        _row(' ', 'Delayed continued:',     del_cont)
        _row('+', 'Delayed new:',           del_new)
        _row('-', 'Delayed dropped:',       del_drop)

    print('\n' + '=' * 84)
    print('  ^ Graduated: was Delayed -> now DCA  |  v Weakened: was DCA -> now Delayed')
    print('  + New signal  |  - Dropped from signal\n')

    # ── SMA21 pullback/recovery pattern scan ───────────────────────────────────
    tickers = collect_tickers(stocks_a) | collect_tickers(stocks_b)
    ticker_etf = ticker_etf_map(stocks_a, stocks_b)
    matched = find_sma21_pattern_stocks(tickers)
    print_sma21_pattern_results(matched, ticker_etf)


def collect_tickers(stocks: dict) -> set[str]:
    """Flatten the {etf: {'DCA': [...], 'Delayed': [...]}} structure into a ticker set."""
    tickers: set[str] = set()
    for cats in stocks.values():
        tickers.update(cats.get('DCA', []))
        tickers.update(cats.get('Delayed', []))
    return tickers


def ticker_etf_map(*stocks_dicts: dict) -> dict[str, str]:
    """Map each ticker to its sector ETF, using the {etf: {'DCA': [...], 'Delayed': [...]}} structure."""
    mapping: dict[str, str] = {}
    for stocks in stocks_dicts:
        for etf, cats in stocks.items():
            for ticker in cats.get('DCA', []) + cats.get('Delayed', []):
                mapping[ticker] = etf
    return mapping


def passes_sma21_pattern(df: pd.DataFrame) -> bool:
    """
    Last 21 trading days, split into an 11-day head and a 10-day tail:
      - SMA_21 must be higher now than 21 days ago (trending up)
      - at least 8 of the 11 head days close above SMA_21
      - at most 8 of the 10 tail days close below SMA_21
      - SMA_200 must not be above the upper Bollinger band (current day)
    """
    req = {'Close', 'SMA_21', 'SMA_200', 'UpperBand'}
    if not req.issubset(df.columns):
        return False

    df = df.sort_index()
    df = df[~df.index.duplicated(keep='last')]
    if len(df) < 21:
        return False

    last21 = df.tail(21)
    if last21['SMA_21'].isna().any():
        return False

    if not (last21['SMA_21'].iloc[-1] > last21['SMA_21'].iloc[0]):
        return False

    head = last21.iloc[:11]
    tail = last21.iloc[11:]

    above_head = (head['Close'] > head['SMA_21']).sum()
    below_tail = (tail['Close'] < tail['SMA_21']).sum()

    last = df.iloc[-1]
    if pd.isna(last['SMA_200']) or pd.isna(last['UpperBand']):
        return False
    if last['SMA_200'] > last['UpperBand']:
        return False

    return above_head >= 8 and below_tail <= 8


def find_sma21_pattern_stocks(tickers: set[str], indicator_dir: Path = INDICATOR_DIR) -> list[str]:
    matched = []
    for ticker in sorted(tickers):
        try:
            df = pd.read_csv(indicator_dir / f'{ticker}.csv', index_col=0, parse_dates=True)
        except FileNotFoundError:
            continue
        if passes_sma21_pattern(df):
            matched.append(ticker)
    return matched


def print_sma21_pattern_results(matched: list[str], ticker_etf: dict[str, str]) -> None:
    print('\n' + '=' * 84)
    print('  SMA21 PULLBACK/RECOVERY PATTERN (last 21 trading days)')
    print('=' * 84)
    if matched:
        for ticker in matched:
            etf = ticker_etf.get(ticker, '')
            sector = SECTOR_NAMES.get(etf, etf or 'Unknown')
            print(f'  {ticker:<8} {etf:<6} {sector}')
    else:
        print('  (none)')
    print()


if __name__ == '__main__':
    if len(sys.argv) == 3:
        a, b = Path(sys.argv[1]), Path(sys.argv[2])
    else:
        files = sorted(Path('outputs').glob('*week*.txt'))
        if len(files) < 2:
            print("Error: need at least 2 week*.txt files in outputs/, or pass them as arguments.")
            sys.exit(1)
        a, b = files[-2], files[-1]
        print(f"Comparing {a.name} vs {b.name}")

    for p in (a, b):
        if not p.exists():
            print(f"Error: {p} not found")
            sys.exit(1)

    compare(a, b)
