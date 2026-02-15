#!/usr/bin/env python3
"""
Kira V1 - Configuration Module
Loads credentials from .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API Credentials
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
SESSION_NAME = os.getenv('SESSION_NAME', 'kira_v1')

# Optional settings
LOG_LEVEL = os.getenv('BOT_LOG_LEVEL', 'INFO')

# Validate credentials
if not API_ID or not API_HASH:
    print("❌ ERROR: API_ID and API_HASH must be set in .env file!")
    print("Please create a .env file with your Telegram API credentials.")
    print("Get them from: https://my.telegram.org")
    exit(1)

if API_ID == 34454601 or API_HASH == '32100eb1572c3a449077720f5981b7cb':
    print("⚠️  WARNING: Using default credentials! Please update your .env file with your own API credentials.")
