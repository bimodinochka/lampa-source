import json
import os

# --- LOAD TEST DATA ---
def load_test_data():
    """Load test data from JSON file"""
    try:
        with open("test_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: test_data.json not found, using empty data")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error loading test_data.json: {e}")
        return {}


def get_test_data(key, default=None):
    """Safely get test data with fallback"""
    return TEST_DATA.get(key, default if default is not None else [])


def save_test_data():
    """Save test data back to JSON file"""
    try:
        with open("test_data.json", "w", encoding="utf-8") as f:
            json.dump(TEST_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving test_data.json: {e}")


def update_test_data(key, value):
    """Update test data and save to file"""
    TEST_DATA[key] = value
    save_test_data()


TEST_DATA = load_test_data() 