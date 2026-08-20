# 🤖 Advanced Telegram Group Manager & Limit Bot

A production-ready Telegram bot built using `python-telegram-bot` (v20+ async) and SQLAlchemy (SQLite). Designed specifically for group management, file search tracking, automatic muting/restrictions, dual-language support (Bangla & English), interactive admin panels, and seamless deployment on **Koyeb** or other cloud platforms.

---

## ✨ Features

1. **Daily File Search & Message Limit:** 
   - Tracks text messages and file searches per member per calendar day (UTC).
   - If a user crosses **4 messages/searches**, the 5th message triggers an automatic **24-hour mute/restriction**.
2. **Dual-Language Responses (Bangla & English):**
   - All warnings, notifications, and welcome messages are presented with **Bangla on top** and **English below it**.
3. **Group Welcome Greetings:**
   - Automatically welcomes new members as soon as they join the group.
4. **Interactive Admin Panel (`/panel`):**
   - An intuitive inline-keyboard menu for administrators to check stats and get system configurations.
5. **Global Statistics (`/stats`):**
   - Live data showing total registered users and currently restricted users.
6. **Broadcast Feature (`/broadcast`):**
   - Allows admins to push announcements directly to all tracked users simultaneously.
7. **Database Persistence:**
   - Uses **SQLite** via SQLAlchemy so that user tracking counts, timestamps, and restriction states are preserved across bot restarts.
8. **Koyeb Ready:**
   - Includes a built-in lightweight Flask health-check web server to fulfill web-service requirements on hosting platforms like Koyeb.

---

## 📂 Project Structure

```text
├── main.py             # Core bot application & Flask health server
├── requirements.txt    # Python dependencies
├── README.md           # Documentation & Deployment Guide
└── bot_database.db     # SQLite database (auto-generated on first run)
