"""
Synthetic Credit Card Spending & Suspicious Activity Dataset Generator
------------------------------------------------------------------
Generates two tables:
  - customers.csv   (100 rows)
  - transactions.csv (~2000-2500 rows)

Also generates a private answer_key.csv (NOT for publishing) listing
exactly which transactions/customers were deliberately injected as
suspicious, so detection rules can be validated against ground truth.

Design goals:
  - Realistic "normal" spending behavior as the majority of the data
  - 15-20 deliberately injected anomalies across 5 categories:
      1. Personal deviation spike
      2. Velocity spike (burst of transactions in a short window)
      3. Geographic deviation
      4. Round-number clustering
      5. Dormant reactivation
  - Anomalies are NOT flagged in the public data - they must be
    discoverable via analysis, same as real-world data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

N_CUSTOMERS = 100
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

CITIES = [
    "Cairo", "Giza", "Alexandria", "Mansoura", "Tanta",
    "Aswan", "Luxor", "Port Said", "Suez", "Ismailia",
    "Dubai", "Riyadh", "Doha", "London", "Istanbul"  # a few "unusual" out-of-country cities
]
HOME_CITIES = CITIES[:10]  # customers are normally based in Egyptian cities
FAR_CITIES = CITIES[10:]   # used for geographic-deviation anomalies

CARD_TYPES = ["Standard", "Gold", "Platinum"]
CARD_TYPE_WEIGHTS = [0.55, 0.30, 0.15]

MERCHANT_CATEGORIES = [
    "Groceries", "Dining", "Fuel", "Utilities", "Online Shopping",
    "Electronics", "Travel", "Entertainment", "Healthcare", "Clothing",
    "Home & Furniture", "Education", "Jewelry", "Cash Withdrawal"
]

# rough typical spend ranges per category (min, max) for "normal" transactions
CATEGORY_SPEND_RANGE = {
    "Groceries": (15, 120),
    "Dining": (10, 90),
    "Fuel": (20, 60),
    "Utilities": (30, 150),
    "Online Shopping": (15, 250),
    "Electronics": (50, 600),
    "Travel": (100, 900),
    "Entertainment": (10, 80),
    "Healthcare": (20, 300),
    "Clothing": (20, 200),
    "Home & Furniture": (50, 500),
    "Education": (50, 400),
    "Jewelry": (100, 1200),
    "Cash Withdrawal": (50, 400),
}

# -----------------------
# 1. Generate Customers
# -----------------------
customers = []
for i in range(1, N_CUSTOMERS + 1):
    cust_id = f"CUST{i:04d}"
    home_city = random.choice(HOME_CITIES)
    age = int(np.clip(np.random.normal(38, 11), 21, 70))
    card_type = random.choices(CARD_TYPES, weights=CARD_TYPE_WEIGHTS)[0]
    # account open date sometime in the last 6 years
    days_since_open = random.randint(60, 2200)
    account_open_date = START_DATE - timedelta(days=days_since_open)
    # income bracket loosely tied to card type
    if card_type == "Standard":
        income_bracket = random.choice(["Low", "Medium"])
    elif card_type == "Gold":
        income_bracket = random.choice(["Medium", "High"])
    else:
        income_bracket = "High"

    # target number of transactions this year: 20-25 avg, with variation 8-32
    n_txns = int(np.clip(np.random.normal(22, 6), 8, 32))

    customers.append({
        "CustomerID": cust_id,
        "HomeCity": home_city,
        "Age": age,
        "CardType": card_type,
        "IncomeBracket": income_bracket,
        "AccountOpenDate": account_open_date.strftime("%Y-%m-%d"),
        "TargetTxnCount": n_txns,  # used for generation only, dropped from public dataset
    })

customers_df = pd.DataFrame(customers)

# -----------------------
# 2. Generate "normal" transactions per customer
# -----------------------
transactions = []
txn_counter = 1

def random_date_between(start, end):
    delta_days = (end - start).days
    if delta_days <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta_days))

# each customer gets a personal "typical spend" multiplier so spending
# is realistically heterogeneous (some customers just spend more than others)
customer_spend_multiplier = {}
customer_preferred_categories = {}

for _, cust in customers_df.iterrows():
    mult = np.clip(np.random.normal(1.0, 0.35), 0.4, 2.5)
    customer_spend_multiplier[cust["CustomerID"]] = mult
    # each customer has 3-6 preferred categories they transact in most often
    n_pref = random.randint(3, 6)
    customer_preferred_categories[cust["CustomerID"]] = random.sample(MERCHANT_CATEGORIES, n_pref)

for _, cust in customers_df.iterrows():
    cid = cust["CustomerID"]
    home_city = cust["HomeCity"]
    open_date = datetime.strptime(cust["AccountOpenDate"], "%Y-%m-%d")
    earliest_txn_date = max(START_DATE, open_date)
    n_txns = int(cust["TargetTxnCount"])
    mult = customer_spend_multiplier[cid]
    pref_categories = customer_preferred_categories[cid]

    for _ in range(n_txns):
        # 80% chance category is one of the customer's preferred ones
        if random.random() < 0.8:
            category = random.choice(pref_categories)
        else:
            category = random.choice(MERCHANT_CATEGORIES)

        low, high = CATEGORY_SPEND_RANGE[category]
        amount = round(np.random.uniform(low, high) * mult, 2)

        txn_date = random_date_between(earliest_txn_date, END_DATE)

        # weekday/weekend natural skew: slightly more dining/entertainment on weekends
        transactions.append({
            "TransactionID": f"TXN{txn_counter:05d}",
            "CustomerID": cid,
            "Date": txn_date.strftime("%Y-%m-%d"),
            "Amount": amount,
            "MerchantCategory": category,
            "TransactionCity": home_city,
        })
        txn_counter += 1

txns_df = pd.DataFrame(transactions)

# -----------------------
# 3. Inject anomalies
# -----------------------
answer_key = []

customer_ids = customers_df["CustomerID"].tolist()

def next_txn_id():
    global txn_counter
    tid = f"TXN{txn_counter:05d}"
    txn_counter += 1
    return tid

# --- 3a. Personal deviation spike (4 customers, 1 spike each) ---
dev_customers = random.sample(customer_ids, 4)
for cid in dev_customers:
    cust_rows = txns_df[txns_df["CustomerID"] == cid]
    avg_amt = cust_rows["Amount"].mean() if len(cust_rows) else 100
    spike_amount = round(avg_amt * random.uniform(8, 15), 2)
    home_city = customers_df.loc[customers_df.CustomerID == cid, "HomeCity"].values[0]
    spike_date = random_date_between(START_DATE + timedelta(days=100), END_DATE)
    tid = next_txn_id()
    new_row = {
        "TransactionID": tid,
        "CustomerID": cid,
        "Date": spike_date.strftime("%Y-%m-%d"),
        "Amount": spike_amount,
        "MerchantCategory": random.choice(["Electronics", "Jewelry", "Travel", "Cash Withdrawal"]),
        "TransactionCity": home_city,
    }
    txns_df = pd.concat([txns_df, pd.DataFrame([new_row])], ignore_index=True)
    answer_key.append({**new_row, "AnomalyType": "Personal Deviation Spike",
                        "Reason": f"Amount ~{spike_amount/avg_amt:.1f}x this customer's average transaction"})

# --- 3b. Velocity spike (4 customers, burst of 6-8 txns in <24 hours) ---
vel_customers = random.sample([c for c in customer_ids if c not in dev_customers], 4)
for cid in vel_customers:
    home_city = customers_df.loc[customers_df.CustomerID == cid, "HomeCity"].values[0]
    burst_date = random_date_between(START_DATE + timedelta(days=60), END_DATE - timedelta(days=1))
    burst_size = random.randint(6, 8)
    burst_ids = []
    for _ in range(burst_size):
        category = random.choice(MERCHANT_CATEGORIES)
        low, high = CATEGORY_SPEND_RANGE[category]
        amount = round(np.random.uniform(low, high), 2)
        tid = next_txn_id()
        new_row = {
            "TransactionID": tid,
            "CustomerID": cid,
            "Date": burst_date.strftime("%Y-%m-%d"),
            "Amount": amount,
            "MerchantCategory": category,
            "TransactionCity": home_city,
        }
        txns_df = pd.concat([txns_df, pd.DataFrame([new_row])], ignore_index=True)
        burst_ids.append(tid)
        answer_key.append({**new_row, "AnomalyType": "Velocity Spike",
                            "Reason": f"1 of {burst_size} transactions by this customer on same day (burst)"})

# --- 3c. Geographic deviation (4 customers, 1-2 txns in a far/unusual city) ---
geo_customers = random.sample([c for c in customer_ids if c not in dev_customers + vel_customers], 4)
for cid in geo_customers:
    n_geo = random.choice([1, 2])
    for _ in range(n_geo):
        far_city = random.choice(FAR_CITIES)
        category = random.choice(["Travel", "Jewelry", "Cash Withdrawal", "Electronics"])
        low, high = CATEGORY_SPEND_RANGE[category]
        amount = round(np.random.uniform(low, high), 2)
        txn_date = random_date_between(START_DATE + timedelta(days=30), END_DATE)
        tid = next_txn_id()
        new_row = {
            "TransactionID": tid,
            "CustomerID": cid,
            "Date": txn_date.strftime("%Y-%m-%d"),
            "Amount": amount,
            "MerchantCategory": category,
            "TransactionCity": far_city,
        }
        txns_df = pd.concat([txns_df, pd.DataFrame([new_row])], ignore_index=True)
        answer_key.append({**new_row, "AnomalyType": "Geographic Deviation",
                            "Reason": f"Transaction city ({far_city}) differs from customer's home city"})

# --- 3d. Round-number clustering (3 customers, 3-4 suspiciously round txns each) ---
round_customers = random.sample(
    [c for c in customer_ids if c not in dev_customers + vel_customers + geo_customers], 3
)
round_amounts_pool = [500, 1000, 1500, 2000, 2500, 3000]
for cid in round_customers:
    home_city = customers_df.loc[customers_df.CustomerID == cid, "HomeCity"].values[0]
    n_round = random.choice([3, 4])
    chosen_amounts = random.sample(round_amounts_pool, n_round)
    for amt in chosen_amounts:
        txn_date = random_date_between(START_DATE + timedelta(days=30), END_DATE)
        tid = next_txn_id()
        new_row = {
            "TransactionID": tid,
            "CustomerID": cid,
            "Date": txn_date.strftime("%Y-%m-%d"),
            "Amount": float(amt),
            "MerchantCategory": "Cash Withdrawal",
            "TransactionCity": home_city,
        }
        txns_df = pd.concat([txns_df, pd.DataFrame([new_row])], ignore_index=True)
        answer_key.append({**new_row, "AnomalyType": "Round-Number Clustering",
                            "Reason": "Suspiciously round transaction amount, part of a cluster"})

# --- 3e. Dormant reactivation (4 customers, long gap then sudden burst) ---
dorm_customers = random.sample(
    [c for c in customer_ids if c not in dev_customers + vel_customers + geo_customers + round_customers], 4
)
for cid in dorm_customers:
    home_city = customers_df.loc[customers_df.CustomerID == cid, "HomeCity"].values[0]
    # force existing transactions for this customer into first 4 months only
    mask = txns_df["CustomerID"] == cid
    txns_df.loc[mask, "Date"] = [
        random_date_between(START_DATE, START_DATE + timedelta(days=110)).strftime("%Y-%m-%d")
        for _ in range(mask.sum())
    ]
    # then inject a burst of 5-6 transactions after a 5+ month gap
    reactivation_start = START_DATE + timedelta(days=280)
    n_react = random.randint(5, 6)
    for _ in range(n_react):
        category = random.choice(MERCHANT_CATEGORIES)
        low, high = CATEGORY_SPEND_RANGE[category]
        amount = round(np.random.uniform(low, high) * 1.5, 2)  # slightly elevated
        txn_date = random_date_between(reactivation_start, END_DATE)
        tid = next_txn_id()
        new_row = {
            "TransactionID": tid,
            "CustomerID": cid,
            "Date": txn_date.strftime("%Y-%m-%d"),
            "Amount": amount,
            "MerchantCategory": category,
            "TransactionCity": home_city,
        }
        txns_df = pd.concat([txns_df, pd.DataFrame([new_row])], ignore_index=True)
        answer_key.append({**new_row, "AnomalyType": "Dormant Reactivation",
                            "Reason": "Sudden activity after 5+ month gap of no transactions"})

# -----------------------
# 4. Finalize & save
# -----------------------
txns_df = txns_df.sort_values(["CustomerID", "Date"]).reset_index(drop=True)
customers_public_df = customers_df.drop(columns=["TargetTxnCount"])

answer_key_df = pd.DataFrame(answer_key)

customers_public_df.to_csv("/home/claude/cc_project/customers.csv", index=False)
txns_df.to_csv("/home/claude/cc_project/transactions.csv", index=False)
answer_key_df.to_csv("/home/claude/cc_project/answer_key_PRIVATE.csv", index=False)

print(f"Customers: {len(customers_public_df)}")
print(f"Transactions: {len(txns_df)}")
print(f"Injected anomalies: {len(answer_key_df)}")
print(answer_key_df["AnomalyType"].value_counts())
