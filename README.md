# Personal Finance Analytics System

A modular **end-to-end personal finance analytics system** that ingests Amex & Discover credit card transactions, normalizes and stores them, and generates **monthly, yearly, and predictive spending insights**.

The system is designed with a **Python-based, storage-agnostic architecture**, emphasizing automation, extensibility, and long-term financial memory.

---

## Project Overview

Managing personal finances across multiple credit cards quickly becomes messy due to:

- Inconsistent schemas across providers (e.g. Amex & Discover)
- Duplicate or repeated transactions
- No unified category system
- Lack of historical memory for long-term analysis

This project addresses these challenges by building a **persistent analytics pipeline** that transforms raw transaction data into structured insights and forward-looking budget forecasts.

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

- **Predictive budgeting (In Progress)**  
  Forecasts next-period category-level spending using regression-based models.

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
  Performs aggregation, feature engineering, and budget prediction.

- **UI Layer**  
  Presents results via an interactive Streamlit dashboard.

This separation allows individual components to evolve independently (e.g., swapping CSV storage for SQL).

---

## Project Structure

```text
personal-finance-analytics/
│
├── app.py                 # Streamlit application entry point
├── core/                  # Core analytics & agent logic
│   ├── ingestion.py
│   ├── storage.py
│   ├── report.py
│   ├── predict.py （developing in progress)
│   └── agent.py
│
├── pages/                 # Streamlit multi-page UI
│   ├── Data_Breakdown.py
│   └── Budget_Prediction.py (developing in progress)
│
├── data/                 
├── README.md
├── requirements.txt
└── .gitignore
```

## Data Handling & Privacy
- No real personal or financial data is included in this repository.
- If transactions.csv is not found, the system automatically initializes a new local dataset with the required schema.
- All user-specific data files are excluded via .gitignore.

This design ensures privacy while maintaining full reproducibility.

