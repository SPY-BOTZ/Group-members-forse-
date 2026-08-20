import os
import logging
from datetime import datetime, timezone, timedelta
from flask import Flask
from threading import Thread

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

# ---------------------------------------------------------------------------
# LOGGING CONFIGURATION
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONFIGURATION & ENVIRONMENT VARIABLES
# ---------------------------------------------------------------------------
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("Missing BOT_TOKEN environment variable!")

PORT = int(os.getenv("PORT", "8000"))

# Telegram Admin ID
ADMIN_USER_IDS = [1249672673] 

# Global dynamic search limit (Default = 4)
CURRENT_SEARCH_LIMIT = 4

# Startup Photo URL
STARTUP_PHOTO_URL = os.getenv("STARTUP_PHOTO_URL", "https://iili.io/CQw1J3X.jpg")

# Bot Username & External Links
BOT_USERNAME = "Group_FsuBbot"
SUPPORT_CHANNEL_URL = "https://t.me/Prime_Movie_YT_Group"
DEVELOPER_URL = "https://t.me/botmaster55"

# ---------------------------------------------------------------------------
# DATABASE SETUP (SQLite via SQLAlchemy)
# ---------------------------------------------------------------------------
Base = declarative_base()

class UserActivity(Base):
    __tablename__ = "user_activity"

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    message_count = Column(Integer, default=0)
    last_reset_date = Column(String, default="")
    restricted_until = Column(DateTime, nullable=True)
    invited_count = Column(Integer, default=0)
    referred_by = Column(Integer, nullable=True)

class GroupSettings(Base):
    __tablename__ = "group_settings"

    chat_id = Column(Integer, primary_key=True)
    custom_welcome = Column(String, nullable=True)

