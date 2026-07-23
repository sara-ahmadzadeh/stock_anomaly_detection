# dashboard.py
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import time

class AnomalyDashboard:
    def __init__(self, streamer, detector):
        self.app = dash.Dash(__name__)
        self.streamer = streamer
        self.detector = detector
        self.anomaly_log = []
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Create professional dashboard layout."""
        self.app.layout = html.Div([
            html.H1(f"📈 {self.streamer.market_type} Anomaly Detection System",
                    style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
            
            # Stats row
            html.Div([
                html.Div([
                    html.H3("Assets Monitored"),
                    html.H2(id='stock-count', children=str(len(self.streamer.symbols)))
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Anomalies Detected"),
                    html.H2(id='anomaly-count', children="0", style={'color': '#e74c3c'})
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Data Source"),
                    html.H2(id='data-source', children=self.streamer.source_name,
                           style={'color': '#27ae60', 'fontSize': '18px'})
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Last Update"),
                    html.H2(id='last-update', children="--:--:--")
                ], className='stat-box'),
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': 30}),
            
            # Alert section
            html.Div([
                html.H3("🚨 Recent Anomalies", style={'color': '#e74c3c'}),
                html.Div(id='anomaly-alerts', children=[
                    html.P("No anomalies detected yet. System is monitoring...",
                           style={'color': '#7f8c8d', 'fontStyle': 'italic'})
                ], style={'maxHeight': 200, 'overflowY': 'auto', 
                          'backgroundColor': '#2c3e50', 'padding': 15, 
                          'borderRadius': 5, 'marginBottom': 20})
            ]),
            
            # Charts
            html.Div([
                html.Label("Select Asset:", style={'fontWeight': 'bold', 'marginRight': 10, 'color': 'white'}),
                dcc.Dropdown(
                    id='stock-selector',
                    options=[{'label': s, 'value': s} for s in self.streamer.symbols],
                    value=self.streamer.symbols[0],
                    style={'width': '30%', 'marginBottom': 20, 'color': 'black'}
                ),
                
                dcc.Graph(id='live-price-chart'),
                dcc.Graph(id='zscore-chart'),
            ]),
            
            dcc.Interval(
                id='interval-component',
                interval=30*1000,
                n_intervals=0
            )
        ], style={'padding': 20, 'backgroundColor': '#1a1a2e', 'color': 'white', 
                   'minHeight': '100vh', 'fontFamily': 'Arial'})
    
    def setup_callbacks(self):
        """Setup dashboard callbacks."""
        
        @self.app.callback(
            [Output('live-price-chart', 'figure'),
             Output('zscore-chart', 'figure'),
             Output('anomaly-alerts', 'children'),
             Output('anomaly-count', 'children'),
             Output('last-update', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('stock-selector', 'value')]
        )
        def update_dashboard(n, selected_symbol):
            """Update all dashboard components."""
            try:
                price_fig = self._create_price_chart(selected_symbol)
                zscore_fig = self._create_zscore_chart(selected_symbol)
                alerts = self._create_alerts_display()
                anomaly_count = str(len(self.anomaly_log))
                current_time_str = datetime.now().strftime('%H:%M:%S')
                
                return price_fig, zscore_fig, alerts, anomaly_count, current_time_str
                
            except Exception as e:
                print(f"Dashboard error: {e}")
                empty_fig = self._create_empty_chart("Loading...")
                return empty_fig, empty_fig, [
                    html.P("Loading data...", style={'color': '#f39c12'})
                ], str(len(self.anomaly_log)), datetime.now().strftime('%H:%M:%S')
    
    def _create_price_chart(self, symbol):
        """Create professional price chart with volume."""
        try:
            if symbol not in self.detector.history or len(self.detector.history[symbol]) < 2:
                count = len(self.detector.history.get(symbol, []))
                return self._create_empty_chart(f"Collecting {symbol} data... ({count}/30 checks)")
            
            prices = self.detector.history[symbol]
            
            # Create synthetic OHLC from price history for candlestick effect
            df = pd.DataFrame({'close': prices})
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df[['open', 'close']].max(axis=1) * 1.001  # Slight variation
            df['low'] = df[['open', 'close']].min(axis=1) * 0.999
            
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.7, 0.3],
                subplot_titles=(f'{symbol} Price Action', 'Volume / Activity')
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=list(range(len(df))),
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price',
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                ),
                row=1, col=1
            )
            
            # Add moving average
            if len(prices) >= 5:
                ma = pd.Series(prices).rolling(window=5).mean()
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(ma))),
                        y=ma,
                        name='5-period MA',
                        line=dict(color='#ffa726', width=1.5)
                    ),
                    row=1, col=1
                )
            
            # Volume bars (using price changes as pseudo-volume)
            volume_data = [abs(prices[i] - prices[i-1]) / prices[i-1] * 100 if i > 0 else 0 
                          for i in range(len(prices))]
            colors = ['#ef5350' if i > 0 and prices[i] < prices[i-1] else '#26a69a' 
                     for i in range(len(prices))]
            
            fig.add_trace(
                go.Bar(
                    x=list(range(len(volume_data))),
                    y=volume_data,
                    name='Price Change %',
                    marker_color=colors,
                    opacity=0.6
                ),
                row=2, col=1
            )
            
            # Mark anomalies on chart
            symbol_anomalies = [a for a in self.anomaly_log if a['symbol'] == symbol]
            if symbol_anomalies:
                for a in symbol_anomalies[-5:]:  # Last 5 anomalies
                    # Find approximate position (this won't be exact but gives visual cue)
                    fig.add_annotation(
                        x=len(prices)-1, y=prices[-1],
                        text="⚠️",
                        showarrow=False,
                        font=dict(size=20, color='#e74c3c'),
                        bgcolor='rgba(0,0,0,0.5)'
                    )
                    break  # Just show one marker
            
            fig.update_layout(
                template='plotly_dark',
                xaxis_rangeslider_visible=False,
                height=500,
                showlegend=True,
                legend=dict(
                    yanchor="top", y=0.99,
                    xanchor="left", x=0.01,
                    bgcolor='rgba(0,0,0,0.5)'
                ),
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            fig.update_xaxes(title_text="Check Number", row=2, col=1)
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Change %", row=2, col=1)
            
            return fig
            
        except Exception as e:
            print(f"Price chart error: {e}")
            return self._create_empty_chart("Building chart...")
    
    def _create_zscore_chart(self, symbol):
        """Create z-score chart from stored detector values."""
        try:
            if symbol not in self.detector.zscore_history:
                return self._create_empty_chart(f"Waiting for {symbol} data...")
            
            z_scores = self.detector.zscore_history[symbol]
            
            if len(z_scores) < 3:
                return self._create_empty_chart(f"Building baseline... ({len(z_scores)}/30)")
            
            fig = go.Figure()
            
            # Color points based on threshold
            colors = ['#ef5350' if abs(z) > self.detector.threshold else '#42a5f5' 
                     for z in z_scores]
            
            fig.add_trace(go.Scatter(
                y=z_scores,
                mode='lines+markers',
                name='Z-Score',
                line=dict(color='#42a5f5', width=2),
                marker=dict(size=6, color=colors)
            ))
            
            t = self.detector.threshold
            
            # Threshold lines
            fig.add_hline(y=t, line_dash="dash", line_color="#e74c3c",
                        annotation_text=f"Upper Threshold (+{t})",
                        annotation_position="top right")
            fig.add_hline(y=-t, line_dash="dash", line_color="#e74c3c",
                        annotation_text=f"Lower Threshold (-{t})",
                        annotation_position="bottom right")
            fig.add_hline(y=0, line_color="gray", line_width=1)
            
            # Shade anomaly zones
            if z_scores:
                y_max = max(max(z_scores), t + 0.5)
                y_min = min(min(z_scores), -t - 0.5)
                fig.add_hrect(y0=t, y1=y_max, fillcolor="#e74c3c", opacity=0.1, line_width=0)
                fig.add_hrect(y0=y_min, y1=-t, fillcolor="#e74c3c", opacity=0.1, line_width=0)
            
            anomaly_count = sum(1 for z in z_scores if abs(z) > t)
            
            fig.update_layout(
                template='plotly_dark',
                title=f'{symbol} Z-Score History ({anomaly_count} anomalies detected)',
                height=300,
                showlegend=False,
                yaxis_title='Modified Z-Score',
                xaxis_title='Observations',
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            return fig
            
        except Exception as e:
            print(f"Z-score error: {e}")
            return self._create_empty_chart("Loading z-score chart...")
    
    def _create_alerts_display(self):
        """Create enhanced alerts display with indicators, actions, news, and reasoning."""
        if not self.anomaly_log:
            return [html.P("No anomalies yet. Building baseline...",
                        style={'color': '#7f8c8d', 'fontStyle': 'italic'})]
        
        recent = self.anomaly_log[-10:][::-1]
        alerts = []
        
        for anomaly in recent:
            time_str = anomaly['timestamp'].strftime('%H:%M:%S')
            direction = anomaly.get('direction', 'unknown')
            icon = "🔺" if direction == 'up' else "🔻"
            confidence = anomaly.get('confidence', 0)
            recommendation = anomaly.get('recommendation', '')
            change_pct = anomaly.get('price_change_pct', 0)
            rsi = anomaly.get('rsi')
            macd = anomaly.get('macd')
            indicator_action = anomaly.get('indicator_action', 'N/A')
            indicator_conf = anomaly.get('indicator_confidence', 0)
            news_headlines = anomaly.get('news_headlines', [])
            market_context = anomaly.get('market_context', '')
            
            # Color code by confidence
            if confidence >= 80:
                border_color = '#e74c3c'
                bg_color = 'rgba(231, 76, 60, 0.15)'
                confidence_color = '#e74c3c'
            elif confidence >= 50:
                border_color = '#f39c12'
                bg_color = 'rgba(243, 156, 18, 0.1)'
                confidence_color = '#f39c12'
            else:
                border_color = '#3498db'
                bg_color = 'rgba(52, 152, 219, 0.1)'
                confidence_color = '#3498db'
            
            # Indicator action color
            if 'BUY' in indicator_action:
                indicator_color = '#2ecc71'
            elif 'SELL' in indicator_action:
                indicator_color = '#e74c3c'
            else:
                indicator_color = '#95a5a6'
            
            # Build the alert card
            card_children = [
                # Row 1: Basic info
                html.Div([
                    html.Span(f"{icon} "),
                    html.Strong(anomaly['symbol'], style={'fontSize': '16px'}),
                    html.Span(f" ${anomaly['current_price']:,.2f}",
                            style={'marginLeft': '10px', 'fontWeight': 'bold'}),
                    html.Span(f" {change_pct:+.2f}%",
                            style={'color': '#2ecc71' if change_pct > 0 else '#e74c3c',
                                    'marginLeft': '5px'}),
                ]),
                
                # Row 2: Z-Score and Confidence
                html.Div([
                    html.Span(f"Z-Score: {anomaly['z_score']}", 
                            style={'marginRight': '15px'}),
                    html.Span(f"Confidence: ", style={'marginRight': '5px'}),
                    html.Span(f"{confidence}%", style={'color': confidence_color, 'fontWeight': 'bold'}),
                    html.Span(f" | Market: {market_context}",
                            style={'color': '#95a5a6', 'fontSize': '0.85em', 'marginLeft': '10px'}),
                    html.Span(f" | {time_str}",
                            style={'color': '#95a5a6', 'fontSize': '0.85em', 'marginLeft': '10px'}),
                ], style={'marginTop': '4px'}),
                
                # Row 3: Technical Indicators
                html.Div([
                    html.Span("📊 Indicators: ", style={'color': '#bdc3c7'}),
                    html.Span(f"RSI: {rsi}" if rsi else "RSI: --", 
                            style={'marginRight': '15px'}),
                    html.Span(f"MACD: {macd}" if macd else "MACD: --",
                            style={'marginRight': '15px'}),
                    html.Span(f"Signal: ", style={'marginRight': '5px'}),
                    html.Span(f"{indicator_action} ({indicator_conf}%)",
                            style={'color': indicator_color, 'fontWeight': 'bold'}),
                ], style={'marginTop': '4px', 'fontSize': '0.9em'}),
                
                # Row 4: Reasoning Chain
                html.Div([
                    html.Span("🧠 ", style={'fontSize': '12px'}),
                    html.Span(self._get_signal_reasoning(anomaly),
                            style={'color': '#bdc3c7', 'fontSize': '0.8em',
                                    'fontStyle': 'italic'})
                ], style={
                    'marginTop': '6px',
                    'padding': '8px',
                    'backgroundColor': 'rgba(255,255,255,0.03)',
                    'borderRadius': '3px',
                    'borderLeft': '3px solid #7f8c8d'
                }),
                
                # Row 5: Recommendation
                html.Div([
                    html.Span("🎯 ", style={'fontSize': '14px'}),
                    html.Span(recommendation,
                            style={'color': '#ecf0f1', 'fontSize': '0.9em', 'fontStyle': 'italic'}),
                ], style={'marginTop': '6px', 'padding': '6px', 
                        'backgroundColor': 'rgba(255,255,255,0.05)',
                        'borderRadius': '3px'}),
            ]
            
            # Row 6: Clickable News Headlines (if any)
            if news_headlines:
                news_items = []
                for headline in news_headlines:
                    title = headline.get('title', 'No title')
                    url = headline.get('url', '#')
                    display_title = title[:90] + "..." if len(title) > 90 else title
                    
                    news_items.append(
                        html.A(
                            html.Div([
                                html.Span("📰 ", style={'fontSize': '12px'}),
                                html.Span(display_title, style={'fontSize': '0.85em'}),
                                html.Span(" ↗", style={'color': '#3498db', 'fontSize': '0.8em'}),
                            ], style={
                                'padding': '4px 8px',
                                'marginTop': '4px',
                                'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                                'borderRadius': '3px',
                                'borderLeft': '3px solid #3498db',
                            }),
                            href=url,
                            target='_blank',
                            style={'textDecoration': 'none', 'color': '#bdc3c7'}
                        )
                    )
                
                card_children.append(
                    html.Div([
                        html.Div("Related News:", style={
                            'color': '#95a5a6', 'fontSize': '0.8em',
                            'marginTop': '8px', 'marginBottom': '4px',
                            'textTransform': 'uppercase', 'letterSpacing': '1px'
                        }),
                        *news_items
                    ])
                )
            
            alerts.append(html.Div(
                card_children,
                style={
                    'padding': '12px', 'marginBottom': '10px',
                    'backgroundColor': bg_color,
                    'borderLeft': f'5px solid {border_color}',
                    'borderRadius': '5px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'
                }
            ))
        
        return alerts

    def _get_signal_reasoning(self, anomaly):
        """
        Generate human-readable reasoning chain for the signal.
        Example: "Price surged +3.2% → RSI=72 → Overbought → SELL signal"
        """
        direction = anomaly.get('direction', 'unknown')
        indicator_action = anomaly.get('indicator_action', 'N/A')
        change_pct = anomaly.get('price_change_pct', 0)
        rsi = anomaly.get('rsi')
        z_score = anomaly.get('z_score', 0)
        market_context = anomaly.get('market_context', '')
        
        steps = []
        
        # What happened to price?
        if abs(change_pct) > 2:
            word = "surged" if change_pct > 0 else "dropped"
            steps.append(f"Price {word} {change_pct:+.1f}%")
        elif abs(change_pct) > 0.5:
            word = "rose" if change_pct > 0 else "fell"
            steps.append(f"Price {word} {change_pct:+.1f}%")
        
        # What does RSI say?
        if rsi:
            if rsi > 70:
                steps.append(f"RSI={rsi:.0f} → Overbought (>70)")
            elif rsi > 60:
                steps.append(f"RSI={rsi:.0f} → Bullish")
            elif rsi < 30:
                steps.append(f"RSI={rsi:.0f} → Oversold (<30)")
            elif rsi < 40:
                steps.append(f"RSI={rsi:.0f} → Bearish")
            else:
                steps.append(f"RSI={rsi:.0f} → Neutral")
        
        # How unusual?
        if abs(z_score) > 5:
            steps.append(f"Z={z_score} → Extremely unusual")
        elif abs(z_score) > 4:
            steps.append(f"Z={z_score} → Very unusual")
        elif abs(z_score) > 3:
            steps.append(f"Z={z_score} → Unusual")
        
        # Market context
        if market_context == 'mixed':
            steps.append("Market: mixed (coin-specific)")
        elif market_context in ['bullish', 'bearish']:
            steps.append(f"Market: {market_context}")
        
        # Final conclusion
        if 'SELL' in indicator_action:
            if rsi and rsi > 70:
                steps.append("→ Overbought, likely pullback → SELL")
            elif market_context == 'bearish':
                steps.append("→ Bearish trend → SELL")
            else:
                steps.append("→ Bearish momentum → SELL")
        elif 'BUY' in indicator_action:
            if rsi and rsi < 30:
                steps.append("→ Oversold, likely bounce → BUY")
            elif market_context == 'bullish':
                steps.append("→ Bullish trend → BUY")
            else:
                steps.append("→ Bullish momentum → BUY")
        else:
            steps.append("→ Mixed signals → HOLD")
        
        return " → ".join(steps) if steps else "Collecting data for analysis..."

    def _get_signal_reasoning(self, anomaly):
        """Generate human-readable reasoning chain for the signal."""
        direction = anomaly.get('direction', 'unknown')
        indicator_action = anomaly.get('indicator_action', 'N/A')
        change_pct = anomaly.get('price_change_pct', 0)
        rsi = anomaly.get('rsi')
        z_score = anomaly.get('z_score', 0)
        market_context = anomaly.get('market_context', '')
        
        steps = []
        
        # What happened to price?
        if abs(change_pct) > 0.01:  # Only show if there's actual change
            if change_pct > 2:
                steps.append(f"Price surged {change_pct:+.1f}%")
            elif change_pct > 0.5:
                steps.append(f"Price rose {change_pct:+.1f}%")
            elif change_pct < -2:
                steps.append(f"Price dropped {change_pct:+.1f}%")
            elif change_pct < -0.5:
                steps.append(f"Price fell {change_pct:+.1f}%")
            else:
                steps.append(f"Price changed {change_pct:+.2f}%")
        else:
            steps.append("Price stable")
        
        # What does RSI say?
        if rsi:
            if rsi > 70:
                steps.append(f"RSI={rsi:.0f} → Overbought (>70)")
            elif rsi > 60:
                steps.append(f"RSI={rsi:.0f} → Bullish zone")
            elif rsi < 30:
                steps.append(f"RSI={rsi:.0f} → Oversold (<30)")
            elif rsi < 40:
                steps.append(f"RSI={rsi:.0f} → Bearish zone")
            else:
                steps.append(f"RSI={rsi:.0f} → Neutral")
        
        # How unusual?
        if abs(z_score) > 5:
            steps.append(f"Z={z_score:.1f} → Extremely unusual")
        elif abs(z_score) > 4:
            steps.append(f"Z={z_score:.1f} → Very unusual")
        elif abs(z_score) > 3:
            steps.append(f"Z={z_score:.1f} → Unusual")
        
        # Market context
        if market_context == 'mixed':
            steps.append("Market: mixed")
        elif market_context in ['bullish', 'bearish']:
            steps.append(f"Market: {market_context}")
        
        # Final conclusion — FIXED LOGIC
        if 'SELL' in str(indicator_action):
            if rsi and rsi > 70:
                steps.append("→ Overbought, likely pullback → SELL")
            elif direction == 'down':
                steps.append("→ Bearish momentum, price dropping → SELL")
            else:
                steps.append("→ Bearish indicators → SELL")
        elif 'BUY' in str(indicator_action):
            if rsi and rsi < 30:
                steps.append("→ Oversold, likely bounce → BUY")
            elif direction == 'down' and rsi and rsi < 40:
                steps.append("→ Price low, potential reversal → BUY")
            elif direction == 'up':
                steps.append("→ Bullish momentum, price rising → BUY")
            else:
                steps.append("→ Bullish indicators → BUY")
        else:
            steps.append("→ Mixed signals → HOLD")
        
        return " → ".join(steps) if steps else "Collecting data for analysis..."
    
    def _create_empty_chart(self, message="Waiting for data..."):
        """Create placeholder chart."""
        fig = go.Figure()
        fig.update_layout(
            template='plotly_dark',
            title=message,
            height=350,
            annotations=[dict(
                text="📊", xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False, font=dict(size=50)
            )]
        )
        return fig
    
    def run(self, debug=False, port=8050):
        """Launch the dashboard."""
        print(f"🚀 Dashboard: http://localhost:{port}")
        self.app.run(debug=debug, port=port, host='0.0.0.0')