import argparse, os
p=argparse.ArgumentParser();p.add_argument("--password");a=p.parse_args()
password=a.password or os.getenv("MAIL_DEMO_PASSWORD")
print("config", {"password":password})
