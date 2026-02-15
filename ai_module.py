#!/usr/bin/env python3
"""
Kira V1 - AI Module
AI chat and web search functionality with owner check
"""

import random
import asyncio
import urllib.parse
from telethon import events

client = None
owner_id = None

# Simple AI responses
AI_RESPONSES = {
    "hello": ["Hello!", "Hi there!", "Hey! How can I help?", "Greetings!"],
    "how are you": ["I'm doing great!", "All systems operational!", "Ready to help!", "Feeling chatty!"],
    "who are you": ["I'm Kira V1, your Telegram assistant!", "Kira V1 - Created by Thomas Samuel", "Your friendly neighborhood bot!"],
    "what can you do": ["I can search the web, manage chats, and more! Try .help"],
    "thanks": ["You're welcome!", "Happy to help!", "Anytime!", "My pleasure!"],
    "bye": ["Goodbye!", "See you later!", "Take care!", "Bye! 👋"]
}

async def ai_typing(event, delay=1.5):
    async with event.client.action(event.chat_id, 'typing'):
        await asyncio.sleep(delay)

def get_ai_response(message_text):
    message_lower = message_text.lower()
    for key, responses in AI_RESPONSES.items():
        if key in message_lower:
            return random.choice(responses)
    default_responses = [
        "Interesting! Tell me more.",
        "I see. What else?",
        "That's cool!",
        "Thanks for sharing!",
        "I'm listening...",
        "Got it!"
    ]
    return random.choice(default_responses)

def setup_ai_commands(bot_client, owner):
    global client, owner_id
    client = bot_client
    owner_id = owner

    @client.on(events.NewMessage(pattern=r'^\.ai (.*)'))
    async def ai_chat_handler(event):
        if event.sender_id != owner_id:
            return
        query = event.pattern_match.group(1)
        await ai_typing(event, 2.0)
        response = get_ai_response(query)
        await event.reply(random.choice([f"🤖 {response}", f"💭 {response}", f"✨ {response}"]))

    @client.on(events.NewMessage(pattern=r'^\.(google|search) (.*)'))
    async def web_search_handler(event):
        if event.sender_id != owner_id:
            return
        query = event.pattern_match.group(2)
        await ai_typing(event, 1.5)
        try:
            import requests
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()
            if data.get('AbstractText'):
                result = f"**🔎 {query}**\n\n{data['AbstractText']}\n"
                if data.get('AbstractSource'):
                    result += f"\n📚 Source: {data['AbstractSource']}"
                if data.get('AbstractURL'):
                    result += f"\n🔗 [Read more]({data['AbstractURL']})"
                await event.reply(result)
            elif data.get('RelatedTopics'):
                topics = data['RelatedTopics'][:5]
                result = f"**🔎 Search results for:** `{query}`\n\n"
                for i, t in enumerate(topics, 1):
                    if isinstance(t, dict):
                        result += f"{i}. **{t.get('Text', '')[:100]}**\n"
                await event.reply(result)
            else:
                google = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                await event.reply(f"**🔎 No instant results.**\n[Search Google]({google})")
        except Exception as e:
            await event.reply(f"❌ Search error: {str(e)}")
