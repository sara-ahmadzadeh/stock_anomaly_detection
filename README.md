# 📈 Real-Time Market Anomaly Detection System

A production-ready monitoring system that detects unusual market activity in real-time using statistical analysis. Supports both traditional stocks and cryptocurrency markets through a pluggable data source architecture.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-brightgreen)](http://localhost:8050)

<p align="center">
  <img src="assets/dashboard_demo.gif" alt="Dashboard Demo" width="800"/>
</p>

## 🎯 Overview

Financial analysts and traders spend hours watching screens for unusual market movements. This system automates that process by:

- **Ingesting** real-time market data every 2 minutes
- **Detecting** anomalies using Modified Z-Score statistical analysis
- **Visualizing** results on an interactive dashboard
- **Alerting** stakeholders via email when anomalies occur

The system is designed to surface only truly unusual events, reducing noise and false positives that plague simple threshold-based monitoring.


## ✨ Features

### 🔌 Multi-Source Data Ingestion
- **Stocks**: Real-time data from Yahoo Finance (AAPL, GOOGL, MSFT, AMZN, TSLA)
- **Crypto**: 24/7 data from CoinGecko API (BTC, ETH, SOL, DOGE, ADA, XRP)
- **Switch instantly** by changing one line in `config.py`
- **Extensible**: Add new data sources without changing core logic

### 🧠 Intelligent Anomaly Detection
- **Modified Z-Score** with Median Absolute Deviation (MAD)
- **Adaptive thresholds** using rolling windows
- **Multi-metric validation** (price + volume for stocks)
- **Configurable sensitivity** per market type

### 📊 Real-Time Dashboard
- **Live candlestick charts** with moving averages
- **Z-Score tracking** with threshold visualization
- **Anomaly alert panel** showing recent detections
- **System health metrics** (monitoring status, anomaly count)
- **Dark theme** designed for extended monitoring sessions

### 🚨 Alert System
- **Email notifications** for confirmed anomalies
- **Slack webhook integration** (optional)
- **Anomaly logging** for historical analysis
- **Configurable alert rules**

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Gmail account (for email alerts)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/stock-anomaly-detection.git
cd stock-anomaly-detection

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your email credentials


## 🎬 Live Demo

<p align="center">
  <img src="assets/dashboard_overview.png" alt="Dashboard" width="800"/>
</p>

### Anomaly Detection in Action

<p align="center">
  <img src="assets/terminal_output.png" alt="Terminal Output" width="600"/>
</p>

### Z-Score Tracking

<p align="center">
  <img src="assets/zscore_chart.png" alt="Z-Score Chart" width="600"/>
</p>


![Dashboard Demo](assets/dashboard_demo.gif)