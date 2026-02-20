import csv
import argparse
import os
from datetime import datetime



PRICING_RULES = [
    {"product_id": "prod_api_requests", "plan_id": "plan_free", "unit": "requests", "price": 0.00, "curr": "USD"},
    

    {"product_id": "prod_api_requests", "plan_id": "plan_starter", "unit": "requests", "price": 0.0001, "curr": "USD"},
    {"product_id": "prod_storage_gb", "plan_id": "plan_starter", "unit": "gb_month", "price": 0.10, "curr": "USD"},
    

    {"product_id": "prod_api_requests", "plan_id": "plan_pro", "unit": "requests", "price": 0.00008, "curr": "USD"},
    {"product_id": "prod_storage_gb", "plan_id": "plan_pro", "unit": "gb_month", "price": 0.08, "curr": "USD"},
    {"product_id": "prod_compute_minutes", "plan_id": "plan_pro", "unit": "minutes", "price": 0.05, "curr": "USD"},


    {"product_id": "prod_api_requests", "plan_id": "plan_enterprise", "unit": "requests", "price": 0.00005, "curr": "USD"},
    {"product_id": "prod_storage_gb", "plan_id": "plan_enterprise", "unit": "gb_month", "price": 0.05, "curr": "USD"},
    {"product_id": "prod_compute_minutes", "plan_id": "plan_enterprise", "unit": "minutes", "price": 0.03, "curr": "USD"},
    {"product_id": "prod_ai_tokens", "plan_id": "plan_enterprise", "unit": "tokens", "price": 0.000002, "curr": "USD"},
]

def generate_pricing(output_dir):
    filename = "pricing_catalog.csv"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["rate_id", "product_id", "plan_id", "unit", "unit_price", "currency", "effective_from", "effective_to"])
        
        for i, rule in enumerate(PRICING_RULES):
            rate_id = f"rate_{i+1:03d}"
            eff_from = f"{datetime.now().year}-01-01"
            eff_to = ""
            
            writer.writerow([
                rate_id,
                rule["product_id"],
                rule["plan_id"],
                rule["unit"],
                rule["price"],
                rule["curr"],
                eff_from,
                eff_to
            ])
            
    print(f"Generated pricing catalog to {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default=".")
    args = parser.parse_args()
    
    generate_pricing(args.output)
