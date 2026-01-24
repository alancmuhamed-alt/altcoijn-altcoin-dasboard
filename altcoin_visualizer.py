import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class AltcoinRatioVisualizer:
    def __init__(self):
        """Visualizer for Altcoin Ratio analysis."""
        pass

    def create_altcoin_ratio_chart(self, btc_df, ratio_df, support_levels=None,
                                     resistance_levels=None, bsl_ssl=None,
                                     output_file='altcoin_ratio.html'):
        """
        Create Pine Script style chart:
        - BTC candlesticks (gray/transparent)
        - Altcoin Ratio candlesticks (yellow overlay)
        - SMA 50 (orange)
        - EMA 21 (blue) + SMA 20 (green) with fill
        - Auto S/R levels
        - BSL/SSL lines
        - Info table

        Args:
            btc_df: BTC OHLCV data
            ratio_df: Altcoin ratio data with indicators
            support_levels: Support levels DataFrame
            resistance_levels: Resistance levels DataFrame
            bsl_ssl: Dict with BSL and SSL values
            output_file: Output HTML filename
        """
        fig = go.Figure()

        # 1. BTC Candlesticks (background, muted colors)
        fig.add_trace(
            go.Candlestick(
                x=btc_df['datetime'],
                open=btc_df['open'],
                high=btc_df['high'],
                low=btc_df['low'],
                close=btc_df['close'],
                name='BTC/USDT',
                increasing_line_color='rgba(150, 150, 150, 0.3)',
                decreasing_line_color='rgba(100, 100, 100, 0.3)',
                increasing_fillcolor='rgba(150, 150, 150, 0.2)',
                decreasing_fillcolor='rgba(100, 100, 100, 0.2)',
                showlegend=True
            )
        )

        # 2. Altcoin Ratio Candlesticks (yellow overlay)
        fig.add_trace(
            go.Candlestick(
                x=ratio_df['datetime'],
                open=ratio_df['ar_open'],
                high=ratio_df['ar_high'],
                low=ratio_df['ar_low'],
                close=ratio_df['ar_close'],
                name='Alt Ratio [15M]',
                increasing_line_color='rgba(255, 204, 0, 0.6)',
                decreasing_line_color='rgba(255, 204, 0, 0.8)',
                increasing_fillcolor='rgba(255, 204, 0, 0.4)',
                decreasing_fillcolor='rgba(255, 204, 0, 0.6)',
                showlegend=True
            )
        )

        # 3. SMA 50 (orange)
        fig.add_trace(
            go.Scatter(
                x=ratio_df['datetime'],
                y=ratio_df['sma50'],
                name='SMA 50',
                line=dict(color='orange', width=2),
                showlegend=True
            )
        )

        # 4. EMA 21 (blue)
        fig.add_trace(
            go.Scatter(
                x=ratio_df['datetime'],
                y=ratio_df['ema21'],
                name='EMA 21',
                line=dict(color='blue', width=2),
                showlegend=True,
                fill=None
            )
        )

        # 5. SMA 20 (green) with fill to EMA 21
        fig.add_trace(
            go.Scatter(
                x=ratio_df['datetime'],
                y=ratio_df['sma20'],
                name='SMA 20',
                line=dict(color='green', width=2),
                fill='tonexty',
                fillcolor='rgba(0, 255, 255, 0.15)',
                showlegend=True
            )
        )

        # 6. Support Levels (green lines)
        if support_levels is not None and len(support_levels) > 0:
            for idx, level in support_levels.iterrows():
                fig.add_hline(
                    y=level['price'],
                    line_dash="solid",
                    line_color="lime",
                    line_width=2,
                    annotation_text=f"S{idx+1}",
                    annotation_position="right"
                )

        # 7. Resistance Levels (red lines)
        if resistance_levels is not None and len(resistance_levels) > 0:
            for idx, level in resistance_levels.iterrows():
                fig.add_hline(
                    y=level['price'],
                    line_dash="solid",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"R{idx+1}",
                    annotation_position="right"
                )

        # 8. BSL (Buy-Side Liquidity - green)
        if bsl_ssl and 'bsl' in bsl_ssl and bsl_ssl['bsl'] is not None:
            fig.add_hline(
                y=bsl_ssl['bsl'],
                line_dash="dash",
                line_color="green",
                line_width=2,
                annotation_text="BSL",
                annotation_position="left"
            )

        # 9. SSL (Sell-Side Liquidity - red)
        if bsl_ssl and 'ssl' in bsl_ssl and bsl_ssl['ssl'] is not None:
            fig.add_hline(
                y=bsl_ssl['ssl'],
                line_dash="dash",
                line_color="red",
                line_width=2,
                annotation_text="SSL",
                annotation_position="left"
            )

        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Altcoin Ratio [15M] + BSL/SSL + Auto S/R</b>',
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            hovermode='x unified',
            template='plotly_dark',
            width=2400,
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="Price")

        # Save HTML with interactive config
        config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'altcoin_ratio',
                'height': 800,
                'width': 2400,
                'scale': 1
            }
        }
        fig.write_html(output_file, config=config)
        print(f"\n✓ Altcoin Ratio chart saved to: {output_file}")

        return output_file

    def create_sr_table_text(self, support_levels, resistance_levels):
        """Create S/R table summary for display."""
        text = "\n" + "="*50
        text += "\n  SUPPORT & RESISTANCE LEVELS"
        text += "\n" + "="*50

        text += "\n\n  RESISTANCES:"
        if resistance_levels is not None and len(resistance_levels) > 0:
            for idx, level in resistance_levels.iterrows():
                # Pine Script metodu: count yok, sadece price var
                text += f"\n    R{idx+1}: ${level['price']:,.2f}"
        else:
            text += "\n    None found"

        text += "\n\n  SUPPORTS:"
        if support_levels is not None and len(support_levels) > 0:
            for idx, level in support_levels.iterrows():
                # Pine Script metodu: count yok, sadece price var
                text += f"\n    S{idx+1}: ${level['price']:,.2f}"
        else:
            text += "\n    None found"

        text += "\n" + "="*50
        return text

    def add_footprint_markers(self, fig, footprint_df):
        """Add footprint markers to chart (aggressive buy/sell/trap)."""
        if footprint_df is None or len(footprint_df) == 0:
            return fig

        # Aggressive buyers (green circles at bottom)
        aggressive_buys = footprint_df[footprint_df['is_aggressive_buy']]
        if len(aggressive_buys) > 0:
            fig.add_trace(
                go.Scatter(
                    x=aggressive_buys['datetime'],
                    y=aggressive_buys['low'],
                    mode='markers',
                    name='Aggressive Buy',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color='lime',
                        line=dict(color='darkgreen', width=1)
                    ),
                    hovertemplate='<b>Aggressive Buy</b><br>Price: %{y:.2f}<extra></extra>'
                )
            )

        # Aggressive sellers (red circles at top)
        aggressive_sells = footprint_df[footprint_df['is_aggressive_sell']]
        if len(aggressive_sells) > 0:
            fig.add_trace(
                go.Scatter(
                    x=aggressive_sells['datetime'],
                    y=aggressive_sells['high'],
                    mode='markers',
                    name='Aggressive Sell',
                    marker=dict(
                        symbol='circle',
                        size=8,
                        color='red',
                        line=dict(color='darkred', width=1)
                    ),
                    hovertemplate='<b>Aggressive Sell</b><br>Price: %{y:.2f}<extra></extra>'
                )
            )

        # Trap zones (yellow rectangles)
        traps = footprint_df[footprint_df['is_trap']]
        for idx, trap in traps.iterrows():
            fig.add_shape(
                type="rect",
                x0=trap['datetime'] - pd.Timedelta(minutes=7.5),
                x1=trap['datetime'] + pd.Timedelta(minutes=7.5),
                y0=trap['low'],
                y1=trap['high'],
                fillcolor='rgba(255, 255, 0, 0.3)',
                line=dict(color='yellow', width=2)
            )

            # Warning label
            fig.add_annotation(
                x=trap['datetime'],
                y=trap['high'],
                text="⚠",
                showarrow=False,
                font=dict(size=16, color='yellow'),
                bgcolor='rgba(0, 0, 0, 0.5)'
            )

        return fig

    def add_order_flow_profile(self, fig, profile_df, current_time, profile_scale=20, offset=5):
        """Add order flow profile bars to the right side of chart."""
        if profile_df is None or len(profile_df) == 0:
            return fig

        max_vol = max(profile_df['buy_volume'].max(), profile_df['sell_volume'].max())

        if max_vol == 0:
            return fig

        time_offset = pd.Timedelta(minutes=offset * 15)  # 15m timeframe

        # Buy volume bars (green)
        for idx, row in profile_df.iterrows():
            if row['buy_volume'] > 0:
                width = (row['buy_volume'] / max_vol) * profile_scale
                bar_start = current_time + time_offset
                bar_end = bar_start + pd.Timedelta(minutes=width * 15)

                fig.add_shape(
                    type="rect",
                    x0=bar_start,
                    x1=bar_end,
                    y0=row['price_bottom'],
                    y1=row['price_top'],
                    fillcolor='rgba(0, 255, 187, 0.7)',
                    line=dict(width=1, color='rgba(0, 255, 187, 0.7)')
                )

        # Sell volume bars (red, offset to the right)
        sell_offset = time_offset + pd.Timedelta(minutes=(profile_scale + 2) * 15)

        for idx, row in profile_df.iterrows():
            if row['sell_volume'] > 0:
                width = (row['sell_volume'] / max_vol) * profile_scale
                bar_start = current_time + sell_offset
                bar_end = bar_start + pd.Timedelta(minutes=width * 15)

                fig.add_shape(
                    type="rect",
                    x0=bar_start,
                    x1=bar_end,
                    y0=row['price_bottom'],
                    y1=row['price_top'],
                    fillcolor='rgba(255, 17, 0, 0.7)',
                    line=dict(width=1, color='rgba(255, 17, 0, 0.7)')
                )

        return fig

    def create_orderbook_depth_chart(self, orderbook_data, output_file='orderbook_depth.html'):
        """
        Create real-time order book depth chart.

        Args:
            orderbook_data: Order book snapshot with bids and asks
            output_file: Output HTML filename
        """
        if not orderbook_data:
            print("⚠ No order book data available")
            return None

        bids = orderbook_data['bids']  # [[price, qty], ...]
        asks = orderbook_data['asks']

        # Calculate cumulative volumes
        bid_prices = [price for price, _ in bids]
        bid_volumes = [qty for _, qty in bids]
        bid_cumulative = []
        cumsum = 0
        for vol in bid_volumes:
            cumsum += vol
            bid_cumulative.append(cumsum)

        ask_prices = [price for price, _ in asks]
        ask_volumes = [qty for _, qty in asks]
        ask_cumulative = []
        cumsum = 0
        for vol in ask_volumes:
            cumsum += vol
            ask_cumulative.append(cumsum)

        # Create figure
        fig = go.Figure()

        # Bid side (green, left)
        fig.add_trace(
            go.Scatter(
                x=bid_prices,
                y=bid_cumulative,
                name='Bid Depth',
                fill='tozeroy',
                fillcolor='rgba(0, 255, 0, 0.3)',
                line=dict(color='green', width=2),
                hovertemplate='<b>Bid</b><br>Price: $%{x:.2f}<br>Cumulative: %{y:.2f}<extra></extra>'
            )
        )

        # Ask side (red, right)
        fig.add_trace(
            go.Scatter(
                x=ask_prices,
                y=ask_cumulative,
                name='Ask Depth',
                fill='tozeroy',
                fillcolor='rgba(255, 0, 0, 0.3)',
                line=dict(color='red', width=2),
                hovertemplate='<b>Ask</b><br>Price: $%{x:.2f}<br>Cumulative: %{y:.2f}<extra></extra>'
            )
        )

        # Mark best bid/ask
        if bids:
            fig.add_vline(x=bids[0][0], line_dash="dash", line_color="green",
                         annotation_text="Best Bid", annotation_position="top")

        if asks:
            fig.add_vline(x=asks[0][0], line_dash="dash", line_color="red",
                         annotation_text="Best Ask", annotation_position="top")

        # Calculate stats for title
        bid_volume = sum(qty for _, qty in bids)
        ask_volume = sum(qty for _, qty in asks)
        imbalance = bid_volume / ask_volume if ask_volume > 0 else 0
        spread = asks[0][0] - bids[0][0] if asks and bids else 0

        fig.update_layout(
            title=dict(
                text=f'<b>Real-Time Order Book Depth - {orderbook_data["symbol"]}</b><br>' +
                     f'<sub>Spread: ${spread:.2f} | Bid/Ask Ratio: {imbalance:.2f}</sub>',
                x=0.5,
                xanchor='center',
                font=dict(size=18)
            ),
            xaxis_title='Price (USD)',
            yaxis_title='Cumulative Volume',
            template='plotly_dark',
            height=600,
            showlegend=True,
            hovermode='x unified'
        )

        config = {
            'displayModeBar': True,
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'orderbook_depth',
                'height': 600,
                'width': 1200,
                'scale': 1
            }
        }
        fig.write_html(output_file, config=config)
        print(f"\n✓ Order book depth chart saved to: {output_file}")

        return output_file

    def add_orderbook_overlay(self, fig, orderbook_stats, y_position='bottom'):
        """
        Add order book statistics overlay to existing chart.

        Args:
            fig: Plotly figure object
            orderbook_stats: Order book statistics dict
            y_position: Position of overlay ('top' or 'bottom')
        """
        if not orderbook_stats:
            return fig

        # Create annotation with order book stats
        stats_text = (
            f"<b>Order Book (Live)</b><br>"
            f"Spread: ${orderbook_stats['spread']:.2f} ({orderbook_stats['spread_pct']:.3f}%)<br>"
            f"Bid Vol: {orderbook_stats['bid_volume']:.2f}<br>"
            f"Ask Vol: {orderbook_stats['ask_volume']:.2f}<br>"
            f"Ratio: {orderbook_stats['volume_ratio']:.2f}<br>"
            f"<b>Imbalance: {orderbook_stats['imbalance']}</b>"
        )

        y_pos = 0.02 if y_position == 'bottom' else 0.98
        y_anchor = 'bottom' if y_position == 'bottom' else 'top'

        fig.add_annotation(
            text=stats_text,
            xref='paper',
            yref='paper',
            x=0.02,
            y=y_pos,
            xanchor='left',
            yanchor=y_anchor,
            showarrow=False,
            bgcolor='rgba(0, 0, 0, 0.7)',
            bordercolor='yellow',
            borderwidth=2,
            font=dict(size=12, color='white')
        )

        return fig

    def create_combined_chart(self, btc_df, ratio_df, orderbook_data,
                               support_levels=None, resistance_levels=None,
                               bsl_ssl=None, footprint_df=None,
                               orderbook_candles=50,
                               output_file='altcoin_combined.html'):
        """
        Create combined multi-panel chart:
        - Top panel: Altcoin Ratio with all indicators
        - Bottom panel: Real-time Order Book Depth

        Args:
            btc_df: BTC OHLCV data
            ratio_df: Altcoin ratio data with indicators
            orderbook_data: Current order book snapshot
            support_levels: Support levels DataFrame
            resistance_levels: Resistance levels DataFrame
            bsl_ssl: Dict with BSL and SSL values
            footprint_df: Footprint analysis data
            orderbook_candles: Number of recent candles to show for order book reference
            output_file: Output HTML filename
        """
        from plotly.subplots import make_subplots

        # Create subplots: 2 rows, 1 column
        # Top panel (70% height): Main chart
        # Bottom panel (30% height): Order book depth
        # SHARED X-AXIS = Alt paneller birlikte hareket eder
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.70, 0.30],
            vertical_spacing=0.05,
            subplot_titles=('<b>Altcoin Ratio [15M] + All Indicators</b>',
                           '<b>Real-Time Order Book Depth</b>'),
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}]],
            shared_xaxes=False  # Order Book farkli x-axis (price) kullaniyor
        )

        # ========== TOP PANEL: MAIN CHART ==========

        # 1. BTC Candlesticks (background)
        fig.add_trace(
            go.Candlestick(
                x=btc_df['datetime'],
                open=btc_df['open'],
                high=btc_df['high'],
                low=btc_df['low'],
                close=btc_df['close'],
                name='BTC/USDT',
                increasing_line_color='rgba(150, 150, 150, 0.3)',
                decreasing_line_color='rgba(100, 100, 100, 0.3)',
                increasing_fillcolor='rgba(150, 150, 150, 0.2)',
                decreasing_fillcolor='rgba(100, 100, 100, 0.2)',
                showlegend=True
            ),
            row=1, col=1
        )

        # 2. Altcoin Ratio Candlesticks
        import numpy as np

        fig.add_trace(
            go.Candlestick(
                x=ratio_df['datetime'],
                open=ratio_df['ar_open'],
                high=ratio_df['ar_high'],
                low=ratio_df['ar_low'],
                close=ratio_df['ar_close'],
                name='Alt Ratio [15M]',
                increasing_line_color='rgba(255, 204, 0, 0.6)',
                decreasing_line_color='rgba(255, 204, 0, 0.8)',
                increasing_fillcolor='rgba(255, 204, 0, 0.4)',
                decreasing_fillcolor='rgba(255, 204, 0, 0.6)',
                showlegend=True,
                hoverinfo='skip'  # Hover'ı kapat, aşağıdaki scatter gösterecek
            ),
            row=1, col=1
        )

        # 2b. Invisible Scatter for detailed hover info
        hover_data = np.column_stack((
            ratio_df['sma20'].fillna(0),
            ratio_df['ema21'].fillna(0),
            ratio_df['sma50'].fillna(0),
            ratio_df['ar_open'],
            ratio_df['ar_high'],
            ratio_df['ar_low'],
            ratio_df['ar_close']
        ))

        fig.add_trace(
            go.Scatter(
                x=ratio_df['datetime'],
                y=ratio_df['ar_close'],
                mode='markers',
                marker=dict(size=0.1, opacity=0),  # Invisible
                name='',
                showlegend=False,
                customdata=hover_data,
                hovertemplate='<b>%{x}</b><br><br>' +
                              '<b>SMA 20</b><br>%{customdata[0]:,.3f}<br><br>' +
                              '<b>EMA 21</b><br>%{customdata[1]:,.3f}<br><br>' +
                              '<b>SMA 50</b><br>%{customdata[2]:,.3f}<br><br>' +
                              '<b>Alt Ratio [15M]</b><br>' +
                              'Open: %{customdata[3]:,.2f}<br>' +
                              'High: %{customdata[4]:,.2f}<br>' +
                              'Low: %{customdata[5]:,.2f}<br>' +
                              'Close: %{customdata[6]:,.2f}<br><br>' +
                              '<b>Indicators:</b><br>' +
                              'SMA 20: %{customdata[0]:,.3f}<br>' +
                              'EMA 21: %{customdata[1]:,.3f}<br>' +
                              'SMA 50: %{customdata[2]:,.3f}' +
                              '<extra></extra>'
            ),
            row=1, col=1
        )

        # 3. SMA 50 (orange)
        fig.add_trace(
            go.Scatter(
                x=ratio_df['datetime'],
                y=ratio_df['sma50'],
                name='SMA 50',
                line=dict(color='orange', width=2),
                showlegend=True
            ),
            row=1, col=1
        )

        # 4. EMA 21 (blue)
        fig.add_trace(
            go.Scatter(
                x=ratio_df['datetime'],
                y=ratio_df['ema21'],
                name='EMA 21',
                line=dict(color='blue', width=2),
                showlegend=True,
                fill=None
            ),
            row=1, col=1
        )

        # 5. SMA 20 (green) with fill
        fig.add_trace(
            go.Scatter(
                x=ratio_df['datetime'],
                y=ratio_df['sma20'],
                name='SMA 20',
                line=dict(color='green', width=2),
                fill='tonexty',
                fillcolor='rgba(0, 255, 255, 0.15)',
                showlegend=True
            ),
            row=1, col=1
        )

        # 6. Support Levels
        if support_levels is not None and len(support_levels) > 0:
            for idx, level in support_levels.iterrows():
                fig.add_hline(
                    y=level['price'],
                    line_dash="solid",
                    line_color="lime",
                    line_width=2,
                    annotation_text=f"S{idx+1}",
                    annotation_position="right",
                    row=1, col=1
                )

        # 7. Resistance Levels
        if resistance_levels is not None and len(resistance_levels) > 0:
            for idx, level in resistance_levels.iterrows():
                fig.add_hline(
                    y=level['price'],
                    line_dash="solid",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"R{idx+1}",
                    annotation_position="right",
                    row=1, col=1
                )

        # 8. BSL (Buy-Side Liquidity)
        if bsl_ssl and 'bsl' in bsl_ssl and bsl_ssl['bsl'] is not None:
            fig.add_hline(
                y=bsl_ssl['bsl'],
                line_dash="dash",
                line_color="green",
                line_width=2,
                annotation_text="BSL",
                annotation_position="left",
                row=1, col=1
            )

        # 9. SSL (Sell-Side Liquidity)
        if bsl_ssl and 'ssl' in bsl_ssl and bsl_ssl['ssl'] is not None:
            fig.add_hline(
                y=bsl_ssl['ssl'],
                line_dash="dash",
                line_color="red",
                line_width=2,
                annotation_text="SSL",
                annotation_position="left",
                row=1, col=1
            )

        # 10. Footprint markers
        if footprint_df is not None and len(footprint_df) > 0:
            # Aggressive buyers
            aggressive_buys = footprint_df[footprint_df['is_aggressive_buy']]
            if len(aggressive_buys) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=aggressive_buys['datetime'],
                        y=aggressive_buys['low'],
                        mode='markers',
                        name='Aggressive Buy',
                        marker=dict(symbol='circle', size=8, color='lime',
                                   line=dict(color='darkgreen', width=1)),
                        hovertemplate='<b>Aggressive Buy</b><br>Price: %{y:.2f}<extra></extra>'
                    ),
                    row=1, col=1
                )

            # Aggressive sellers
            aggressive_sells = footprint_df[footprint_df['is_aggressive_sell']]
            if len(aggressive_sells) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=aggressive_sells['datetime'],
                        y=aggressive_sells['high'],
                        mode='markers',
                        name='Aggressive Sell',
                        marker=dict(symbol='circle', size=8, color='red',
                                   line=dict(color='darkred', width=1)),
                        hovertemplate='<b>Aggressive Sell</b><br>Price: %{y:.2f}<extra></extra>'
                    ),
                    row=1, col=1
                )

        # ========== BOTTOM PANEL: ORDER BOOK DEPTH (ESKİ HALİ) ==========

        if orderbook_data:
            bids = orderbook_data['bids']
            asks = orderbook_data['asks']

            # Calculate cumulative volumes
            bid_prices = [price for price, _ in bids]
            bid_volumes = [qty for _, qty in bids]
            bid_cumulative = []
            cumsum = 0
            for vol in bid_volumes:
                cumsum += vol
                bid_cumulative.append(cumsum)

            ask_prices = [price for price, _ in asks]
            ask_volumes = [qty for _, qty in asks]
            ask_cumulative = []
            cumsum = 0
            for vol in ask_volumes:
                cumsum += vol
                ask_cumulative.append(cumsum)

            # Bid side (green area)
            fig.add_trace(
                go.Scatter(
                    x=bid_prices,
                    y=bid_cumulative,
                    name='Bid Depth',
                    fill='tozeroy',
                    fillcolor='rgba(0, 255, 0, 0.3)',
                    line=dict(color='green', width=2),
                    hovertemplate='<b>Bid</b><br>Price: $%{x:.2f}<br>Cumulative: %{y:.2f}<extra></extra>'
                ),
                row=2, col=1
            )

            # Ask side (red area)
            fig.add_trace(
                go.Scatter(
                    x=ask_prices,
                    y=ask_cumulative,
                    name='Ask Depth',
                    fill='tozeroy',
                    fillcolor='rgba(255, 0, 0, 0.3)',
                    line=dict(color='red', width=2),
                    hovertemplate='<b>Ask</b><br>Price: $%{x:.2f}<br>Cumulative: %{y:.2f}<extra></extra>'
                ),
                row=2, col=1
            )

            # Mark best bid/ask
            if bids:
                fig.add_vline(x=bids[0][0], line_dash="dash", line_color="green",
                             annotation_text="Best Bid", annotation_position="top",
                             row=2, col=1)

            if asks:
                fig.add_vline(x=asks[0][0], line_dash="dash", line_color="red",
                             annotation_text="Best Ask", annotation_position="top",
                             row=2, col=1)

            # Calculate stats
            bid_volume = sum(qty for _, qty in bids)
            ask_volume = sum(qty for _, qty in asks)
            imbalance = bid_volume / ask_volume if ask_volume > 0 else 0
            spread = asks[0][0] - bids[0][0] if asks and bids else 0

            # Add stats annotation
            stats_text = (
                f"Spread: ${spread:.2f} | "
                f"Bid/Ask Ratio: {imbalance:.2f} | "
                f"Symbol: {orderbook_data['symbol']}"
            )

            fig.add_annotation(
                text=stats_text,
                xref='paper',
                yref='paper',
                x=0.5,
                y=0.28,
                xanchor='center',
                yanchor='top',
                showarrow=False,
                bgcolor='rgba(0, 0, 0, 0.7)',
                bordercolor='yellow',
                borderwidth=2,
                font=dict(size=12, color='white')
            )

        # Add timestamp to title
        from datetime import datetime
        import pytz
        dubai_tz = pytz.timezone('Asia/Dubai')
        current_time = datetime.now(dubai_tz).strftime('%H:%M:%S')

        # Update layout - NATIVE ZOOM ALLOWED
        fig.update_layout(
            title=dict(
                text=f'<b>Altcoin Terminal</b><br><sub style="color:#888">Last Update: Dubai {current_time}</sub>',
                x=0.5,
                xanchor='center',
                font=dict(size=16)
            ),
            hovermode='closest',
            template='plotly_dark',
            autosize=True,
            height=None,
            showlegend=True,
            dragmode=False,  # Plotly drag KAPALI - native kullan
            xaxis_rangeslider_visible=False,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="center",
                x=0.5,
                font=dict(size=9)
            ),
            margin=dict(l=30, r=10, t=60, b=30),
            font=dict(size=10),
            hoverlabel=dict(font_size=10)
        )

        # Update axes
        fig.update_xaxes(
            title_text="Time",
            row=1, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        fig.update_yaxes(
            title_text="Price",
            row=1, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        fig.update_xaxes(
            title_text="Price (USD)",
            row=2, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        fig.update_yaxes(
            title_text="Cumulative Volume",
            row=2, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )

        # INTERACTIVE CHART - Zoom ve pan aktif
        config = {
            'displayModeBar': True,
            'displaylogo': False,
            'scrollZoom': True,  # Mouse wheel zoom AÇIK
            'doubleClick': 'reset',  # Çift tık sıfırlar
            'responsive': True,
            'staticPlot': False,
            'editable': False,
            'showTips': True,
            'modeBarButtonsToAdd': ['pan2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 'resetScale2d'],
        }

        # Direkt Plotly HTML - wrapper yok, tam interaktif
        fig.write_html(output_file, config=config, include_plotlyjs='cdn')

        print(f"\n✓ Combined dashboard saved to: {output_file}")

        return output_file