engine = create_engine("sqlite:///bot_database.db", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# ---------------------------------------------------------------------------
# DUMMY WEB SERVER (Koyeb Health Check)
# ---------------------------------------------------------------------------
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Telegram Bot & Admin Panel are running successfully!", 200

def run_web_server():
    app.run(host="0.0.0.0", port=PORT)

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def get_warning_message(user_name, user_id):
    return (
        f"⚠️ **सतর্কতা / Warning**\n\n"
        f"👤 Member: **{user_name}** (`{user_id}`)\n"
        f"👉 আপনি ইতিমধ্যে {CURRENT_SEARCH_LIMIT}টি ফাইল সার্চ করে ফেলেছেন। আনলিমিটেড ব্যবহার করার আগে আপনাকে এই গ্রুপে অন্তত ২ জন মেম্বার যোগ করতে হবে, তবেই আপনি এই গ্রুপে মুভি ফাইল সার্চ করতে পারবেন\n\n🔕অন্যথায় আগামী ৬ ঘণ্টার জন্য আপনার ফাইল সার্চ সুবিধা বন্ধ থাকবে。\n\n"
        f"👉 Sir aapne phale hi {CURRENT_SEARCH_LIMIT} file search ki hai. Unlimited lene se phale aapko is group pe 2 member add karna padega, tabhi aap is group pe movie file search kar sakte ho\n\n🔓Member add na karne par aapki search limit 6 ghante ke liye block kar di jayएगी."
    )

def get_welcome_message(user_name, chat_id):
    session = SessionLocal()
    try:
        setting = session.query(GroupSettings).filter_by(chat_id=chat_id).first()
        if setting and setting.custom_welcome:
            return setting.custom_welcome.format(name=user_name)
    finally:
        session.close()

    return (
        f"👋 **স্বাগতম / Welcome, {user_name}!**\n\n"
        f"🇮🇳 আমাদের গ্রুপে আপনাকে স্বাগতম। দয়া করে গ্রুপের নিয়মকানুন মেনে চলুন এবং মুভি সার্চ করার সময় লিমিট খেয়াল রাখুন।\n\n"
        f"🇮🇳 Welcome to our group! Please follow the rules and enjoy your stay."
    )

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    if user.id in ADMIN_USER_IDS:
        return True
    if chat.type == "private":
        return True
    try:
        member = await chat.get_member(user.id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return False

# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if args and args[0].isdigit():
        referrer_id = int(args[0])
        if referrer_id != user.id:
            session = SessionLocal()
            try:
                user_rec = session.query(UserActivity).filter_by(user_id=user.id).first()
                if not user_rec or not user_rec.referred_by:
                    if not user_rec:
                        user_rec = UserActivity(user_id=user.id, username=user.username or user.first_name, referred_by=referrer_id)
                        session.add(user_rec)
                    else:
                        user_rec.referred_by = referrer_id
                    
                    referrer_rec = session.query(UserActivity).filter_by(user_id=referrer_id).first()
                    if referrer_rec:
                        referrer_rec.invited_count += 1
                    else:
                        session.add(UserActivity(user_id=referrer_id, invited_count=1))
                    session.commit()
            finally:
                session.close()

    start_text = (
        "🤖 **Group Manager & Limit Bot**\n\n"
        "🇧🇩 এই বটটি গ্রুপে ফাইল সার্চ লিমিট ম্যানেজ করতে এবং মেম্বারদের ট্র্যাক করতে সাহায্য করে।\n"
        f"🔗 Your Invite Link: `https://t.me/{BOT_USERNAME}?start={user.id}`\n\n"
        "🇬🇧 This bot helps manage file search limits and referral tracking inside groups."
    )

    keyboard = [
        [
            InlineKeyboardButton("➕ Add To My Group", url=f"https://t.me/Group_FsuBbot?startgroup=true"),
            InlineKeyboardButton("📤 Share Bot", url=f"https://t.me/share/url?url=https://t.me/Group_FsuBbot&text=Check%20out%20this%20awesome%20bot!")
        ],
        [
            InlineKeyboardButton("👨‍💻 Developer", url=DEVELOPER_URL),
            InlineKeyboardButton("📢 Support Channel", url=SUPPORT_CHANNEL_URL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.effective_message.reply_photo(
            photo=STARTUP_PHOTO_URL,
            caption=start_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception:
        await update.effective_message.reply_text(
            start_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        await update.effective_message.reply_text("⚠️ This command can only be used inside a group!")
        return

    if not await is_user_admin(update, context):
        await update.effective_message.reply_text("❌ Sirf group admins ya owner hi is command ka istemal kar sakte hain!")
        return

    target_user_id = None
    if update.effective_message.reply_to_message:
        target_user_id = update.effective_message.reply_to_message.from_user.id
    elif context.args and context.args[0].isdigit():
        target_user_id = int(context.args[0])

    if not target_user_id:
        await update.effective_message.reply_text("⚠️ Usage: Kisi ke message par reply karke `/unmute` likhein ya `/unmute <user_id>` likhein.", parse_mode="Markdown")
        return

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_add_web_page_previews=True
    )

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id, user_id=target_user_id, permissions=permissions
        )
        
        session = SessionLocal()
        try:
            user_rec = session.query(UserActivity).filter_by(user_id=target_user_id).first()
            if user_rec:
                user_rec.restricted_until = None
                user_rec.message_count = 0
                session.commit()
        finally:
            session.close()

        await update.effective_message.reply_text(f"✅ User (`{target_user_id}`) ko successfully unmute kar diya gaya hai!", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to unmute user: {e}")
        await update.effective_message.reply_text(f"⚠️ Unmute karne mein error aayi: {e}")

async def set_welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.effective_message.reply_text("❌ Only admins can change the welcome message!")
        return

    chat = update.effective_chat
    if chat.type == "private":
        await update.effective_message.reply_text("⚠️ This command can only be used inside a group!")
        return

    if not context.args:
        await update.effective_message.reply_text("⚠️ Usage: `/setwelcome Hello {name}, welcome to the group!`", parse_mode="Markdown")
        return

    custom_text = " ".join(context.args)
    session = SessionLocal()
    try:
        setting = session.query(GroupSettings).filter_by(chat_id=chat.id).first()
        if not setting:
            setting = GroupSettings(chat_id=chat.id, custom_welcome=custom_text)
            session.add(setting)
        else:
            setting.custom_welcome = custom_text
        session.commit()
        await update.effective_message.reply_text("✅ Custom welcome message updated successfully!")
    finally:
        session.close()

async def set_limit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_SEARCH_LIMIT
    if not await is_user_admin(update, context):
        await update.effective_message.reply_text("❌ Only admins can change the search limit!")
        return

    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text(f"⚠️ Usage: `/setlimit 5`\nCurrent Limit is: `{CURRENT_SEARCH_LIMIT}`", parse_mode="Markdown")
        return

    CURRENT_SEARCH_LIMIT = int(context.args[0])
    await update.effective_message.reply_text(f"✅ Daily search limit successfully updated to `{CURRENT_SEARCH_LIMIT}`!", parse_mode="Markdown")

    async def user_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = SessionLocal()
    try:
        user_rec = session.query(UserActivity).filter_by(user_id=user.id).first()
        searches = user_rec.message_count if user_rec else 0
        invites = user_rec.invited_count if user_rec else 0

        text = (
            f"👤 **Your Stats / আপনার স্ট্যাটাস**\n\n"
            f"❤️‍🔥 সার্চ করেছেন: `{searches} / {CURRENT_SEARCH_LIMIT}`\n"
            f"❤️‍🔥 সফল ইনভাইট: `{invites}`\n\n"
            f"❤️‍🔥 Searches Used: `{searches} / {CURRENT_SEARCH_LIMIT}`\n"
            f"❤️‍🔥 Successful Invites: `{invites}`"
        )
        await update.effective_message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()

async def top_referrers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        top_users = session.query(UserActivity).order_by(UserActivity.invited_count.desc()).limit(10).all()

        text = "🏆 **Top Referrers / শীর্ষ ইনভাইটারগণ**\n\n"
        for idx, u in enumerate(top_users, 1):
            name = u.username or f"User {u.user_id}"
            text += f"{idx}. **{name}** - 👥 `{u.invited_count}` invites\n"

        if not top_users:
            text += "No referral data available yet."


        await update.effective_message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        total_users = session.query(UserActivity).count()
        now_utc = datetime.now(timezone.utc)
        restricted_users = session.query(UserActivity).filter(UserActivity.restricted_until > now_utc).count()
        
        stats_text = (
            "📊 **বট স্ট্যাটিস্টিক্স / Bot Statistics**\n\n"
            f"🎉 মোট রেজিস্টার্ড ইউজার: `{total_users}`\n"
            f"💥 বর্তমানে রেস্ট্রিক্টেড ইউজার: `{restricted_users}`\n"
            f"⚡ বর্তমান সার্চ লিমিট: `{CURRENT_SEARCH_LIMIT}`\n\n"
            f"💫 Total Registered Users: `{total_users}`\n"
            f"📣 Currently Restricted Users: `{restricted_users}`"
        )
        await update.effective_message.reply_text(stats_text, parse_mode="Markdown")
    finally:
        session.close()

async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.effective_message.reply_text("❌ You are not authorized to use this command!")
        return

    keyboard = [
        [InlineKeyboardButton("📊 View Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        "🎛️ **অ্যাডমিন কন্ট্রোল প্যানেল / Admin Control Panel**", 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_user_admin(update, context):
        await query.edit_message_text("❌ Action denied. Admin privileges required.")
        return

    session = SessionLocal()
    try:
        if query.data == "admin_stats":
            total_users = session.query(UserActivity).count()
            now_utc = datetime.now(timezone.utc)
            restricted_users = session.query(UserActivity).filter(UserActivity.restricted_until > now_utc).count()
            
            await query.edit_message_text(
                f"📊 **Live Panel Stats**\n\nTotal Users: {total_users}\nRestricted: {restricted_users}\nCurrent Limit: {CURRENT_SEARCH_LIMIT}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
            )
        elif query.data == "admin_broadcast_info":
            await query.edit_message_text(
                "📢 **Broadcast Guide**\n\nUse command: `/broadcast Your text here`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
            )
        elif query.data == "admin_refresh" or query.data == "admin_back":
            keyboard = [
                [InlineKeyboardButton("📊 View Stats", callback_data="admin_stats")],
                [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_info")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")]
            ]
            await query.edit_message_text("🎛️ **Admin Control Panel**", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        session.close()

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update, context):
        await update.effective_message.reply_text("❌ Only admins can broadcast.")
        return

    if not context.args:
        await update.effective_message.reply_text("⚠️ Usage: `/broadcast Hello message`", parse_mode="Markdown")
        return

    broadcast_msg = " ".join(context.args)
    session = SessionLocal()
    try:
        users = session.query(UserActivity).all()
        for u in users:
            try:
                await context.bot.send_message(chat_id=u.user_id, text=f"📢 **Announcement:**\n\n{broadcast_msg}", parse_mode="Markdown")
            except Exception:
                pass
        await update.effective_message.reply_text("✅ Broadcast completed successfully!")
    finally:
        session.close()

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        wel_text = get_welcome_message(member.full_name, chat.id)
        await update.message.reply_text(wel_text, parse_mode="Markdown")

async def track_messages_and_enforce_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.from_user or message.from_user.is_bot:
        return

    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return  

    user = message.from_user
    user_id = user.id

    if user_id in ADMIN_USER_IDS:
        return

    username = user.username or user.first_name
    current_utc_date = datetime.now(timezone.utc).strftime("%Y-m-d")

    session = SessionLocal()
    try:
        user_record = session.query(UserActivity).filter_by(user_id=user_id).first()

        if not user_record:
            user_record = UserActivity(
                user_id=user_id,
                username=username,
                message_count=0,
                last_reset_date=current_utc_date,
                restricted_until=None
            )
            session.add(user_record)
            session.commit()

        now_utc = datetime.now(timezone.utc)
        if user_record.restricted_until:
            restricted_until_dt = user_record.restricted_until
            if restricted_until_dt.tzinfo is None:
                restricted_until_dt = restricted_until_dt.replace(tzinfo=timezone.utc)

            if now_utc < restricted_until_dt:
                try:
                    await message.delete()
                except Exception:
                    pass
                return
            else:
                user_record.restricted_until = None
                session.commit()

        if user_record.last_reset_date != current_utc_date:
            user_record.message_count = 0
            user_record.last_reset_date = current_utc_date
            session.commit()

        user_record.message_count += 1
        session.commit()

        current_count = user_record.message_count

        if current_count > CURRENT_SEARCH_LIMIT:
            mute_duration = timedelta(hours=6)
            until_time = now_utc + mute_duration

            # Restricted user can still invite/add members to the group
            permissions = ChatPermissions(
                can_send_messages=False, 
                can_send_audios=False, 
                can_send_documents=False,
                can_send_photos=False, 
                can_send_videos=False, 
                can_send_video_notes=False,
                can_send_voice_notes=False, 
                can_add_web_page_previews=False,
                can_invite_users=True
            )

            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id, user_id=user_id, permissions=permissions, until_date=until_time
                )
                user_record.restricted_until = until_time.replace(tzinfo=None)
                session.commit()

                await message.reply_text(
                    get_warning_message(user.full_name, user_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to restrict user: {e}")

    except Exception as db_error:
        logger.error(f"DB Error: {db_error}")
    finally:
        session.close()

def main():
    server_thread = Thread(target=run_web_server, daemon=True)
    server_thread.start()

    application = ApplicationBuilder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("userstats", user_stats_command))
    application.add_handler(CommandHandler("topreferrers", top_referrers_command))
    application.add_handler(CommandHandler("setwelcome", set_welcome_command))
    application.add_handler(CommandHandler("setlimit", set_limit_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("panel", panel_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CallbackQueryHandler(admin_callback_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(
        MessageHandler(filters.TEXT | filters.Document.ALL | filters.PHOTO | filters.VIDEO, track_messages_and_enforce_limit)
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
            
