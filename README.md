# Project Name: "Real-Time Stock Market Anomaly Detection System"

## What It Builds:
A live monitoring system that ingests stock price data, detects unusual price movements using statistical methods, visualizes anomalies on an interactive dashboard, and sends email/Slack alerts when anomalies occur.

## Business Problem It Solves:
Financial analysts and traders need to quickly identify unusual market activity that could indicate breaking news, market manipulation, or trading opportunities. Instead of staring at screens all day, this system surfaces only the truly unusual events.

## Key Features
- Real-time data streaming from Yahoo Finance
- Multi-metric anomaly detection (price + volume)
- Adaptive thresholds using rolling statistics
- Interactive dashboard with candlestick charts
- Automated email/Slack alerts
- False positive reduction through volume confirmation

## Quick Start
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
