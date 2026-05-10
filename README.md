# CryptoAnalyst Trading Toolkit

**CryptoAnalyst Trading Toolkit** is a prototype trading research application focused on technical market analysis, chart/image interpretation, ML-assisted signal processing, order book visualization, and trader decision support.

This project is part of a professional portfolio for **Trader Analyst / Crypto Market Analyst / Quant Research** roles.

---

## Objective

The objective of this project is to demonstrate a custom-built trading analysis workflow capable of supporting:

- Market structure analysis
- Technical pattern recognition
- Chart and image-based analysis
- ML-assisted feature processing
- Order book visualization
- Trader dashboard monitoring
- Decision-support reporting

---

## Application Overview

The application is organized into four main modules:

CryptoAnalyst/
│
├── Chatbot
├── HMI
├── MLFramework
└── TechAnalyze
Module Summary
Module	Purpose
Chatbot	Assistant and reporting layer designed to explain market context and summarize trade-relevant insights.
HMI	User interface layer for visualizing technical analysis, market structures, model outputs, and decision-support information.
MLFramework	Machine-learning framework for processing market features and supporting signal classification.
TechAnalyze	Technical analysis engine focused on price structures, trend behavior, support/resistance zones, order book data, patterns, and market context.
High-Level Architecture
Market Data / Chart Image / Technical Inputs
                  ↓
             TechAnalyze
                  ↓
             MLFramework
                  ↓
                  HMI
                  ↓
          Chatbot / Report Layer

The goal is to combine technical analysis, machine learning, visualization, and natural-language explanation into a single research-oriented trading toolkit.

Screenshots
Main HMI

The main dashboard provides access to different analysis views, including technical resume, fast analysis, order book, report, and chatbot-related components.

<img src="docs/screenshots/HMI_Main.png" width="900">
Technical Resume

The technical resume view summarizes multiple indicators across different timeframes, helping evaluate market context, trend behavior, momentum, volatility, and signal strength.

<img src="docs/screenshots/HMI_Resume.png" width="900">
Order Book View

The order book view is designed to support market microstructure analysis and order-flow interpretation.

<img src="docs/screenshots/HMI_Orderbook.png" width="900">
ChatBot View

The chatbot layer is intended to support explanation, reporting, and interpretation of technical findings.

<img src="docs/screenshots/HMI_ChatBot.png" width="900">
Extra Plot Patterns

Additional plots help visualize indicator behavior, patterns, market structure, and technical conditions.

<img src="docs/screenshots/HMI_ExtraPlotPatterns.png" width="900">
Portfolio Relevance

This project demonstrates skills that are relevant for Trader Analyst and Crypto Market Analyst roles:

Technical analysis
Market structure interpretation
Crypto market monitoring
Data-driven trading research
Python-based tooling
Machine-learning workflow design
Order book and market microstructure visualization
Dashboard/HMI development
Clear communication of technical findings
Decision-support system design
Current Status

This is an active prototype. The current repository is prepared as a portfolio-safe version and does not include:

Private credentials
API keys
Real broker accounts
Private trading records
Sensitive execution logic
Production trading parameters
Roadmap

Planned improvements include:

Improved crypto research layer
Token profile analysis
Catalyst tracking
Liquidity and order-flow notes
Strategy brief generation
Additional documentation
Cleaner installation instructions
More detailed example workflows
Disclaimer

This project is for research, educational, and portfolio demonstration purposes only.

It is not financial advice and does not guarantee trading performance.
