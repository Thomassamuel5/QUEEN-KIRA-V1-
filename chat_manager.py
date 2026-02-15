#!/usr/bin/env python3
"""
Kira V1 - Chat Management Module
Multi-account chat management features
"""

import json
import csv
import datetime
import sqlite3
from telethon import TelegramClient
from telethon.tl.types import Channel, User, Chat
from utils import DB_PATH, format_timedelta, safe_datetime_compare

class MultiAccountManager:
    """Manage multiple Telegram accounts"""
    
    def __init__(self, main_client):
        self.accounts = {}
        self.active_accounts = []
        self.main_client = main_client
        self.main_account_added = False
        
    async def add_account(self, session_name, api_id, api_hash, account_name=None):
        """Add a new account to manage"""
        try:
            # This is the main account
            me = await self.main_client.get_me()
            acc_name = account_name or me.first_name or "Main Account"
            
            account_info = {
                'client': self.main_client,
                'name': acc_name,
                'phone': me.phone,
                'user_id': me.id,
                'username': me.username or '',
                'api_id': api_id,
                'api_hash': api_hash,
                'session': session_name,
                'is_main': True
            }
            
            self.accounts[me.id] = account_info
            self.active_accounts.append(me.id)
            self.main_account_added = True
            
            # Store in database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO accounts 
                (account_id, account_name, phone, api_id, api_hash, session_file, last_sync)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (me.id, acc_name, me.phone, api_id, api_hash, session_name, datetime.datetime.now()))
            conn.commit()
            conn.close()
            
            print(f"✅ Added main account: {acc_name} (@{me.username}) ID: {me.id}")
            return me.id
            
        except Exception as e:
            print(f"❌ Error adding account: {e}")
            return None
    
    async def get_all_chats(self, account_id=None, limit=50):
        """Get all chats from specified account(s)"""
        all_chats = []
        accounts_to_check = [account_id] if account_id else self.active_accounts
        
        for acc_id in accounts_to_check:
            if acc_id in self.accounts:
                account = self.accounts[acc_id]
                try:
                    dialogs = await account['client'].get_dialogs(limit=min(limit, 100))
                    
                    for dialog in dialogs:
                        chat = dialog.entity
                        last_date = dialog.date
                        
                        if last_date and hasattr(last_date, 'tzinfo') and last_date.tzinfo is not None:
                            last_date = last_date.replace(tzinfo=None)
                        
                        chat_data = {
                            'account_id': acc_id,
                            'account_name': account['name'],
                            'chat_id': dialog.id,
                            'title': dialog.name or getattr(chat, 'title', 'Unknown'),
                            'username': getattr(chat, 'username', None),
                            'type': type(chat).__name__,
                            'unread_count': dialog.unread_count,
                            'unread_mentions': dialog.unread_mentions_count,
                            'last_message_date': last_date,
                            'archived': dialog.archived,
                            'pinned': dialog.pinned,
                            'deleted': False,
                            'is_user': isinstance(chat, User),
                            'is_channel': isinstance(chat, Channel),
                            'is_group': isinstance(chat, Chat)
                        }
                        
                        if isinstance(chat, (Channel, Chat)):
                            try:
                                if hasattr(chat, 'participants_count'):
                                    chat_data['participants_count'] = chat.participants_count
                            except:
                                pass
                        
                        all_chats.append(chat_data)
                    
                    print(f"✅ Retrieved {len(dialogs)} chats from account {account['name']}")
                    
                except Exception as e:
                    print(f"❌ Error getting chats for account {account['name']}: {e}")
        
        return all_chats
    
    async def sync_chats_to_db(self):
        """Sync all chats from all accounts to database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        chat_count = 0
        for acc_id in self.active_accounts:
            if acc_id in self.accounts:
                account = self.accounts[acc_id]
                try:
                    chats = await self.get_all_chats(acc_id, limit=30)
                    
                    for chat in chats:
                        cursor.execute('''
                            INSERT OR REPLACE INTO chats 
                            (chat_id, title, username, type, participants_count, 
                             archived, deleted, last_accessed, account_id, account_name, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            chat['chat_id'],
                            chat['title'],
                            chat['username'],
                            chat['type'],
                            chat.get('participants_count', 0),
                            chat.get('archived', False),
                            chat.get('deleted', False),
                            datetime.datetime.now(),
                            acc_id,
                            account['name'],
                            json.dumps(chat, default=str)
                        ))
                        chat_count += 1
                    
                    cursor.execute('''
                        UPDATE accounts SET last_sync = ? WHERE account_id = ?
                    ''', (datetime.datetime.now(), acc_id))
                    
                except Exception as e:
                    print(f"❌ Error syncing account {account['name']}: {e}")
        
        conn.commit()
        conn.close()
        return chat_count
