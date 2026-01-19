# Personal Finance Analytics System

A modular **Personal Finance Analytics System** that ingests multi-source credit card transactions, normalizes and stores them, and generates **monthly, yearly, and predictive spending insights**.  
Built with **Python + SQL-ready architecture**, designed for **automation, extensibility, and future AI integration**.

---

## Project Overview

Managing personal finances across multiple credit cards is messy:
- Different schemas (Amex / Chase / Discover)
- Duplicate transactions
- Inconsistent categories
- No long-term financial memory

This project addresses these challenges by building a **Personal Finance Analytics System** that:

1. Ingests raw transaction files from multiple sources  
2. Normalizes and assigns stable transaction IDs  
3. Stores historical data with persistent memory  
4. Analyzes spending patterns by time and category  
5. Predicts future monthly spending  
6. Prepares clean outputs for dashboards and reports  

The system is designed like a **production-grade analytics pipeline**, not a one-off script.

---

## Core Features

### Data Ingestion & Normalization
- Supports multiple banks with different schemas

- - Deterministic transaction ID generation:
- Base key construction
- Duplicate ranking
- Hash-based encoding

### Persistent Financial Memory
- Incremental ingestion without overwriting history
- Enables:
- Monthly spend tracking
- Year-over-year comparisons
- Long-term behavioral analysis

### Analytics & Reporting
- Monthly and yearly spend summaries
- Category-level aggregation
- Rare-category handling
- Report-ready structured outputs

### Predictive Modeling
- Time-aware feature engineering
- Validation-first modeling approach
- Next-month spending forecasts
- Designed for extensible ML strategies

### Agent-Based Architecture
- Analytics logic separated from data access
- Prediction layer cannot directly access raw transaction files
- Enforces clean abstraction boundaries (industry-style design)

---

## Project Structure

```bash
├── ingestion.py     # Data loading, normalization, ID assignment
├── storage.py       # Persistent storage layer (CSV → SQL-ready)
├── report.py        # Monthly & yearly reporting logic
├── predict.py       # Predictive modeling & forecasting
├── agent.py         # Orchestrates tools & enforces access control
├── data/
│   ├── raw/         # Original credit card statements
│   ├── processed/  # Cleaned & merged datasets
│   └── outputs/    # Reports & predictions
└── README.md
