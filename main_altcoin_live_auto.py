#!/usr/bin/env python3
"""
CANLI TERMINAL - Arka planda sürekli çalışır (input gerektirmez)
"""
import sys
import time
from datetime import datetime
import pytz
from altcoin_ratio import AltcoinRatioCalculator
from altcoin_visualizer import AltcoinRatioVisualizer
from liquidity_levels import LiquidityAnalyzer

# Force unbuffered output
sys.stdout = open(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', buffering=1)


def main():
    # Sabit ayarlar (input yok)
    overlay_symbol = 'ETH/USDT'
    overlay_name = 'ETH'
    timeframe = "15m"
    days = 10
    orderbook_candles = 100
    update_interval = 900  # 15 dakika (900 saniye)

    print("=" * 70)
    print("  CANLI ALTCOIN TERMINAL - OTOMATIK MOD")
    print("=" * 70)
    print(f"\n✓ {days} günlük veri")
    print(f"✓ Son {orderbook_candles} mum")
    print(f"✓ Her {update_interval} saniyede güncelleniyor")
    print(f"✓ Ctrl+C ile durdur\n")

    # Initialize
    calculator = AltcoinRatioCalculator()
    visualizer = AltcoinRatioVisualizer()
    liquidity = LiquidityAnalyzer()

    from websocket_stream import BinanceWebSocketStream, BinanceOrderBookStream

    ws_symbol = overlay_symbol.replace('/', '').lower()

    # Start streams
    candle_stream = BinanceWebSocketStream(ws_symbol)
    orderbook_stream = BinanceOrderBookStream(ws_symbol, depth_level=20)

    print("🔴 Starting WebSocket streams...")
    candle_stream.start()
    orderbook_stream.start()

    if not candle_stream.wait_for_candle(timeout=10):
        print("✗ No candle data")
        sys.exit(1)

    if not orderbook_stream.wait_for_orderbook(timeout=10):
        print("✗ No order book data")
        sys.exit(1)

    print("✓ Streams active!\n")

    output_file = "/Users/muhamedalanc/altcoin_combined_eth_live.html"
    update_count = 0
    dubai_tz = pytz.timezone('Asia/Dubai')

    # İLK SEFERDA historical data çek
    print("\n📥 Fetching initial historical data...")
    initial_df = calculator.fetch_overlay_price(overlay_symbol, timeframe, days=days)
    if initial_df is None:
        print("✗ Could not fetch initial data")
        sys.exit(1)
    print(f"✓ Initial data: {len(initial_df)} candles")

    try:
        while True:
            update_count += 1
            dubai_time = datetime.now(dubai_tz).strftime('%H:%M:%S')
            print(f"\n{'='*70}")
            print(f"  UPDATE #{update_count} - Dubai: {dubai_time}")
            print(f"{'='*70}")

            # Fetch fresh market data
            market_data = calculator.fetch_market_caps()
            if not market_data:
                print("⚠ Market data fetch failed, using old data")
                time.sleep(update_interval)
                continue

            # Get LIVE candle data from WebSocket (eğer varsa)
            ws_df = candle_stream.get_dataframe(limit=days * 96)

            if ws_df is not None and len(ws_df) > 0:
                # WebSocket data var - CANLI VERİ
                overlay_df = ws_df
                print(f"🔴 LIVE WebSocket: {len(overlay_df)} candles (son: {overlay_df['datetime'].iloc[-1]})")
            else:
                # WebSocket henüz hazır değil - historical data kullan
                overlay_df = calculator.fetch_overlay_price(overlay_symbol, timeframe, days=days)
                if overlay_df is None:
                    print("⚠ Candle data fetch failed")
                    time.sleep(update_interval)
                    continue
                print(f"📊 Historical: {len(overlay_df)} candles")

            # Calculate ratio
            ratio_df = calculator.calculate_synthetic_altcoin_ratio(overlay_df, market_data, overlay_name)
            ratio_df = calculator.calculate_indicators(ratio_df)

            # Get order book
            orderbook_stats = orderbook_stream.get_orderbook_stats()
            orderbook_data = orderbook_stream.get_current_orderbook()

            if orderbook_stats:
                print(f"📊 Spread: ${orderbook_stats['spread']:.2f} | "
                      f"Bid/Ask: {orderbook_stats['volume_ratio']:.2f} | "
                      f"{orderbook_stats['imbalance']}")

            # Calculate S/R
            sr_result = calculator.find_auto_sr_levels_pinescript(
                ratio_df, left_right=3, tolerance=30.0,
                max_supports=4, max_resistances=4
            )

            # BSL/SSL
            ratio_ohlc = ratio_df[['datetime', 'ar_open', 'ar_high', 'ar_low', 'ar_close']].copy()
            ratio_ohlc.columns = ['datetime', 'open', 'high', 'low', 'close']
            swings = liquidity.find_swing_highs_lows(ratio_ohlc, swing_length=10)

            bsl = swings['swing_highs']['price'].iloc[-1] if len(swings['swing_highs']) > 0 else None
            ssl = swings['swing_lows']['price'].iloc[-1] if len(swings['swing_lows']) > 0 else None

            # Footprint
            footprint_df = calculator.calculate_footprint(ratio_df, lookback=50)

            # Create chart - YENİ VERİYLE
            print(f"📝 Regenerating HTML: {output_file}")
            visualizer.create_combined_chart(
                btc_df=overlay_df,
                ratio_df=ratio_df,
                orderbook_data=orderbook_data,
                support_levels=sr_result['supports'],
                resistance_levels=sr_result['resistances'],
                bsl_ssl={'bsl': bsl, 'ssl': ssl},
                footprint_df=footprint_df,
                orderbook_candles=orderbook_candles,
                output_file=output_file
            )

            dubai_time_now = datetime.now(dubai_tz).strftime('%H:%M:%S')
            print(f"✓ Dashboard güncellendi: Dubai {dubai_time_now}")
            print(f"✓ HTML file yazıldı: {output_file}")

            # AUTO-PUSH TO GITHUB
            import subprocess
            git_repo = "/Users/muhamedalanc/altcoin-dashboard"
            try:
                print(f"🔄 Pushing to GitHub...")
                subprocess.run(f"cp {output_file} {git_repo}/", shell=True, check=True)
                subprocess.run(f"cd {git_repo} && git add altcoin_combined_eth_live.html", shell=True, check=True)
                commit_msg = f"Auto-update dashboard - Dubai {dubai_time_now}"
                subprocess.run(f'cd {git_repo} && git commit -m "{commit_msg}" && git push', shell=True, check=True)
                print(f"✓ GitHub güncellendi: {dubai_time_now}")
            except Exception as e:
                print(f"⚠ GitHub push failed: {e}")

            print(f"⏳ Sonraki güncelleme {update_interval} saniye sonra...")

            time.sleep(update_interval)

    except KeyboardInterrupt:
        print("\n\n⚠ Terminal durduruldu!")
        if orderbook_stream:
            orderbook_stream.stop()
        print("✓ Order Book stream kapatıldı")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        if orderbook_stream:
            orderbook_stream.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
