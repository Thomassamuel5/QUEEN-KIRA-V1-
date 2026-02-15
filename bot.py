#!/usr/bin/env python3
"""
Kira V1 - Core Bot Module
Main bot client and command handlers with auto-typing and owner-only control
"""

import asyncio
import os
import time
import random
import datetime
import math
import urllib.parse
import json
import subprocess
import sys
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.messages import DeleteMessagesRequest, SendMessageRequest
from telethon.tl.functions.channels import InviteToChannelRequest, EditBannedRequest, JoinChannelRequest
from telethon.tl.types import InputMessagesFilterEmpty, ChatBannedRights, MessageEntityMention
from telethon.errors import FloodWaitError, MessageIdInvalidError, ChatAdminRequiredError, UserNotParticipantError

# Import configuration
from config import API_ID, API_HASH, SESSION_NAME

# Import modules
from utils import DB_PATH, format_timedelta, safe_datetime_compare
from chat_manager import MultiAccountManager
import ai_module

# Initialize client with credentials from .env
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Initialize account manager
account_manager = MultiAccountManager(client)

# Owner ID (will be set after login)
owner_id = None

# ==================== DECORATORS ====================

def owner_only(func):
    """Decorator to restrict command usage to bot owner only"""
    async def wrapper(event):
        global owner_id
        if event.sender_id != owner_id:
            await event.reply("❌ You are not authorized to use this bot.")
            return
        return await func(event)
    return wrapper

async def auto_typing(event, delay=1.0):
    """Show typing indicator before responding"""
    async with client.action(event.chat_id, 'typing'):
        await asyncio.sleep(delay)

def with_typing(delay=1.0):
    def decorator(func):
        async def wrapper(event):
            await auto_typing(event, delay)
            return await func(event)
        return wrapper
    return decorator

# ==================== COMMAND HANDLERS ====================

# ---------- Basic ----------
@client.on(events.NewMessage(pattern=r'^\.ping$'))
@owner_only
@with_typing(0.5)
async def ping_handler(event):
    """Check bot response time"""
    start = time.time()
    message = await event.reply('🏓 Pong!')
    end = time.time()
    await message.edit(f'🏓 Pong! `{round((end - start) * 1000, 3)}ms`')

@client.on(events.NewMessage(pattern=r'^\.alive$'))
@owner_only
@with_typing(1.0)
async def alive_handler(event):
    """Check if bot is running"""
    await event.reply('**Kira V1 is alive!** ✨\nMulti-File Edition with AI & Auto-Typing')

@client.on(events.NewMessage(pattern=r'^\.help$'))
@owner_only
@with_typing(1.5)
async def help_handler(event):
    """Show all commands"""
    help_text = """
**🤖 Kira V1 Commands (Owner Only)**

**🌐 Web Search & AI:**
`.google <query>` - Search the web
`.ai <message>` - Chat with AI

**📊 Account & Chats:**
`.mychats` - View all chats
`.listaccounts` - List managed accounts
`.backupchats` - Backup chat data
`.exportchats csv/json` - Export chats
`.findchat name` - Search chats
`.chatstats` - Chat statistics
`.chatinfo id/name` - Detailed chat info
`.clearchats days` - Find inactive chats

**👤 Profile:**
`.name first last` - Change profile name
`.bio text` - Change profile bio
`.setpfp` - Set profile picture (reply to image)
`.delpfp` - Delete profile picture
`.pfp` - Get your profile photo

**📱 Chat Management:**
`.purge [n]` - Delete last n messages (or reply to start)
`.del` - Delete replied message
`.pin` - Pin replied message
`.unpin` - Unpin last pinned message
`.kick` - Kick replied user (need admin)
`.invite @username` - Invite user to group
`.mute [duration]` - Mute user (duration in minutes)
`.unmute` - Unmute replied user
`.archive` - Archive current chat
`.unarchive` - Unarchive current chat

**🔧 Utilities:**
`.weather <city>` - Get weather
`.wiki <query>` - Wikipedia summary
`.define <word>` - Dictionary definition
`.lyrics <song>` - Get song lyrics
`.qr <text>` - Generate QR code
`.shorten <url>` - Shorten URL
`.crypto <coin>` - Cryptocurrency price
`.stock <symbol>` - Stock price
`.yt <query>` - YouTube search link
`.translate <lang> <text>` - Translate text
`.tts <text>` - Text to speech (audio)
`.remind <time> <message>` - Set reminder (time in minutes)
`.poll question|opt1|opt2...` - Create poll
`.timer <seconds>` - Simple timer

**✨ Fun:**
`.mock <text>` - mOcKiNg TeXt
`.vaporwave <text>` - ｖａｐｏｒｗａｖｅ
`.reverse <text>` - Reverse text
`.flip` - Flip a coin
`.choose a,b,c` - Choose randomly
`.rps rock/paper/scissors` - Play Rock Paper Scissors
`.slot` - Slot machine
`.cat` - Random cat picture
`.dog` - Random dog picture
`.fact` - Random fact
`.joke` - Random joke
`.quote` - Random quote
`.anime <query>` - Anime search

**⚙️ System (Owner only):**
`.restart` - Restart bot
`.shutdown` - Stop bot
`.logs [lines]` - Show recent logs
`.eval <code>` - Execute Python code
`.exec <command>` - Execute shell command
`.setvar <key> <value>` - Set persistent variable
`.getvar <key>` - Get persistent variable
`.broadcast <message>` - Send message to all chats

**Other:**
`.id` - Get your ID
`.info [@user]` - Get user info
`.dice` - Roll dice
`.dart` - Throw dart
`.8ball <question>` - Magic 8-ball
`.love` - Love calculator
`.calc <expression>` - Calculator
`.time` - Current time
"""
    try:
        image_file = "kira.jpg"
        if os.path.exists(image_file):
            await client.send_file(event.chat_id, image_file)
        await event.reply(help_text)
    except Exception as e:
        await event.reply(help_text)

