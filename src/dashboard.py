# Dashboard Creation
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

class AnomalyDashboard:
    def __init__(self, streamer, detector):
        self.app = dash.Dash(__name__)
        self.streamer = streamer
        self.detector = detector
        self.anomaly_log = []
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Create dashboard layout with Plotly/Dash."""
        self.app.layout = html.Div([
            html.H1("📈 Stock Market Anomaly Detection System",
                    style={'textAlign': 'center', 'color': '#2c3e50'}),
            
            html.Div([
                html.Div([
                    html.H3("Latest Anomalies"),
                    html.Div(id='anomaly-alerts')
                ], className='alerts-panel'),
                
                html.Div([
                    dcc.Graph(id='live-price-chart'),
                    dcc.Graph(id='zscore-chart'),
                ]),
                
                html.Div([
                    dcc.Graph(id='anomaly-history-chart')
                ])
            ]),
            
            dcc.Interval(
                id='interval-component',
                interval=60*1000,  # Update every minute
                n_intervals=0
            )
        ])
    
    def create_price_chart(self, data):
        """Create candlestick chart with anomaly markers."""
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3])
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Volume bars
        colors = ['red' if row['close'] < row['open'] else 'green' 
                 for _, row in data.iterrows()]
        fig.add_trace(
            go.Bar(x=data.index, y=data['volume'], name='Volume',
                  marker_color=colors),
            row=2, col=1
        )
        
        # Mark anomalies
        anomalies = [a for a in self.anomaly_log if a['timestamp'] in data.index]
        if anomalies:
            anomaly_times = [a['timestamp'] for a in anomalies]
            anomaly_prices = [data.loc[t, 'high'] * 1.02 for t in anomaly_times]
            
            fig.add_trace(
                go.Scatter(
                    x=anomaly_times,
                    y=anomaly_prices,
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=15, color='red'),
                    name='Anomaly'
                ),
                row=1, col=1
            )
        
        fig.update_layout(
            title='Real-Time Stock Price & Volume',
            xaxis_title='Time',
            yaxis_title='Price ($)',
            template='plotly_dark',
            height=600
        )
        
        return fig
    
    def run(self, debug=True):
        """Launch the dashboard."""
        self.app.run_server(debug=debug, port=8050)