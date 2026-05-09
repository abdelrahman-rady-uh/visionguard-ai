#!/usr/bin/env python
"""Test script to debug import issues"""
import sys
import traceback

print("Python version:", sys.version)
print("Starting import test...\n")

try:
    print("1. Importing dotenv...")
    from dotenv import load_dotenv
    print("   ✓ dotenv imported successfully\n")
except Exception as e:
    print(f"   ✗ Error importing dotenv: {e}\n")
    traceback.print_exc()

try:
    print("2. Loading environment variables...")
    load_dotenv()
    print("   ✓ Environment loaded\n")
except Exception as e:
    print(f"   ✗ Error loading env: {e}\n")
    traceback.print_exc()

try:
    print("3. Importing backend.app...")
    from backend.app import app
    print("   ✓ backend.app imported successfully\n")
except Exception as e:
    print(f"   ✗ Error importing backend.app: {e}\n")
    traceback.print_exc()
    sys.exit(1)

print("All imports successful!")
print("Starting Flask app...")
import os
os.environ['FLASK_DEBUG'] = 'False'
app.run(host="127.0.0.1", port=5000, debug=False)
