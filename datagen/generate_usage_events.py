import json
import random
import uuid
import argparse
import os
from datetime import datetime, timedelta


PRODUCTS = ["prod_api_requests", "prod_storage_gb", "prod_compute_minutes", "prod_ai_tokens"]
UNITS = {
    "prod_api_requests": "requests",
    "prod_storage_gb": "gb_month",
    "prod_compute_minutes": "minutes",
    "prod_ai_tokens": "tokens"
}
REGIONS = ["us-east-1", "us-west-2", "eu-central-1"]

def generate_events(date_str, num_customers, events_per_customer, late_prob=0.01, duplicate_prob=0.01):
    """
    Generates synthetic usage events for a given date.
    
    Args:
        date_str (str): Date string YYYY-MM-DD
        num_customers (int): Number of unique customers to simulate
        events_per_customer (int): Average events per customer
        late_prob (float): Probability of an event being "late" (timestamp < date)
        duplicate_prob (float): Probability of emitting a duplicate event
    """
    current_date = datetime.strptime(date_str, "%Y-%m-%d")
    customers = [f"cust_{i}" for i in range(1, num_customers + 1)]
    
    events = []
    
    for cust in customers:
        # Randomize events per customer
        count = int(random.gauss(events_per_customer, events_per_customer * 0.2))
        count = max(1, count)
        
        for _ in range(count):
            product = random.choice(PRODUCTS)
            
            if random.random() < late_prob:
                # Late-arriving event
                days_late = random.randint(1, 7)
                ts = current_date - timedelta(days=days_late)
            else:

                seconds_offset = random.randint(0, 86399)
                ts = current_date + timedelta(seconds=seconds_offset)
                
            event = {
                "event_id": str(uuid.uuid4()),
                "event_timestamp": ts.isoformat() + "Z",
                "customer_id": cust,
                "product_id": product,
                "plan_id": f"plan_{random.choice(['starter', 'pro', 'enterprise'])}",
                "quantity": abs(round(random.gauss(10, 5), 2)),
                "unit": UNITS[product],
                "region": random.choice(REGIONS),
                "schema_version": "1.0"
            }
            
            events.append(event)
            
            if random.random() < duplicate_prob:
                events.append(event)

    return events

def save_events(events, date_str, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    filename = f"usage_events_{date_str}.jsonl"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
            
    print(f"Generated {len(events)} events to {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate usage events")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Date to generate for (YYYY-MM-DD)")
    parser.add_argument("--customers", type=int, default=10, help="Number of customers")
    parser.add_argument("--events", type=int, default=5, help="Avg events per customer")
    parser.add_argument("--output", type=str, default=".", help="Output directory")
    
    args = parser.parse_args()
    
    events = generate_events(args.date, args.customers, args.events)
    save_events(events, args.date, args.output)
