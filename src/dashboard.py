# dashboard.py
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import threading
import time

class AnomalyDashboard:
    def __init__(self, streamer, detector):
        self.app = dash.Dash(__name__)
        self.streamer = streamer
        self.detector = detector
        self.anomaly_log = []
        self.current_data = pd.DataFrame()
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Create dashboard layout with Plotly/Dash."""
        self.app.layout = html.Div([
            html.H1("📈 Stock Market Anomaly Detection System",
                    style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
            
            # Stats row
            html.Div([
                html.Div([
                    html.H3("Stocks Monitored"),
                    html.H2(id='stock-count', children="5")
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Anomalies Detected"),
                    html.H2(id='anomaly-count', children="0", 
                           style={'color': '#e74c3c'})
                ], className='stat-box'),
                
                html.Div([
                    html.H3("Last Update"),
                    html.H2(id='last-update', children="--:--:--")
                ], className='stat-box'),
                
                html.Div([
                    html.H3("System Status"),
                    html.H2(id='system-status', children="🟢 Active",
                           style={'color': '#27ae60'})
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
                # Stock selector
                html.Label("Select Stock:", style={'fontWeight': 'bold', 'marginRight': 10}),
                dcc.Dropdown(
                    id='stock-selector',
                    options=[{'label': s, 'value': s} for s in self.streamer.symbols],
                    value=self.streamer.symbols[0],
                    style={'width': '30%', 'marginBottom': 20, 'color': 'black'}
                ),
                
                # Price chart
                dcc.Graph(id='live-price-chart'),
                
                # Z-score chart
                dcc.Graph(id='zscore-chart'),
            ]),
            
            # Update interval (every 30 seconds)
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # 30 seconds in milliseconds
                n_intervals=0
            )
        ], style={'padding': 20, 'backgroundColor': '#1a1a2e', 'color': 'white', 
                   'minHeight': '100vh', 'fontFamily': 'Arial'})
    
    def setup_callbacks(self):
        """Setup all dashboard callbacks."""
        
        @self.app.callback(
            [Output('live-price-chart', 'figure'),
             Output('zscore-chart', 'figure'),
             Output('anomaly-alerts', 'children'),
             Output('anomaly-count', 'children'),
             Output('last-update', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('stock-selector', 'value')]
        )
        def update_dashboard(n, selected_stock):
            """Update all dashboard components."""
            try:
                # Fetch latest data
                latest_data = self.streamer.fetch_latest()
                
                if not latest_data.empty and selected_stock in latest_data.index:
                    stock_data = latest_data.loc[selected_stock]
                    
                    # Run anomaly detection
                    result = self.detector.detect_anomalies(
                        selected_stock, 
                        stock_data['close']
                    )
                    
                    # Log anomaly if detected
                    if result['is_anomaly']:
                        anomaly_record = {
                            'symbol': selected_stock,
                            'timestamp': datetime.now(),
                            'z_score': result['z_score'],
                            'direction': result['direction'],
                            'current_price': stock_data['close'],
                            'volume': stock_data['volume']
                        }
                        self.anomaly_log.append(anomaly_record)
                        
                        # Keep only last 50 anomalies
                        if len(self.anomaly_log) > 50:
                            self.anomaly_log = self.anomaly_log[-50:]
                    
                    # Create price chart
                    price_fig = self.create_price_chart(selected_stock, result)
                    
                    # Create z-score chart
                    zscore_fig = self.create_zscore_chart(selected_stock)
                    
                    # Create alerts display
                    alerts = self.create_alerts_display()
                    
                    # Count anomalies
                    anomaly_count = str(len(self.anomaly_log))
                    
                    # Update timestamp
                    current_time = datetime.now().strftime('%H:%M:%S')
                    
                    return price_fig, zscore_fig, alerts, anomaly_count, current_time
                
                # If no data, return empty figures
                return self.create_empty_chart(), self.create_empty_chart(), \
                       [html.P("Waiting for data...")], "0", "--:--:--"
                       
            except Exception as e:
                print(f"Dashboard update error: {e}")
                return self.create_empty_chart(), self.create_empty_chart(), \
                       [html.P(f"Error: {str(e)}", style={'color': 'red'})], \
                       str(len(self.anomaly_log)), datetime.now().strftime('%H:%M:%S')
    
    def create_price_chart(self, symbol, anomaly_result):
        """Create price chart with anomaly indicators."""
        try:
            # Get recent history for the symbol
            hist = self.streamer.historical_data(period="1d")
            
            if symbol in hist and not hist[symbol].empty:
                data = hist[symbol].tail(50)  # Last 50 data points
                
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f'{symbol} Price Action', 'Volume')
                )
                
                # Candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name='OHLC',
                        increasing_line_color='#26a69a',
                        decreasing_line_color='#ef5350'
                    ),
                    row=1, col=1
                )
                
                # Add SMA lines
                data['SMA_5'] = data['Close'].rolling(window=5).mean()
                data['SMA_20'] = data['Close'].rolling(window=20).mean()
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['SMA_5'],
                        name='5-period SMA',
                        line=dict(color='#ffa726', width=1)
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data['SMA_20'],
                        name='20-period SMA',
                        line=dict(color='#42a5f5', width=1)
                    ),
                    row=1, col=1
                )
                
                # Mark current anomaly if detected
                if anomaly_result['is_anomaly']:
                    current_price = data['Close'].iloc[-1]
                    fig.add_trace(
                        go.Scatter(
                            x=[data.index[-1]],
                            y=[current_price],
                            mode='markers',
                            marker=dict(
                                symbol='x',
                                size=15,
                                color='red',
                                line=dict(width=2)
                            ),
                            name=f"Anomaly (z={anomaly_result['z_score']})"
                        ),
                        row=1, col=1
                    )
                
                # Volume bars
                colors = ['#ef5350' if row['Close'] < row['Open'] 
                         else '#26a69a' for _, row in data.iterrows()]
                
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data['Volume'],
                        name='Volume',
                        marker_color=colors,
                        opacity=0.7
                    ),
                    row=2, col=1
                )
                
                # Update layout
                fig.update_layout(
                    template='plotly_dark',
                    xaxis_rangeslider_visible=False,
                    height=500,
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        bgcolor='rgba(0,0,0,0.5)'
                    ),
                    margin=dict(l=50, r=50, t=50, b=50)
                )
                
                # Update axes
                fig.update_xaxes(title_text="Time", row=2, col=1)
                fig.update_yaxes(title_text="Price ($)", row=1, col=1)
                fig.update_yaxes(title_text="Volume", row=2, col=1)
                
                return fig
            
            return self.create_empty_chart()
            
        except Exception as e:
            print(f"Error creating price chart: {e}")
            return self.create_empty_chart()
    
    def create_zscore_chart(self, symbol):
        """Create z-score tracking chart."""
        try:
            # Get z-score history from detector
            if symbol in self.detector.history:
                zscore_data = self.detector.history[symbol]
                
                if len(zscore_data) > 1:
                    # Calculate z-scores for all historical points
                    z_scores = []
                    for i in range(len(zscore_data)):
                        if i >= self.detector.window_size:
                            window = zscore_data[i-self.detector.window_size:i+1]
                            z_score = self.detector.modified_zscore(
                                pd.Series(window)
                            ).iloc[-1]
                            z_scores.append(z_score)
                        else:
                            z_scores.append(0)
                    
                    fig = go.Figure()
                    
                    # Z-score line
                    fig.add_trace(go.Scatter(
                        y=z_scores,
                        mode='lines+markers',
                        name='Z-Score',
                        line=dict(color='#42a5f5', width=2),
                        marker=dict(
                            size=8,
                            color=['#ef5350' if abs(z) > self.detector.threshold 
                                   else '#42a5f5' for z in z_scores]
                        )
                    ))
                    
                    # Threshold lines
                    fig.add_hline(
                        y=self.detector.threshold,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Upper Threshold (+{self.detector.threshold})",
                        annotation_position="top right"
                    )
                    
                    fig.add_hline(
                        y=-self.detector.threshold,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Lower Threshold (-{self.detector.threshold})",
                        annotation_position="bottom right"
                    )
                    
                    fig.add_hline(
                        y=0,
                        line_color="gray",
                        line_width=1
                    )
                    
                    # Shade anomaly regions
                    fig.add_hrect(
                        y0=self.detector.threshold,
                        y1=max(z_scores + [self.detector.threshold + 1]),
                        fillcolor="red",
                        opacity=0.1,
                        line_width=0
                    )
                    
                    fig.add_hrect(
                        y0=min(z_scores + [-self.detector.threshold - 1]),
                        y1=-self.detector.threshold,
                        fillcolor="red",
                        opacity=0.1,
                        line_width=0
                    )
                    
                    fig.update_layout(
                        title=f'{symbol} Z-Score History',
                        template='plotly_dark',
                        height=300,
                        showlegend=False,
                        yaxis_title='Modified Z-Score',
                        xaxis_title='Observations',
                        margin=dict(l=50, r=50, t=50, b=50)
                    )
                    
                    return fig
            
            return self.create_empty_chart()
            
        except Exception as e:
            print(f"Error creating z-score chart: {e}")
            return self.create_empty_chart()
    
    def create_alerts_display(self):
        """Create alerts display from anomaly log."""
        if not self.anomaly_log:
            return [html.P("No anomalies detected yet. System is monitoring...",
                          style={'color': '#7f8c8d', 'fontStyle': 'italic'})]
        
        # Show last 5 anomalies
        recent_anomalies = self.anomaly_log[-5:][::-1]
        
        alerts = []
        for anomaly in recent_anomalies:
            time_str = anomaly['timestamp'].strftime('%H:%M:%S')
            direction_icon = "🔺" if anomaly['direction'] == 'up' else "🔻"
            
            alert_item = html.Div([
                html.Span(f"{direction_icon} "),
                html.Strong(f"{anomaly['symbol']}"),
                html.Span(f" - Z-Score: {anomaly['z_score']} "),
                html.Span(f"(${anomaly['current_price']:.2f}) "),
                html.Span(f"at {time_str}",
                         style={'color': '#95a5a6', 'fontSize': '0.9em'})
            ], style={
                'padding': '8px',
                'marginBottom': '5px',
                'backgroundColor': 'rgba(231, 76, 60, 0.1)',
                'borderLeft': '4px solid #e74c3c',
                'borderRadius': '3px'
            })
            
            alerts.append(alert_item)
        
        return alerts
    
    def create_empty_chart(self):
        """Create an empty placeholder chart."""
        fig = go.Figure()
        fig.update_layout(
            template='plotly_dark',
            title='Waiting for data...',
            height=400,
            annotations=[dict(
                text="Loading market data...",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=20, color='gray')
            )]
        )
        return fig
    
    def run(self, debug=True, port=8050):
        """Launch the dashboard."""
        print(f"🚀 Dashboard starting on http://localhost:{port}")
        print("📊 Open your browser to view the live monitoring system")
        self.app.run(debug=debug, port=port, host='0.0.0.0')