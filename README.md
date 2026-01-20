# Personal Finance Analytics System

A modular **end-to-end personal finance analytics system** that ingests Amex & Discover credit card transactions, normalizes and stores them, and generates **monthly and yearly spending insights**.

The system is built with a **Python-based, storage-agnostic architecture**, emphasizing automation, extensibility, and long-term financial memory.

---

## Project Overview

Managing personal finances across multiple credit cards quickly becomes messy due to:

- Inconsistent schemas across providers (e.g. Amex & Discover)
- Duplicate or repeated transactions
- No unified category system
- Lack of historical memory for long-term analysis

This project addresses these challenges by building a **persistent analytics pipeline** that transforms raw transaction data into structured, reusable insights.

---

## Key Features

- **Multi-source ingestion & normalization**  
  Standardizes heterogeneous transaction schemas into a unified canonical format.

- **Deduplication & transaction identity tracking**  
  Ensures consistent transaction history across repeated uploads.

- **Persistent financial memory**  
  Maintains historical transaction panels for longitudinal analysis.

- **Analytics & reporting**  
  Generates monthly and yearly spending breakdowns by category.

- **Interactive dashboard**  
  Exposes insights through a multi-page Streamlit interface.

---

## System Architecture

The system follows a layered design:

- **Ingestion Layer**  
  Handles schema alignment, date parsing, and transaction deduplication.

- **Storage Layer**  
  Manages persistent transaction memory and derived analytical panels.

- **Analytics Layer**  
  Performs aggregation and feature engineering for reporting.

- **UI Layer**  
  Presents results via an interactive Streamlit dashboard.

This separation allows individual components to evolve independently (e.g., swapping CSV storage for SQL).

---

## Project Structure

```text
personal-finance-analytics/
│
├── Home.py                # Streamlit application entry point
├── core/                  # Core analytics & agent logic
│   ├── ingestion.py
│   ├── storage.py
│   ├── report.py
│   └── agent.py
│
├── pages/                 # Streamlit multi-page UI
│   └── Data_Breakdown.py
│
├── data/
├── README.md
├── requirements.txt
└── .gitignore
```
## How to Use

### 1. Clone the repository
```bash
git clone https://github.com/dtstevee/personal-finance-analytics.git
cd personal-finance-analytics
```
### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3.Run the application
```bash
streamlit run Home.py
```
