"""Synthetic initial input utility; not target solution."""
import csv

def load_records(path):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def validate_record(row):
    return bool(row.get('id') and row.get('title'))