# ---------- Chat Management ----------
@client.on(events.NewMessage(pattern=r'^\.mychats$'))
@owner_only
@with_typing(2.0)
async def my_chats_handler(event):
    """Get all your chats from all accounts"""
    try:
        all_chats = await account_manager.get_all_chats(limit=40)
        total_chats = len(all_chats)
        
        if total_chats == 0:
            await event.reply("❌ No chats found.")
            return
        
        account_counts = {}
        for chat in all_chats:
            acc_name = chat['account_name']
            account_counts[acc_name] = account_counts.get(acc_name, 0) + 1
        
        response = f"**📊 Your Chats Summary**\n"
        response += f"**Total chats:** {total_chats}\n\n"
        
        for acc_name, count in account_counts.items():
            response += f"**{acc_name}:** {count} chats\n"
        
        recent_chats = sorted(
            all_chats, 
            key=lambda x: x.get('last_message_date') or datetime.datetime.min, 
            reverse=True
        )[:5]
        
        response += f"\n**🕐 Recent Chats:**\n"
        for i, chat in enumerate(recent_chats, 1):
            title = chat['title'][:20] + '...' if len(chat['title']) > 20 else chat['title']
            emoji = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
            response += f"{i}. {emoji} **{title}**\n"
        
        await event.reply(response)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.listaccounts$'))
@owner_only
@with_typing(1.0)
async def list_accounts_handler(event):
    """List all managed accounts"""
    try:
        if not account_manager.active_accounts:
            await event.reply("❌ No accounts found.")
            return
        
        response = "**👥 Managed Accounts:**\n\n"
        
        for acc_id in account_manager.active_accounts:
            if acc_id in account_manager.accounts:
                account = account_manager.accounts[acc_id]
                response += f"**{account['name']}**\n"
                response += f"• ID: `{acc_id}`\n"
                response += f"• Username: @{account['username']}\n\n"
        
        await event.reply(response)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.backupchats$'))
@owner_only
@with_typing(1.5)
async def backup_chats_handler(event):
    """Backup all chats metadata to database"""
    try:
        msg = await event.reply("💾 Backing up chat metadata...")
        count = await account_manager.sync_chats_to_db()
        await msg.edit(f"✅ Backed up {count} chats to database!")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.exportchats (csv|json)$'))
@owner_only
@with_typing(2.0)
async def export_chats_handler(event):
    """Export chats to CSV or JSON"""
    fmt = event.pattern_match.group(1)
    try:
        msg = await event.reply(f"📤 Exporting chats to {fmt.upper()}...")
        all_chats = await account_manager.get_all_chats(limit=100)
        if not all_chats:
            await msg.edit("❌ No chats to export.")
            return
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if fmt == 'csv':
            filename = f"chats_{timestamp}.csv"
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Account', 'Chat ID', 'Title', 'Username', 'Type', 'Unread', 'Last Active'])
                for chat in all_chats:
                    writer.writerow([
                        chat['account_name'],
                        chat['chat_id'],
                        chat['title'],
                        chat['username'] or '',
                        chat['type'],
                        chat['unread_count'],
                        str(chat.get('last_message_date', ''))
                    ])
            await client.send_file(event.chat_id, filename)
            os.remove(filename)
        elif fmt == 'json':
            filename = f"chats_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_chats, f, default=str, indent=2)
            await client.send_file(event.chat_id, filename)
            os.remove(filename)
        await msg.edit(f"✅ Exported {len(all_chats)} chats to {fmt.upper()}!")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.findchat (.*)'))
