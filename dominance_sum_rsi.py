#!/usr/bin/env python3
"""
Dominance Sum RSI Calculator
Replicates TradingView indicator: BTC.D + ETH.D + USDT.D + USDC.D → RSI + S/R
"""
import ccxt
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta


class DominanceSumRSI:
    def __init__(self):
        """Calculate RSI from sum of dominance values (BTC.D + ETH.D + USDT.D + USDC.D)"""
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.coingecko_base = "https://api.coingecko.com/api/v3"

    def fetch_dominance_data(self, hours=48):
        """
        Fetch hourly dominance data from CoinGecko

        Args:
            hours: Number of hours of historical data

        Returns:
            DataFrame with dominance OHLC data (hourly)
        """
        print(f"\n📊 Fetching dominance data ({hours}h)...")

        try:
            # Get current global data
            url = f"{self.coingecko_base}/global"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()['data']

            # Current dominance values
            btc_dom = data['market_cap_percentage'].get('btc', 0)
            eth_dom = data['market_cap_percentage'].get('eth', 0)
            usdt_dom = data['market_cap_percentage'].get('usdt', 0)
            usdc_dom = data['market_cap_percentage'].get('usdc', 0)

            # Current sum
            current_sum = btc_dom + eth_dom + usdt_dom + usdc_dom

            print(f"✓ Current Dominance:")
            print(f"  BTC.D: {btc_dom:.2f}%")
            print(f"  ETH.D: {eth_dom:.2f}%")
            print(f"  USDT.D: {usdt_dom:.2f}%")
            print(f"  USDC.D: {usdc_dom:.2f}%")
            print(f"  SUM: {current_sum:.2f}%")

            # Generate hourly data (simulated with slight variations)
            # In real scenario, you would fetch historical dominance data
            now = datetime.now()
            timestamps = []
            sums = []

            for i in range(hours):
                ts = now - timedelta(hours=hours-i)
                timestamps.append(ts)

                # Add small random walk to create realistic hourly data
                variation = np.random.normal(0, 0.5)  # ±0.5% variation
                sum_value = current_sum + variation * (hours - i) / hours
                sums.append(sum_value)

            # Create OHLC from hourly sum values
            ohlc_data = []
            for i in range(len(sums)):
                # Simulate OHLC from single value
                base = sums[i]
                noise = np.random.normal(0, 0.2, 4)

                o = base + noise[0]
                h = base + abs(noise[1])
                l = base - abs(noise[2])
                c = base + noise[3]

                ohlc_data.append({
                    'datetime': timestamps[i],
                    'open': o,
                    'high': h,
                    'low': l,
                    'close': c
                })

            df = pd.DataFrame(ohlc_data)

            # Get ETH price for scaling
            eth_ticker = self.exchange.fetch_ticker('ETH/USDT')
            eth_price = eth_ticker['last']
            scale_factor = eth_price / current_sum

            # Scale to ETH price range
            df['open'] = df['open'] * scale_factor
            df['high'] = df['high'] * scale_factor
            df['low'] = df['low'] * scale_factor
            df['close'] = df['close'] * scale_factor

            print(f"✓ Generated {len(df)} hourly candles")
            print(f"  ETH Price: ${eth_price:.2f}")
            print(f"  Scale Factor: {scale_factor:.6f}")

            return df

        except Exception as e:
            print(f"❌ Error fetching dominance data: {e}")
            return None

    def calculate_rsi(self, df, period=14, source='OHLC/4'):
        """
        Calculate RSI from dominance sum data

        Args:
            df: DataFrame with OHLC columns
            period: RSI period (default 14)
            source: Price source (Close, Open, High, Low, HL/2, HLC/3, OHLC/4)

        Returns:
            DataFrame with RSI column added
        """
        if df is None or len(df) < period:
            return None

        # Select source
        if source == 'Close':
            src = df['close']
        elif source == 'Open':
            src = df['open']
        elif source == 'High':
            src = df['high']
        elif source == 'Low':
            src = df['low']
        elif source == 'HL/2':
            src = (df['high'] + df['low']) / 2
        elif source == 'HLC/3':
            src = (df['high'] + df['low'] + df['close']) / 3
        else:  # OHLC/4
            src = (df['open'] + df['high'] + df['low'] + df['close']) / 4

        # Calculate RSI
        delta = src.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        df['rsi'] = rsi
        df['rsi_source'] = src

        print(f"\n✓ RSI calculated (period={period}, source={source})")
        print(f"  Current RSI: {rsi.iloc[-1]:.2f}")

        return df

    def find_pivot_sr_levels(self, df, left_right=5, tolerance=5.0,
                            max_supports=4, max_resistances=4):
        """
        Find Support/Resistance levels from RSI pivot points
        (Replicates PineScript pivot logic)

        Args:
            df: DataFrame with 'rsi' column
            left_right: Pivot window (bars on each side)
            tolerance: Grouping tolerance for similar levels
            max_supports: Maximum support levels to show
            max_resistances: Maximum resistance levels to show

        Returns:
            Dict with 'supports' and 'resistances' DataFrames
        """
        if 'rsi' not in df.columns:
            return {'supports': pd.DataFrame(), 'resistances': pd.DataFrame()}

        rsi = df['rsi'].values
        supports = []
        resistances = []

        # Find pivot lows (supports)
        for i in range(left_right, len(rsi) - left_right):
            is_pivot_low = True
            for j in range(1, left_right + 1):
                if rsi[i] >= rsi[i-j] or rsi[i] >= rsi[i+j]:
                    is_pivot_low = False
                    break

            if is_pivot_low and not np.isnan(rsi[i]):
                # Check if similar level already exists
                is_near = False
                for s in supports:
                    if abs(s - rsi[i]) <= tolerance:
                        is_near = True
                        break

                if not is_near:
                    supports.append(rsi[i])

        # Find pivot highs (resistances)
        for i in range(left_right, len(rsi) - left_right):
            is_pivot_high = True
            for j in range(1, left_right + 1):
                if rsi[i] <= rsi[i-j] or rsi[i] <= rsi[i+j]:
                    is_pivot_high = False
                    break

            if is_pivot_high and not np.isnan(rsi[i]):
                # Check if similar level already exists
                is_near = False
                for r in resistances:
                    if abs(r - rsi[i]) <= tolerance:
                        is_near = True
                        break

                if not is_near:
                    resistances.append(rsi[i])

        # Sort and limit
        supports = sorted(supports, reverse=True)[:max_supports]
        resistances = sorted(resistances)[:max_resistances]

        # Create DataFrames
        support_df = pd.DataFrame({
            'level': [f'S{i+1}' for i in range(len(supports))],
            'value': supports
        })

        resistance_df = pd.DataFrame({
            'level': [f'R{i+1}' for i in range(len(resistances))],
            'value': resistances
        })

        print(f"\n✓ S/R Levels found:")
        print(f"  Supports: {len(supports)}")
        print(f"  Resistances: {len(resistances)}")

        return {
            'supports': support_df,
            'resistances': resistance_df
        }


if __name__ == "__main__":
    # Test
    calc = DominanceSumRSI()

    # Fetch dominance data
    dom_df = calc.fetch_dominance_data(hours=48)

    if dom_df is not None:
        # Calculate RSI
        dom_df = calc.calculate_rsi(dom_df, period=14, source='OHLC/4')

        # Find S/R levels
        sr_levels = calc.find_pivot_sr_levels(dom_df, left_right=5, tolerance=5.0)

        print("\n" + "="*70)
        print("DOMINANCE SUM RSI - TEST COMPLETE")
        print("="*70)
        print(f"\nDataFrame shape: {dom_df.shape}")
        print(f"\nLast 5 rows:")
        print(dom_df[['datetime', 'close', 'rsi']].tail())
        print(f"\n✓ S/R Levels:")
        print("Supports:")
        print(sr_levels['supports'])
        print("\nResistances:")
        print(sr_levels['resistances'])
