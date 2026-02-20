import json
import random
import argparse
import os
from datetime import datetime

PLANS = ["plan_free", "plan_starter", "plan_pro", "plan_enterprise"]
STATUSES = ["active", "active", "active", "delinquent", "cancelled"]
COUNTRIES = ["US", "CA", "GB", "DE", "FR"]

def generate_customers(date_str, num_customers):
    customers = []
    
    for i in range(1, num_customers + 1):
        cust_id = f"cust_{i}"
        

        
        cust = {
            "customer_id": cust_id,
            "customer_name": f"Customer {i} Ltd",
            "plan_id": random.choice(PLANS),
            "status": random.choice(STATUSES),
            "country": random.choice(COUNTRIES),
            "updated_at": f"{date_str}T00:00:00Z"
        }
        customers.append(cust)
        
    return customers

def save_customers(customers, date_str, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filename = f"customers_{date_str}.jsonl"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        for c in customers:
            f.write(json.dumps(c) + "\n")
            
    print(f"Generated {len(customers)} customers to {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--customers", type=int, default=10)
    parser.add_argument("--output", type=str, default=".")
    
    args = parser.parse_args()
    data = generate_customers(args.date, args.customers)
    save_customers(data, args.date, args.output)
