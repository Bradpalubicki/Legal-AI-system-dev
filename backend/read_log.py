#!/usr/bin/env python3
"""Read uvicorn log file properly"""
import sys

with open('uvicorn.log', 'rb') as f:
    content = f.read()

# Decode, replacing invalid bytes
text = content.decode('utf-8', errors='replace')

# Get last 5000 characters
last_part = text[-5000:]

# Find "Full traceback" section
if "Full traceback" in last_part:
    idx = last_part.find("Full traceback")
    print(last_part[idx:])
else:
    # Just print last 2000 chars
    print("No 'Full traceback' found. Last 2000 characters:")
    print(last_part[-2000:])
