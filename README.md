# 🤖 Telegram Ultra Group Manager & Search Limit Bot

<p align="center">
  <img src="https://iili.io/CQw1J3X.jpg" alt="Bot Banner" width="600" style="border-radius: 10px;">
</p>

<p align="center">
  <b>A powerful, feature-rich Telegram bot designed for groups to manage file search limits, track referrals, and automate member administration seamlessly.</b>
</p>

---

## 🚀 Ultra Features

* **⚡ Dynamic Search Limiting:** Automatically monitors and restricts members after a specific number of searches (default is 4 searches, customisable on the fly).
* **⏳ Smart Auto-Mute Engine:** Automatically mutes rule-breaking members for **6 hours** upon hitting their limit, complete with an instant alert replying directly with their Name and User ID.
* **👑 Admin & Owner `/unmute` Control:** Group admins and owners can instantly restore full messaging permissions for any muted member via command or message reply.
* **👥 Advanced Referral Tracking (`/topreferrers`):** Automatically tracks unique invite links (`?start=USER_ID`) to count successful member additions and showcases a **Top 10 Leaderboard**.
* **⚙️ Dynamic Limit Configuration (`/setlimit`):** Admins can adjust the daily search limit dynamically without needing to restart or redeploy the bot.
* **👋 Custom Welcome Messages (`/setwelcome`):** Groups can set personalized welcome greetings dynamically formatted with the new member's name.
* **🎛️ Interactive Admin Panel:** Clean inline keyboard interface for admins to check live bot statistics and broadcast announcements.
* **🌐 Web Health-Check Integration:** Built-in lightweight Flask web server to ensure 24/7 uptime on cloud hosts like Koyeb, Render, or Railway.

---

## 🛠️ Bot Commands

| Command | Description | Permission |
| :--- | :--- | :--- |
| `/start` | Starts the bot and displays the main menu with quick action buttons. | All Users |
| `/userstats` | View your personal search usage and successful invite count. | All Users |
| `/topreferrers` | Displays the top 10 members with the highest successful referrals. | All Users |
| `/unmute` | Unmutes/un-restricts a restricted user (via reply or user ID). | Group Admins / Owner |
| `/setlimit <number>` | Dynamically updates the daily search limit per group. | Group Admins / Owner |
| `/setwelcome <text>` | Sets a custom welcome message for new members joining the group. | Group Admins / Owner |
| `/panel` | Opens the interactive admin dashboard for quick stats and guides. | Bot Admins |
| `/broadcast <msg>` | Broadcasts an announcement message to all registered bot users. | Bot Admins |
| `/stats` | View overall system statistics (total users, restricted count, etc.). | All Users |

---

## 📋 Inline Interactive Buttons

When users trigger the `/start` command, they are greeted with a rich UI containing 4 quick action buttons:
1. **➕ Add To My Group:** Quick install link to deploy the bot into your groups.
2. **📤 Share Bot:** Instantly share the bot link with friends and networks.
3. **👨‍💻 Developer:** Direct contact link to the developer/maintainer.
4. **📢 Support Channel:** Official updates and community support channel link.

---

## 📦 Environment Variables

Make sure to set the following environment variables on your hosting platform:

* `BOT_TOKEN`: Your Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather).
* `PORT`: Port for the Flask health-check server (default: `8000`).
* `STARTUP_PHOTO_URL`: Direct image link used for the `/start` command banner.

---

## ⚙️ Local Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
   cd your-repo-name

   
