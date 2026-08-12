# Credit Card Transaction Anomaly Analysis

## Project Overview

This project analyzes synthetic credit card transaction data to identify unusual customer transaction patterns using data analytics and anomaly detection techniques.

The project combines Python for data generation and anomaly detection, SQL for data analysis, and Tableau for interactive visualization.

## Anomaly Detection Patterns

The analysis focuses on five transaction anomaly patterns:

- **Velocity Spike** — unusually high transaction activity within a short period
- **Dormant Reactivation** — transactions occurring after a prolonged period of inactivity
- **Geographic Deviation** — transactions occurring in locations that differ significantly from a customer's usual location
- **Round-Number Clustering** — unusual concentration of transactions around round-number amounts
- **Personal Deviation Spike** — transactions significantly higher than a customer's normal spending behavior

## Dashboard

The Tableau dashboard contains two main views:

### Customer Overview & Spending
Provides an overview of:
- Total transactions
- Total customers
- Total spending
- Average transaction amount
- Customer segmentation
- Spending by merchant category and income bracket
- Transaction amount distribution

### Anomaly Overview
Provides:
- Flagged customers
- Flagged transactions
- Percentage of transactions flagged
- Personal deviation analysis
- Velocity spike timeline
- Dormant reactivation timeline
- Geographic deviation heat map
- Round-number clustering analysis

## Tools Used

- Python
- SQL
- Tableau Public

## Key Results

- **2,287** total transactions analyzed
- **100** customers
- **180** flagged transactions
- **42** flagged customers
- **7.87%** of transactions flagged

## Tableau Dashboard

[View the Interactive Tableau Dashboard]((https://public.tableau.com/app/profile/safaa.hilal/viz/CREDITCARDTRANSACTIONANOMALYANALYSIS/Dashboard4?publish=yes))
