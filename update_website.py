#!/usr/bin/env python3
"""
GitHub Actions için tek seferlik güncelleme script'i
Bilgisayar kapalıyken bile her 15 dakikada çalışır
"""
import sys
from datetime import datetime
import pytz
from altcoin_ratio import AltcoinRatioCalculator
from altcoin_visualizer import AltcoinRatioVisualizer
from liquidity_levels import LiquidityAnalyzer
from risk_metrics_calculator import RiskMetricsCalculator
from detailed_risk_analyzer import DetailedRiskAnalyzer
from dominance_sum_rsi import DominanceSumRSI

def main():
    print("=" * 70)
    print("  GITHUB ACTIONS - AUTOMATED UPDATE")
    print("=" * 70)

    dubai_tz = pytz.timezone('Asia/Dubai')
    dubai_time = datetime.now(dubai_tz).strftime('%H:%M:%S')
    print(f"\n🕐 Dubai Time: {dubai_time}")

    # Initialize
    calculator = AltcoinRatioCalculator()
    visualizer = AltcoinRatioVisualizer()
    liquidity = LiquidityAnalyzer()
    risk_calculator = RiskMetricsCalculator()
    detailed_analyzer = DetailedRiskAnalyzer()
    dominance_rsi_calc = DominanceSumRSI()

    # Fetch market data with retry
    print("\n📊 Fetching market data...")
    market_data = None
    for retry in range(3):
        market_data = calculator.fetch_market_caps()
        if market_data:
            break
        print(f"⚠ Retry {retry+1}/3...")
        import time
        time.sleep(5)

    if not market_data:
        print("❌ Market data failed after 3 retries")
        sys.exit(1)

    # Fetch price data with retry
    print("📈 Fetching ETH/USDT data...")
    overlay_df = None
    for retry in range(3):
        overlay_df = calculator.fetch_overlay_price('ETH/USDT', '15m', days=10)
        if overlay_df is not None:
            break
        print(f"⚠ Retry {retry+1}/3...")
        import time
        time.sleep(5)

    if overlay_df is None:
        print("❌ Price data failed after 3 retries")
        sys.exit(1)

    print(f"✅ Fetched {len(overlay_df)} candles")

    # Calculate ratio
    print("🧮 Calculating altcoin ratio...")
    ratio_df = calculator.calculate_synthetic_altcoin_ratio(overlay_df, market_data, 'ETH')
    ratio_df = calculator.calculate_indicators(ratio_df)

    # Calculate S/R levels
    print("📍 Finding S/R levels...")
    sr_result = calculator.find_auto_sr_levels_pinescript(
        ratio_df, left_right=3, tolerance=30.0,
        max_supports=4, max_resistances=4
    )

    # BSL/SSL
    print("🔍 Calculating swing levels...")
    ratio_ohlc = ratio_df[['datetime', 'ar_open', 'ar_high', 'ar_low', 'ar_close']].copy()
    ratio_ohlc.columns = ['datetime', 'open', 'high', 'low', 'close']
    swings = liquidity.find_swing_highs_lows(ratio_ohlc, swing_length=10)

    bsl = swings['swing_highs']['price'].iloc[-1] if len(swings['swing_highs']) > 0 else None
    ssl = swings['swing_lows']['price'].iloc[-1] if len(swings['swing_lows']) > 0 else None

    # Footprint
    footprint_df = calculator.calculate_footprint(ratio_df, lookback=50)

    # Dominance Sum RSI
    print("📊 Calculating Dominance Sum RSI...")
    dom_rsi_df = dominance_rsi_calc.fetch_dominance_data(hours=48)
    if dom_rsi_df is not None:
        dom_rsi_df = dominance_rsi_calc.calculate_rsi(dom_rsi_df, period=14, source='OHLC/4')
        dom_sr_levels = dominance_rsi_calc.find_pivot_sr_levels(
            dom_rsi_df,
            left_right=5,
            tolerance=5.0,
            max_supports=3,
            max_resistances=3
        )
        # Attach S/R levels to dataframe attributes for visualizer
        dom_rsi_df.attrs['rsi_supports'] = dom_sr_levels['supports']
        dom_rsi_df.attrs['rsi_resistances'] = dom_sr_levels['resistances']
        print("✅ Dominance RSI calculated")
    else:
        dom_rsi_df = None
        print("⚠ Dominance RSI failed, continuing without it")

    # Create main chart (WITHOUT order book - GitHub Actions can't do WebSocket)
    print("📊 Creating main chart...")
    output_file = "altcoin_combined_eth_live.html"
    visualizer.create_combined_chart(
        btc_df=overlay_df,
        ratio_df=ratio_df,
        orderbook_data=None,  # No WebSocket in GitHub Actions
        support_levels=sr_result['supports'],
        resistance_levels=sr_result['resistances'],
        bsl_ssl={'bsl': bsl, 'ssl': ssl},
        footprint_df=footprint_df,
        dominance_rsi_df=dom_rsi_df,  # NEW: Add Dominance RSI
        orderbook_candles=100,
        output_file=output_file
    )
    print(f"✅ Chart saved: {output_file}")

    # Calculate Risk Metrics
    print("📊 Calculating risk metrics...")
    coins = {
        'SOL': 'SOL/USDT',
        'ETH': 'ETH/USDT',
        'BNB': 'BNB/USDT',
        'XRP': 'XRP/USDT'  # Changed from DASH (not available on Kraken)
    }

    risk_metrics = risk_calculator.calculate_all_metrics(coins)
    risk_metrics_file = "risk_metrics.json"
    risk_calculator.save_to_json(risk_metrics, risk_metrics_file)
    print(f"✅ Risk metrics saved: {risk_metrics_file}")

    # Generate Detailed Risk Analyzer Dashboards
    print("📊 Creating detailed analyzers...")
    for coin_name, symbol in coins.items():
        analyzer_file = f"{coin_name.lower()}_risk_analyzer.html"
        try:
            detailed_analyzer.create_dashboard(symbol, coin_name, analyzer_file)
            print(f"  ✅ {coin_name}: {analyzer_file}")
        except Exception as e:
            print(f"  ⚠ {coin_name} error: {e}")

    print("\n" + "=" * 70)
    print(f"✅ UPDATE COMPLETE - Dubai {datetime.now(dubai_tz).strftime('%H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    main()
