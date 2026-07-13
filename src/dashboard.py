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
        self._cached_latest = {}
        self._cached_historical = None  # Cache historical data
        self._last_historical_fetch = 0
        self._last_latest_fetch = {}
        self.setup_layout()
        self.setup_callbacks()
    
    def _get_historical_data(self):
        """Get historical data with caching (only fetch every 10 minutes)."""
        now = time.time()
        
        # Return cached data if it's fresh (less than 10 minutes old)
        if self._cached_historical is not None and (now - self._last_historical_fetch) < 600:
            return self._cached_historical
        
        # Fetch new data
        try:
            print("📥 Dashboard: Fetching historical data...")
            self._cached_historical = self.streamer.historical_data()
            self._last_historical_fetch = now
            print("✅ Dashboard: Historical data loaded")
        except Exception as e:
            print(f"⚠️ Dashboard: Historical fetch failed: {e}")
            if self._cached_historical is None:
                self._cached_historical = {}
        
        return self._cached_historical or {}
    
    def setup_layout(self):
        """Create dashboard layout."""
        self.app.layout = html.Div([
            html.H1(f"📈 {self.streamer.market_type} Anomaly Detection",
                    style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 20}),
            
            # Stats row
            html.Div([
                html.Div([
                    html.H3("Assets"),
                    html.H2(id='stock-count', children=str(len(self.streamer.symbols)))
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Anomalies"),
                    html.H2(id='anomaly-count', children="0", style={'color': '#e74c3c'})
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Source"),
                    html.H2(id='data-source', children=self.streamer.source_name,
                           style={'color': '#27ae60', 'fontSize': '18px'})
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Updated"),
                    html.H2(id='last-update', children="--:--:--")
                ], className='stat-box'),
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': 20, 'flexWrap': 'wrap'}),
            
            # Alert section
            html.Div([
                html.H3("🚨 Recent Anomalies", style={'color': '#e74c3c'}),
                html.Div(id='anomaly-alerts', children=[
                    html.P("Monitoring in progress...",
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
            
            # Update every 30 seconds (but data is cached)
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
            """Update dashboard components."""
            try:
                # Get cached historical data
                hist_data = self._get_historical_data()
                
                # Create charts
                price_fig = self._create_price_chart(selected_symbol, hist_data)
                zscore_fig = self._create_zscore_chart(selected_symbol)
                
                # Alerts and counts
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
    
    def _create_price_chart(self, symbol, hist_data):
        """Create price chart from cached historical data."""
        try:
            if not hist_data or symbol not in hist_data:
                return self._create_empty_chart(f"Loading {symbol} data...")
            
            data = hist_data[symbol]
            if data.empty:
                return self._create_empty_chart(f"No data for {symbol} yet")
            
            # Use last 50 points
            data = data.tail(50)
            
            # Check columns available
            has_ohlc = all(col in data.columns for col in ['Open', 'High', 'Low', 'Close'])
            
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.7, 0.3],
                subplot_titles=(f'{symbol} Price', 'Volume')
            )
            
            if has_ohlc and not data['Open'].equals(data['Close']):
                # Candlestick chart (Yahoo Finance with real OHLC)
                fig.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name='Price',
                        increasing_line_color='#26a69a',
                        decreasing_line_color='#ef5350'
                    ),
                    row=1, col=1
                )
            else:
                # Line chart (CoinGecko or flat data)
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        mode='lines',
                        name='Price',
                        line=dict(color='#42a5f5', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(66, 165, 245, 0.1)'
                    ),
                    row=1, col=1
                )
            
            # Volume bars
            if 'Volume' in data.columns:
                volume_data = data['Volume']
                if volume_data.sum() > 0:
                    colors = []
                    for i in range(len(data)):
                        if i == 0:
                            colors.append('#26a69a')
                        else:
                            colors.append('#ef5350' if data['Close'].iloc[i] < data['Close'].iloc[i-1] else '#26a69a')
                    
                    fig.add_trace(
                        go.Bar(x=data.index, y=volume_data, name='Volume',
                              marker_color=colors, opacity=0.5),
                        row=2, col=1
                    )
            
            # Mark current price
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                fig.add_annotation(
                    x=data.index[-1], y=current_price,
                    text=f"${current_price:,.2f}",
                    showarrow=True, arrowhead=1,
                    bgcolor='rgba(0,0,0,0.7)',
                    font=dict(color='white', size=12)
                )
            
            fig.update_layout(
                template='plotly_dark',
                xaxis_rangeslider_visible=False,
                height=450,
                showlegend=True,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                          bgcolor='rgba(0,0,0,0.5)'),
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            fig.update_xaxes(title_text="Time", row=2, col=1)
            fig.update_yaxes(title_text="Price ($)", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
            
            return fig
            
        except Exception as e:
            print(f"Price chart error: {e}")
            return self._create_empty_chart(f"Error loading chart")
    
    def _create_zscore_chart(self, symbol):
        """Create z-score tracking chart."""
        try:
            if symbol in self.detector.history:
                history = self.detector.history[symbol]
                
                if len(history) > 5:
                    # Calculate z-scores
                    z_scores = []
                    for i in range(len(history)):
                        if i >= self.detector.window_size:
                            window = history[i-self.detector.window_size:i+1]
                            z_score = self.detector.modified_zscore(pd.Series(window)).iloc[-1]
                            z_scores.append(z_score)
                        else:
                            z_scores.append(0)
                    
                    fig = go.Figure()
                    
                    colors = ['#ef5350' if abs(z) > self.detector.threshold else '#42a5f5' 
                             for z in z_scores]
                    
                    fig.add_trace(go.Scatter(
                        y=z_scores, mode='lines+markers',
                        name='Z-Score',
                        line=dict(color='#42a5f5', width=2),
                        marker=dict(size=6, color=colors)
                    ))
                    
                    t = self.detector.threshold
                    fig.add_hline(y=t, line_dash="dash", line_color="#e74c3c",
                                annotation_text=f"+{t}")
                    fig.add_hline(y=-t, line_dash="dash", line_color="#e74c3c",
                                annotation_text=f"-{t}")
                    fig.add_hline(y=0, line_color="gray", line_width=1)
                    
                    fig.update_layout(
                        title=f'{symbol} Z-Score (Threshold: ±{t})',
                        template='plotly_dark',
                        height=300,
                        showlegend=False,
                        yaxis_title='Z-Score',
                        xaxis_title='Observations',
                        margin=dict(l=50, r=50, t=50, b=50)
                    )
                    
                    return fig
            
            return self._create_empty_chart("Building baseline... need more data points")
            
        except Exception as e:
            print(f"Z-score error: {e}")
            return self._create_empty_chart("Loading z-score chart...")
    
    def _create_alerts_display(self):
        """Create alerts display."""
        if not self.anomaly_log:
            return [html.P("No anomalies yet. System is monitoring...",
                          style={'color': '#7f8c8d', 'fontStyle': 'italic'})]
        
        recent = self.anomaly_log[-5:][::-1]
        alerts = []
        
        for anomaly in recent:
            time_str = anomaly['timestamp'].strftime('%H:%M:%S')
            direction = anomaly.get('direction', 'unknown')
            icon = "🔺" if direction == 'up' else "🔻" if direction == 'down' else "•"
            
            alerts.append(html.Div([
                html.Span(f"{icon} "),
                html.Strong(anomaly['symbol']),
                html.Span(f" | Z: {anomaly['z_score']} | "),
                html.Span(f"${anomaly['current_price']:,.2f}"),
                html.Span(f" | {time_str}",
                         style={'color': '#95a5a6', 'fontSize': '0.85em'})
            ], style={
                'padding': '8px', 'marginBottom': '5px',
                'backgroundColor': 'rgba(231, 76, 60, 0.1)',
                'borderLeft': '4px solid #e74c3c',
                'borderRadius': '3px'
            }))
        
        return alerts
    
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
        """Launch dashboard."""
        print(f"🚀 Dashboard: http://localhost:{port}")
        self.app.run(debug=debug, port=port, host='0.0.0.0')