@owner_only
@with_typing(2.0)
async def find_chat_handler(event):
    """Search chats by name"""
    query = event.pattern_match.group(1).lower()
    try:
        all_chats = await account_manager.get_all_chats(limit=80)
        found = []
        for chat in all_chats:
            if query in chat['title'].lower() or (chat['username'] and query in chat['username'].lower()):
                found.append(chat)
        if found:
            resp = f"**Found {len(found)} chats:**\n"
            for i, c in enumerate(found[:10], 1):
                resp += f"{i}. **{c['title']}** (Account: {c['account_name']})\n"
            if len(found) > 10:
                resp += f"... and {len(found)-10} more"
            await event.reply(resp)
        else:
            await event.reply("❌ No matching chats.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.chatstats$'))
@owner_only
@with_typing(2.0)
async def chat_stats_handler(event):
    """Show chat statistics"""
    try:
        all_chats = await account_manager.get_all_chats(limit=100)
        total = len(all_chats)
        private = sum(1 for c in all_chats if c['is_user'])
        groups = sum(1 for c in all_chats if c['is_group'])
        channels = sum(1 for c in all_chats if c['is_channel'])
        unread = sum(c['unread_count'] for c in all_chats)
        await event.reply(
            f"**📈 Chat Statistics**\n"
            f"Total chats: {total}\n"
            f"Private: {private}\n"
            f"Groups: {groups}\n"
            f"Channels: {channels}\n"
            f"Unread messages: {unread}"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.chatinfo (.*)'))
@owner_only
@with_typing(2.0)
async def chat_info_handler(event):
    """Detailed info about a chat"""
    identifier = event.pattern_match.group(1)
    try:
        all_chats = await account_manager.get_all_chats(limit=80)
        for chat in all_chats:
            if (str(chat['chat_id']) == identifier or 
                (chat['username'] and chat['username'].lower() == identifier.lower())):
                resp = f"**📄 Chat Info**\n"
                resp += f"Title: {chat['title']}\n"
                resp += f"ID: `{chat['chat_id']}`\n"
                resp += f"Account: {chat['account_name']}\n"
                resp += f"Type: {'Private' if chat['is_user'] else 'Group' if chat['is_group'] else 'Channel'}\n"
                if chat['username']:
                    resp += f"Username: @{chat['username']}\n"
                if chat.get('participants_count'):
                    resp += f"Members: {chat['participants_count']}\n"
                if chat['last_message_date']:
                    resp += f"Last active: {format_timedelta(chat['last_message_date'])}\n"
                await event.reply(resp)
                return
        await event.reply("❌ Chat not found.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.clearchats (\d+)$'))
@owner_only
@with_typing(2.0)
async def clear_chats_handler(event):
    """Find inactive chats older than N days"""
    days = int(event.pattern_match.group(1))
    try:
        all_chats = await account_manager.get_all_chats(limit=100)
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        inactive = []
        for chat in all_chats:
            if chat['last_message_date'] and chat['last_message_date'] < cutoff:
                inactive.append(chat)
        if inactive:
            resp = f"**Inactive chats (> {days} days):**\n"
            for i, c in enumerate(inactive[:10], 1):
                resp += f"{i}. {c['title']} (last: {format_timedelta(c['last_message_date'])})\n"
            if len(inactive) > 10:
                resp += f"... and {len(inactive)-10} more"
            await event.reply(resp)
        else:
            await event.reply("✅ No inactive chats found.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ---------- Profile ----------
@client.on(events.NewMessage(pattern=r'^\.name (.*)'))
@owner_only
@with_typing(1.5)
async def name_handler(event):
    """Change profile name"""
    try:
        names = event.pattern_match.group(1).split(' ', 1)
        first = names[0]
        last = names[1] if len(names) > 1 else ''
        await client(UpdateProfileRequest(first_name=first, last_name=last))
        await event.reply(f"✅ Name changed to **{first} {last}**")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.bio (.*)'))
@owner_only
@with_typing(1.5)
async def bio_handler(event):
    """Change profile bio"""
    try:
        bio = event.pattern_match.group(1)
        await client(UpdateProfileRequest(about=bio))
        await event.reply("✅ Bio updated!")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.setpfp$'))
@owner_only
@with_typing(2.0)
async def setpfp_handler(event):
    """Set profile picture (reply to image)"""
    if not event.is_reply:
        await event.reply("❌ Reply to an image.")
        return
    reply = await event.get_reply_message()
    if reply.photo:
        file = await reply.download_media()
        await client(UploadProfilePhotoRequest(await client.upload_file(file)))
        os.remove(file)
        await event.reply("✅ Profile picture updated!")
    else:
        await event.reply("❌ Reply must be an image.")

@client.on(events.NewMessage(pattern=r'^\.delpfp$'))
@owner_only
@with_typing(1.5)
async def delpfp_handler(event):
    """Delete profile picture"""
    try:
        photos = await client.get_profile_photos('me')
        if photos:
            await client(DeletePhotosRequest(id=[photos[0]]))
            await event.reply("✅ Profile picture deleted.")
        else:
            await event.reply("❌ No profile picture to delete.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.pfp$'))
@owner_only
@with_typing(1.0)
async def pfp_handler(event):
    """Get your profile photo"""
    try:
        photos = await client.get_profile_photos('me')
        if photos:
            await client.send_file(event.chat_id, photos[0])
        else:
            await event.reply("❌ No profile photo.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ---------- Chat Actions ----------
@client.on(events.NewMessage(pattern=r'^\.purge(?:\s+(\d+))?$'))
@owner_only
@with_typing(2.0)
async def purge_handler(event):
    """Delete messages. If reply, delete from that message to current. Else delete last N messages."""
    try:
        if event.is_reply:
            reply = await event.get_reply_message()
            messages = [reply.id]
            async for msg in client.iter_messages(event.chat_id, min_id=reply.id - 1, reverse=True):
                messages.append(msg.id)
            await client(DeleteMessagesRequest(id=messages))
            await event.reply(f"✅ Purged {len(messages)} messages.")
        else:
            n = int(event.pattern_match.group(1) or 10)
            messages = []
            async for msg in client.iter_messages(event.chat_id, limit=n):
                messages.append(msg.id)
            if messages:
                await client(DeleteMessagesRequest(id=messages))
                await event.reply(f"✅ Deleted last {len(messages)} messages.")
            else:
                await event.reply("❌ No messages to delete.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.del$'))
@owner_only
@with_typing(1.0)
async def del_handler(event):
    """Delete replied message"""
    if not event.is_reply:
        await event.reply("❌ Reply to a message.")
        return
    try:
        reply = await event.get_reply_message()
        await reply.delete()
        await event.delete()
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.pin$'))
@owner_only
@with_typing(1.5)
async def pin_handler(event):
    """Pin replied message"""
    if not event.is_reply:
        await event.reply("❌ Reply to a message.")
        return
    try:
        reply = await event.get_reply_message()
        await client(functions.messages.UpdatePinnedMessageRequest(
            peer=event.chat_id,
            id=reply.id,
            silent=False
        ))
        await event.reply("📌 Pinned.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.unpin$'))
@owner_only
@with_typing(1.5)
async def unpin_handler(event):
    """Unpin last pinned message"""
    try:
        await client(functions.messages.UnpinMessagesRequest(
            peer=event.chat_id,
            id=None
        ))
        await event.reply("✅ Unpinned.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.kick$'))
@owner_only
@with_typing(1.5)
async def kick_handler(event):
    """Kick replied user (admin required)"""
    if not event.is_reply:
        await event.reply("❌ Reply to a user.")
        return
    try:
        reply = await event.get_reply_message()
        await client.kick_participant(event.chat_id, reply.sender_id)
        await event.reply("✅ Kicked.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.invite (@\w+)$'))
@owner_only
@with_typing(1.5)
async def invite_handler(event):
    """Invite user by username to current group (admin required)"""
    username = event.pattern_match.group(1)
    try:
        user = await client.get_entity(username)
        await client(InviteToChannelRequest(event.chat_id, [user]))
        await event.reply(f"✅ Invited {username}.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.mute(?:\s+(\d+))?$'))
@owner_only
@with_typing(1.5)
async def mute_handler(event):
    """Mute replied user (duration in minutes, default forever)"""
    if not event.is_reply:
        await event.reply("❌ Reply to a user.")
        return
    minutes = int(event.pattern_match.group(1) or 0)
    try:
        reply = await event.get_reply_message()
        if minutes > 0:
            until_date = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        else:
            until_date = None
            
        rights = ChatBannedRights(
            until_date=until_date,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True
        )
        await client(EditBannedRequest(event.chat_id, reply.sender_id, rights))
        await event.reply(f"✅ Muted {('for '+str(minutes)+' min') if minutes else 'forever'}.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.unmute$'))
@owner_only
@with_typing(1.5)
async def unmute_handler(event):
    """Unmute replied user"""
    if not event.is_reply:
        await event.reply("❌ Reply to a user.")
        return
    try:
        reply = await event.get_reply_message()
        rights = ChatBannedRights(
            until_date=None,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_links=False
        )
        await client(EditBannedRequest(event.chat_id, reply.sender_id, rights))
        await event.reply("✅ Unmuted.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.archive$'))
@owner_only
@with_typing(1.0)
async def archive_handler(event):
    """Archive current chat"""
    try:
        await client.edit_folder(event.chat_id, folder_id=1)  # Archive folder id is 1
        await event.reply("✅ Chat archived.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.unarchive$'))
@owner_only
@with_typing(1.0)
async def unarchive_handler(event):
    """Unarchive current chat"""
    try:
        await client.edit_folder(event.chat_id, folder_id=0)
        await event.reply("✅ Chat unarchived.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ---------- Utilities ----------
@client.on(events.NewMessage(pattern=r'^\.weather (.+)'))
@owner_only
@with_typing(2.0)
async def weather_handler(event):
    """Get weather for a city using wttr.in"""
    city = event.pattern_match.group(1)
    try:
        import requests
        url = f"https://wttr.in/{city}?format=%c+%t+%w+%h&m"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            await event.reply(f"**Weather in {city}:**\n{resp.text.strip()}")
        else:
            await event.reply("❌ Could not fetch weather.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.wiki (.+)'))
@owner_only
@with_typing(2.0)
async def wiki_handler(event):
    """Wikipedia summary"""
    query = event.pattern_match.group(1)
    try:
        import requests
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(query)
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get('extract', 'No summary available.')
            if len(summary) > 1000:
                summary = summary[:1000] + '...'
            await event.reply(f"**{data.get('title', query)}**\n{summary}\n\nRead more: {data.get('content_urls', {}).get('desktop', {}).get('page', '')}")
        else:
            await event.reply("❌ Not found.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.define (.+)'))
@owner_only
@with_typing(2.0)
async def define_handler(event):
    """Dictionary definition using Free Dictionary API"""
    word = event.pattern_match.group(1)
    try:
        import requests
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()[0]
            meanings = data['meanings'][0]
            definition = meanings['definitions'][0]['definition']
            example = meanings['definitions'][0].get('example', 'No example')
            await event.reply(f"**{word}**\n*{meanings['partOfSpeech']}*\n📖 {definition}\n📝 Example: {example}")
        else:
            await event.reply("❌ Word not found.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.lyrics (.+)'))
@owner_only
@with_typing(2.5)
async def lyrics_handler(event):
    """Get song lyrics (using lyrics.ovh)"""
    song = event.pattern_match.group(1)
    try:
        import requests
        url = f"https://api.lyrics.ovh/v1/{song.replace(' ', '%20')}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            lyrics = data['lyrics'][:1000] + ('...' if len(data['lyrics']) > 1000 else '')
            await event.reply(f"**{song}**\n\n{lyrics}")
        else:
            await event.reply("❌ Lyrics not found.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.qr (.+)'))
@owner_only
@with_typing(2.5)
async def qr_handler(event):
    """Generate QR code from text"""
    text = event.pattern_match.group(1)
    try:
        import qrcode
        from io import BytesIO
        img = qrcode.make(text)
        bio = BytesIO()
        bio.name = 'qr.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        await client.send_file(event.chat_id, bio)
    except ImportError:
        await event.reply("❌ qrcode module not installed. Run: pip install qrcode[pil]")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.shorten (.+)'))
@owner_only
@with_typing(2.0)
async def shorten_handler(event):
    """Shorten URL using is.gd"""
    url = event.pattern_match.group(1)
    try:
        import requests
        api = f"https://is.gd/create.php?format=simple&url={urllib.parse.quote(url)}"
        resp = requests.get(api, timeout=10)
        if resp.status_code == 200 and not resp.text.startswith('Error'):
            await event.reply(f"🔗 Shortened: {resp.text.strip()}")
        else:
            await event.reply("❌ Failed to shorten.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.crypto (\w+)'))
@owner_only
@with_typing(2.0)
async def crypto_handler(event):
    """Get cryptocurrency price from CoinGecko"""
    coin = event.pattern_match.group(1).lower()
    try:
        import requests
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,eur,btc&include_24hr_change=true"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and coin in resp.json():
            data = resp.json()[coin]
            usd = data.get('usd', 'N/A')
            eur = data.get('eur', 'N/A')
            btc = data.get('btc', 'N/A')
            change = data.get('usd_24h_change', 0)
            arrow = '📈' if change > 0 else '📉'
            await event.reply(f"**{coin.upper()}**\nUSD: ${usd}\nEUR: €{eur}\nBTC: {btc}\n24h Change: {arrow} {change:.2f}%")
        else:
            await event.reply("❌ Coin not found. Use CoinGecko ID (e.g., bitcoin, ethereum).")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.stock (\w+)'))
@owner_only
@with_typing(2.0)
async def stock_handler(event):
    """Get stock price using yfinance"""
    symbol = event.pattern_match.group(1).upper()
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            change = (data['Close'].iloc[-1] - data['Open'].iloc[-1]) / data['Open'].iloc[-1] * 100
            arrow = '📈' if change > 0 else '📉'
            await event.reply(f"**{symbol}**\nPrice: ${price:.2f}\nChange: {arrow} {change:.2f}%")
        else:
            await event.reply("❌ No data for that symbol.")
    except ImportError:
        await event.reply("❌ yfinance not installed. Run: pip install yfinance")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.yt (.+)'))
@owner_only
@with_typing(1.0)
async def yt_handler(event):
    """YouTube search link"""
    query = event.pattern_match.group(1)
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    await event.reply(f"🔍 YouTube search: [Click here]({search_url})")

@client.on(events.NewMessage(pattern=r'^\.translate (\w{2}) (.+)'))
@owner_only
@with_typing(2.5)
async def translate_handler(event):
    """Translate text to target language (e.g., .translate es hello)"""
    lang = event.pattern_match.group(1)
    text = event.pattern_match.group(2)
    try:
        import requests
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=en|{lang}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            translation = data['responseData']['translatedText']
            await event.reply(f"**Translation ({lang}):**\n{translation}")
        else:
            await event.reply("❌ Translation failed.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.tts (.+)'))
@owner_only
@with_typing(3.0)
async def tts_handler(event):
    """Text to speech using gTTS"""
    text = event.pattern_match.group(1)
    try:
        from gtts import gTTS
        import io
        tts = gTTS(text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.name = 'tts.mp3'
        fp.seek(0)
        await client.send_file(event.chat_id, fp, voice_note=True)
    except ImportError:
        await event.reply("❌ gtts not installed. Run: pip install gtts")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.remind (\d+) (.+)'))
@owner_only
@with_typing(1.0)
async def remind_handler(event):
    """Set a reminder after N minutes"""
    minutes = int(event.pattern_match.group(1))
    message = event.pattern_match.group(2)
    await event.reply(f"⏰ Reminder set for {minutes} minutes.")
    await asyncio.sleep(minutes * 60)
    await event.respond(f"⏰ **Reminder:** {message}")

@client.on(events.NewMessage(pattern=r'^\.poll (.+)'))
@owner_only
@with_typing(2.0)
async def poll_handler(event):
    """Create a poll. Format: .poll Question|Option1|Option2|..."""
    args = event.pattern_match.group(1).split('|')
    if len(args) < 3:
        await event.reply("❌ Usage: .poll Question|Option1|Option2|...")
        return
    question = args[0]
    options = args[1:]
    await client.send_message(event.chat_id, question, poll=options)

@client.on(events.NewMessage(pattern=r'^\.timer (\d+)$'))
@owner_only
@with_typing(1.0)
async def timer_handler(event):
    """Simple timer in seconds"""
    seconds = int(event.pattern_match.group(1))
    msg = await event.reply(f"⏱ Timer set for {seconds} seconds.")
    for i in range(seconds, 0, -1):
        if i % 5 == 0 or i <= 5:
            await msg.edit(f"⏱ {i} seconds remaining...")
        await asyncio.sleep(1)
    await msg.edit("⏰ **Time's up!**")

# ---------- Fun ----------
@client.on(events.NewMessage(pattern=r'^\.mock (.+)'))
@owner_only
@with_typing(1.5)
async def mock_handler(event):
    """Convert text to MoCkInG case"""
    text = event.pattern_match.group(1)
    mocked = ''.join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))
    await event.reply(mocked)

@client.on(events.NewMessage(pattern=r'^\.vaporwave (.+)'))
@owner_only
@with_typing(1.5)
async def vaporwave_handler(event):
    """Convert to fullwidth characters"""
    text = event.pattern_match.group(1)
    fullwidth = ''.join(chr(0xFF00 + (ord(c) - 0x20)) if 0x20 <= ord(c) <= 0x7E else c for c in text)
    await event.reply(fullwidth)

@client.on(events.NewMessage(pattern=r'^\.reverse (.+)'))
@owner_only
@with_typing(1.5)
async def reverse_handler(event):
    """Reverse text"""
    text = event.pattern_match.group(1)
    await event.reply(text[::-1])

@client.on(events.NewMessage(pattern=r'^\.flip$'))
@owner_only
@with_typing(1.0)
async def flip_handler(event):
    """Flip a coin"""
    result = random.choice(['Heads', 'Tails'])
    await event.reply(f"🪙 {result}")

@client.on(events.NewMessage(pattern=r'^\.choose (.+)$'))
@owner_only
@with_typing(1.5)
async def choose_handler(event):
    """Choose randomly from comma-separated list"""
    items = [x.strip() for x in event.pattern_match.group(1).split(',')]
    choice = random.choice(items)
    await event.reply(f"🤔 I choose: **{choice}**")

@client.on(events.NewMessage(pattern=r'^\.rps (.+)$'))
@owner_only
@with_typing(1.5)
async def rps_handler(event):
    """Rock Paper Scissors"""
    user = event.pattern_match.group(1).lower()
    choices = ['rock', 'paper', 'scissors']
    if user not in choices:
        await event.reply("❌ Choose rock, paper, or scissors.")
        return
    bot = random.choice(choices)
    if user == bot:
        result = "It's a tie!"
    elif (user == 'rock' and bot == 'scissors') or (user == 'paper' and bot == 'rock') or (user == 'scissors' and bot == 'paper'):
        result = "You win! 🎉"
    else:
        result = "I win! 🤖"
    await event.reply(f"You: {user}\nMe: {bot}\n\n{result}")

@client.on(events.NewMessage(pattern=r'^\.slot$'))
@owner_only
@with_typing(2.0)
async def slot_handler(event):
    """Slot machine"""
    emojis = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
    spin = [random.choice(emojis) for _ in range(3)]
    result = ' | '.join(spin)
    win = len(set(spin)) == 1
    await event.reply(f"🎰 {result}\n\n{'🎉 JACKPOT!' if win else 'Try again!'}")

@client.on(events.NewMessage(pattern=r'^\.cat$'))
@owner_only
@with_typing(2.0)
async def cat_handler(event):
    """Random cat picture"""
    try:
        import requests
        resp = requests.get('https://api.thecatapi.com/v1/images/search', timeout=10)
        if resp.status_code == 200:
            url = resp.json()[0]['url']
            await client.send_file(event.chat_id, url)
        else:
            await event.reply("❌ Could not fetch cat.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.dog$'))
@owner_only
@with_typing(2.0)
async def dog_handler(event):
    """Random dog picture"""
    try:
        import requests
        resp = requests.get('https://api.thedogapi.com/v1/images/search', timeout=10)
        if resp.status_code == 200:
            url = resp.json()[0]['url']
            await client.send_file(event.chat_id, url)
        else:
            await event.reply("❌ Could not fetch dog.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.fact$'))
@owner_only
@with_typing(1.5)
async def fact_handler(event):
    """Random fact"""
    try:
        import requests
        resp = requests.get('https://uselessfacts.jsph.pl/random.json?language=en', timeout=10)
        if resp.status_code == 200:
            fact = resp.json()['text']
            await event.reply(f"📌 **Did you know?**\n{fact}")
        else:
            await event.reply("❌ Could not fetch fact.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.joke$'))
@owner_only
@with_typing(1.5)
async def joke_handler(event):
    """Random joke"""
    try:
        import requests
        resp = requests.get('https://v2.jokeapi.dev/joke/Any?type=single', timeout=10)
        if resp.status_code == 200:
            joke = resp.json()['joke']
            await event.reply(f"😂 {joke}")
        else:
            await event.reply("❌ Could not fetch joke.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.quote$'))
@owner_only
@with_typing(1.5)
async def quote_handler(event):
    """Random quote"""
    try:
        import requests
        resp = requests.get('https://api.quotable.io/random', timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            await event.reply(f'💬 "{data["content"]}"\n— **{data["author"]}**')
        else:
            await event.reply("❌ Could not fetch quote.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.anime (.+)'))
@owner_only
@with_typing(2.0)
async def anime_handler(event):
    """Search anime info (Jikan API)"""
    query = event.pattern_match.group(1)
    try:
        import requests
        url = f"https://api.jikan.moe/v4/anime?q={urllib.parse.quote(query)}&limit=1"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()['data']
            if data:
                a = data[0]
                msg = f"**{a['title']}** ({a['type']})\n"
                msg += f"⭐ Score: {a['score']} | Episodes: {a['episodes']}\n"
                msg += f"📅 {a.get('aired', {}).get('string', 'N/A')}\n"
                msg += f"📖 {a['synopsis'][:500]}...\n"
                msg += f"🔗 [MyAnimeList]({a['url']})"
                await event.reply(msg)
            else:
                await event.reply("❌ No results.")
        else:
            await event.reply("❌ API error.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ---------- System / Owner only ----------
@client.on(events.NewMessage(pattern=r'^\.restart$'))
@owner_only
@with_typing(1.0)
async def restart_handler(event):
    """Restart the bot"""
    await event.reply("🔄 Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.NewMessage(pattern=r'^\.shutdown$'))
@owner_only
@with_typing(1.0)
async def shutdown_handler(event):
    """Stop the bot"""
    await event.reply("👋 Shutting down...")
    await client.disconnect()
    sys.exit(0)

@client.on(events.NewMessage(pattern=r'^\.logs(?:\s+(\d+))?$'))
@owner_only
@with_typing(2.0)
async def logs_handler(event):
    """Show recent logs (last N lines)"""
    lines = int(event.pattern_match.group(1) or 50)
    try:
        log_file = 'bot.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_lines = f.readlines()[-lines:]
            logs = ''.join(log_lines)[:3500]
            await event.reply(f"**Last {len(log_lines)} lines:**\n```{logs}```")
        else:
            await event.reply("❌ Log file not found.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.eval (.+)'))
@owner_only
@with_typing(2.0)
async def eval_handler(event):
    """Execute Python code (dangerous)"""
    code = event.pattern_match.group(1)
    try:
        result = eval(code)
        await event.reply(f"**Result:** `{result}`")
    except Exception as e:
        await event.reply(f"❌ Error: `{str(e)}`")

@client.on(events.NewMessage(pattern=r'^\.exec (.+)'))
@owner_only
@with_typing(2.0)
async def exec_handler(event):
    """Execute shell command"""
    cmd = event.pattern_match.group(1)
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode() or stderr.decode()
        if not output:
            output = "Command executed (no output)."
        if len(output) > 3500:
            output = output[:3500] + '...'
        await event.reply(f"**Output:**\n```{output}```")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'^\.setvar (\w+) (.+)'))
@owner_only
@with_typing(1.0)
async def setvar_handler(event):
    """Set persistent variable (stored in memory for now)"""
    key = event.pattern_match.group(1)
    value = event.pattern_match.group(2)
    if not hasattr(client, '_vars'):
        client._vars = {}
    client._vars[key] = value
    await event.reply(f"✅ Variable `{key}` set.")

@client.on(events.NewMessage(pattern=r'^\.getvar (\w+)'))
@owner_only
@with_typing(1.0)
async def getvar_handler(event):
    """Get persistent variable"""
    key = event.pattern_match.group(1)
    value = getattr(client, '_vars', {}).get(key, 'Not set')
    await event.reply(f"`{key}` = `{value}`")

@client.on(events.NewMessage(pattern=r'^\.broadcast (.+)'))
@owner_only
@with_typing(3.0)
async def broadcast_handler(event):
    """Send message to all chats (be careful)"""
    msg = event.pattern_match.group(1)
    sent = 0
    failed = 0
    status = await event.reply("📢 Broadcasting...")
    all_chats = await account_manager.get_all_chats(limit=100)
    for chat in all_chats:
        try:
            await client.send_message(chat['chat_id'], msg)
            sent += 1
            await asyncio.sleep(1)
        except:
            failed += 1
    await status.edit(f"✅ Broadcast sent to {sent} chats, failed: {failed}.")

# ---------- Basic info commands ----------
@client.on(events.NewMessage(pattern=r'^\.id$'))
@owner_only
@with_typing(0.5)
async def id_handler(event):
    """Get user/chat ID"""
    try:
        chat = await event.get_chat()
        if event.is_private:
            await event.reply(f'**Your ID:** `{chat.id}`')
        else:
            await event.reply(f'**Chat ID:** `{chat.id}`\n**Your ID:** `{event.sender_id}`')
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

@client.on(events.NewMessage(pattern=r'^\.info(?: (@\w+))?$'))
@owner_only
@with_typing(1.0)
async def info_handler(event):
    """Get user information"""
    try:
        if event.pattern_match.group(1):
            username = event.pattern_match.group(1)
            user = await client.get_entity(username)
        elif event.is_reply:
            reply = await event.get_reply_message()
            user = await client.get_entity(reply.sender_id)
        else:
            user = await client.get_entity(event.sender_id)
        
        info_text = f"""
**👤 User Information:**
**ID:** `{user.id}`
**Name:** `{user.first_name} {user.last_name or ''}`
**Username:** @{user.username if user.username else 'None'}
**Bot:** {'Yes' if user.bot else 'No'}
"""
        await event.reply(info_text)
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

@client.on(events.NewMessage(pattern=r'^\.dice$'))
@owner_only
@with_typing(1.0)
async def dice_handler(event):
    result = random.randint(1, 6)
    await event.reply(f'🎲 Dice roll: **{result}**')

@client.on(events.NewMessage(pattern=r'^\.dart$'))
@owner_only
@with_typing(1.0)
async def dart_handler(event):
    result = random.randint(1, 20)
    await event.reply(f'🎯 Dart score: **{result}**')

@client.on(events.NewMessage(pattern=r'^\.8ball (.*)'))
@owner_only
@with_typing(2.0)
async def eightball_handler(event):
    responses = [
        'It is certain', 'It is decidedly so', 'Without a doubt',
        'Yes definitely', 'As I see it, yes', 'Most likely',
        'Outlook good', 'Yes', 'Signs point to yes',
        'Reply hazy try again', 'Ask again later', 'Better not tell you now',
        'Cannot predict now', 'Concentrate and ask again', 'Don\'t count on it',
        'My reply is no', 'My sources say no', 'Outlook not so good',
        'Very doubtful'
    ]
    await event.reply(f'🎱 **Magic 8-ball says:** {random.choice(responses)}')

@client.on(events.NewMessage(pattern=r'^\.time$'))
@owner_only
@with_typing(0.5)
async def time_handler(event):
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    await event.reply(f'🕐 **Current Time:**\n`{current_time}`')

@client.on(events.NewMessage(pattern=r'^\.calc (.*)'))
@owner_only
@with_typing(1.5)
async def calc_handler(event):
    try:
        expr = event.pattern_match.group(1)
        if any(c in expr for c in ';<>[]{}'):
            await event.reply('Invalid characters!')
            return
        # Use a safe evaluation approach
        allowed_names = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'pow': pow, 'math': math
        }
        result = eval(expr, {"__builtins__": {}}, allowed_names)
        await event.reply(f'🧮 **Result:** `{result}`')
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

@client.on(events.NewMessage(pattern=r'^\.love$'))
@owner_only
@with_typing(2.0)
async def love_handler(event):
    try:
        if event.is_reply:
            reply = await event.get_reply_message()
            user1 = event.sender.first_name or "You"
            user2 = reply.sender.first_name or "Them"
        else:
            user1 = event.sender.first_name or "You"
            user2 = "someone"
        love = random.randint(1, 100)
        hearts = '❤️' * (love // 10) + '🤍' * (10 - love // 10)
        await event.reply(
            f'💖 **Love Calculator** 💖\n\n'
            f'**{user1}** ❤️ **{user2}**\n\n'
            f'Love: **{love}%**\n{hearts}'
        )
    except Exception as e:
        await event.reply(f'Error: {str(e)}')

# Setup AI commands with owner_id
ai_module.setup_ai_commands(client, owner_id)

async def main():
    global owner_id
    print("Connecting to Telegram...")
    await client.start()
    
    me = await client.get_me()
    owner_id = me.id
    print(f"✅ Logged in as: {me.first_name} (@{me.username}) (Owner ID: {owner_id})")
    
    # Update AI module with owner_id
    ai_module.setup_ai_commands(client, owner_id)
    
    # Add main account to manager
    await account_manager.add_account(SESSION_NAME, API_ID, API_HASH, f"{me.first_name} (Main)")
    
    print("\n" + "="*50)
    print("Kira V1 is now running!")
    print("="*50)
    print("\n📱 **Features:**")
    print("• Owner-only commands enforced")
    print("• 50+ commands available")
    print("• Auto-typing enabled")
    print("• AI chat & web search")
    print("="*50)
    
    # Send startup notification to Saved Messages
    try:
        await client.send_message(
            'me',
            f"**Kira V1 Started!** ✅\n\n"
            f"**User:** {me.first_name}\n"
            f"**ID:** `{owner_id}`\n"
            f"**Time:** {datetime.datetime.now().strftime('%H:%M:%S')}\n\n"
            f"Owner-only mode active • 50+ commands"
        )
    except:
        pass
    
    await client.run_until_disconnected()

def run_bot():
    asyncio.run(main())

if __name__ == '__main__':
    print("Please run main.py instead")
