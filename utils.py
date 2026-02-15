#!/usr/bin/env python3
"""
Kira V1 - Utility Functions
Database and helper functions
"""

import sqlite3
import datetime
import json
import os
from datetime import timedelta

# Define DB_PATH at module level
DB_PATH = "kira_chats.db"

def init_database():
    """Initialize SQLite database for storing chat data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables for storing chat information
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        title TEXT,
        username TEXT,
        type TEXT,
        participants_count INTEGER,
        archived BOOLEAN DEFAULT 0,
        deleted BOOLEAN DEFAULT 0,
        last_accessed TIMESTAMP,
        account_id INTEGER,
        account_name TEXT,
        metadata TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER UNIQUE,
        account_name TEXT,
        phone TEXT,
        api_id INTEGER,
        api_hash TEXT,
        session_file TEXT,
        last_sync TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')
    
    conn.commit()
    conn.close()
    return DB_PATH

def safe_datetime_compare(date1, date2):
    """Safely compare two datetime objects"""
    if not date1 or not date2:
        return 0
    
    # Convert to naive datetime if needed
    if hasattr(date1, 'tzinfo') and date1.tzinfo is not None:
        date1 = date1.replace(tzinfo=None)
    if hasattr(date2, 'tzinfo') and date2.tzinfo is not None:
        date2 = date2.replace(tzinfo=None)
    
    return (date1 - date2).days

def format_timedelta(dt):
    """Format time difference in a human readable way"""
    if not dt:
        return "Unknown"
    
    now = datetime.datetime.now()
    
    # Make both datetimes naive for comparison
    dt_naive = dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo is not None else dt
    now_naive = now.replace(tzinfo=None) if hasattr(now, 'tzinfo') and now.tzinfo is not None else now
    
    diff = now_naive - dt_naive
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

# Initialize database
init_database()
