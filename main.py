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

# Optional: Define your admin user IDs here as integers (comma-separated or hardcoded list)
# You can also use context.bot.get_chat_administrators dynamically for group admins.
ADMIN_USER_IDS = [] 

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
# HELPER FUNCTIONS (Dual Language Formats: Bangla on Top, English Below)
# ---------------------------------------------------------------------------
def get_warning_message():
    return (
        "⚠️ **সতর্কতা / Warning**\n\n"
        "🇧🇩 আপনি ইতিমধ্যে ৪টি ফাইল সার্চ করে ফেলেছেন। আনলিমিটেড ব্যবহার করার আগে আপনাকে এই গ্রুপে অন্তত ২ জন মেম্বার যোগ করতে হবে, তবেই আপনি এই গ্রুপে মুভি ফাইল সার্চ করতে পারবেন।\n\n"
        "🇬🇧 Sir aapne phale hi 4 file search ki hai. Unlimited lene se phale aapko is group pe 2 member add karna padega, tabhi aap is group pe movie file search kar sakte ho."
    )

def get_welcome_message(user_name):
    return (
        f"👋 **স্বাগতম / Welcome, {user_name}!**\n\n"
        f"🇧🇩 আমাদের গ্রুপে আপনাকে স্বাগতম। দয়া করে গ্রুপের নিয়মকানুন মেনে চলুন এবং মুভি সার্চ করার সময় লিমিট খেয়াল রাখুন।\n\n"
        f"🇬🇧 Welcome to our group! Please follow the rules and enjoy your stay."
    )

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if the user is an administrator of the chat."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    if chat.type == "private":
        return True # Private chat with bot can be treated as admin context if needed
    try:
        member = await chat.get_member(user.id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return False

# ---------------------------------------------------------------------------
# BOT COMMAND HANDLERS: STATS & ADMIN PANEL
# ---------------------------------------------------------------------------
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows global statistics of the bot / group."""
    session = SessionLocal()
    try:
        total_users = session.query(UserActivity).count()
        now_utc = datetime.now(timezone.utc)
        restricted_users = session.query(UserActivity).filter(UserActivity.restricted_until > now_utc).count()
        
        stats_text = (
            "📊 **বট স্ট্যাটিস্টিক্স / Bot Statistics**\n\n"
            f"🇧🇩 মোট রেজিস্টার্ড ইউজার: `{total_users}`\n"
            f"🇧🇩 বর্তমানে রেস্ট্রিক্টেড ইউজার: `{restricted_users}`\n\n"
            f"🇬🇧 Total Registered Users: `{total_users}`\n"
            f"🇬🇧 Currently Restricted Users: `{restricted_users}`"
        )
        await update.effective_message.reply_text(stats_text, parse_mode="Markdown")
    finally:
        session.close()

async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Interactive Admin Panel for group/bot managers."""
    if not await is_user_admin(update, context):
        await update.effective_message.reply_text(
            "❌ আপনার এই কমান্ডটি ব্যবহার করার অনুমতি নেই!\n"
            "❌ You are not authorized to use this admin panel command!"
        )
        return

    keyboard = [
        [InlineKeyboardButton("📊 View Stats / স্ট্যাটাস", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast / ব্রডকাস্ট", callback_data="admin_broadcast_info")],
        [InlineKeyboardButton("🔄 Refresh DB / রিফ্রেশ", callback_data="admin_refresh")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    panel_text = (
        "🎛️ **অ্যাডমিন কন্ট্রোল প্যানেল / Admin Control Panel**\n\n"
        "🇧🇩 নিচে দেওয়া অপশনগুলো থেকে ম্যানেজ করুন:\n"
        "🇬🇧 Manage your bot using the options below:"
    )
    await update.effective_message.reply_text(panel_text, reply_markup=reply_markup, parse_mode="Markdown")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline buttons clicks for the admin panel."""
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
                f"📊 **Live Panel Stats**\n\n"
                f"Total Users Tracked: {total_users}\n"
                f"Currently Muted/Restricted: {restricted_users}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
            )
        elif query.data == "admin_broadcast_info":
            await query.edit_message_text(
                "📢 **Broadcast Guide**\n\n"
                "To broadcast a message to all users, use command:\n"
                "`/broadcast Your message text here`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
            )
        elif query.data == "admin_refresh" or query.data == "admin_back":
            keyboard = [
                [InlineKeyboardButton("📊 View Stats / স্ট্যাটাস", callback_data="admin_stats")],
                [InlineKeyboardButton("📢 Broadcast / ব্রডকাস্ট", callback_data="admin_broadcast_info")],
                [InlineKeyboardButton("🔄 Refresh DB / রিফ্রেশ", callback_data="admin_refresh")]
            ]
            await query.edit_message_text(
                "🎛️ **অ্যাডমিন কন্ট্রোল প্যানেল / Admin Control Panel**",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    finally:
        session.close()

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcasts a message to all tracked users in the database."""
    if not await is_user_admin(update, context):
        await update.effective_message.reply_text("❌ Only admins can trigger broadcasts.")
        return

    if not context.args:
        await update.effective_message.reply_text("⚠️ Please provide text to broadcast. Example: `/broadcast Hello everyone!`", parse_mode="Markdown")
        return

    broadcast_msg = " ".join(context.args)
    session = SessionLocal()
    try:
        users = session.query(UserActivity).all()
        success_count = 0
        fail_count = 0

        status_msg = await update.effective_message.reply_text("📢 Broadcasting message... Please wait.")

        for u in users:
            try:
                await context.bot.send_message(chat_id=u.user_id, text=f"📢 **Announcement / ঘোষণা:**\n\n{broadcast_msg}", parse_mode="Markdown")
                success_count += 1
            except Exception:
                fail_count += 1

        await status_msg.edit_text(f"✅ Broadcast Complete!\n\nSuccessful: {success_count}\nFailed: {fail_count}")
    finally:
        session.close()

# ---------------------------------------------------------------------------
# WELCOME NEW MEMBERS HANDLER
# ---------------------------------------------------------------------------
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a dual-language welcome message when new members join the group."""
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        welcome_text = get_welcome_message(member.full_name)
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

# ---------------------------------------------------------------------------
# CORE TRACKING & RESTRICTION MIDDLEWARE
# ---------------------------------------------------------------------------
async def track_messages_and_enforce_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tracks messages, handles 4-file search limits, mutes on 5th message."""
    message = update.effective_message
    if not message or not message.from_user or message.from_user.is_bot:
        return

    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return

    user = message.from_user
    user_id = user.id
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
        else:
            user_record.username = username
            session.commit()

        # Check restriction expiration
        now_utc = datetime.now(timezone.utc)
        if user_record.restricted_until:
            restricted_until_dt = user_record.restricted_until
            if restricted_until_dt.tzinfo is None:
                restricted_until_dt = restricted_until_dt.replace(tzinfo=timezone.utc)

            if now_utc < restricted_until_dt:
                try:
                    await message.delete()
                except Exception as e:
                    logger.warning(f"Could not delete message for restricted user {user_id}: {e}")
                return
            else:
                user_record.restricted_until = None
                session.commit()

        # Reset count on new calendar day
        if user_record.last_reset_date != current_utc_date:
            user_record.message_count = 0
            user_record.last_reset_date = current_utc_date
            session.commit()

        # Increment message/search count
        user_record.message_count += 1
        session.commit()

        current_count = user_record.message_count
        logger.info(f"User {user_id} daily count: {current_count}")

        # Enforce mute on 5th message
        if current_count > 4:
            mute_duration = timedelta(hours=24)
            until_time = now_utc + mute_duration

            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )

            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user_id,
                    permissions=permissions,
                    until_date=until_time
                )

                user_record.restricted_until = until_time.replace(tzinfo=None)
                session.commit()

                # Reply with dual-language warning message
                await message.reply_text(get_warning_message(), parse_mode="Markdown")
                logger.info(f"Restricted user {user_id} for 24 hours.")

            except Exception as e:
                logger.error(f"Failed to restrict user {user_id}: {e}")
                await message.reply_text(
                    "⚠️ **Permission Error / অনুমতি ত্রুটি**\n\n"
                    "🇧🇩 আপনার সীমা শেষ হয়েছে, কিন্তু বটকে অ্যাডমিন করা না থাকায় আমি আপনাকে রেস্ট্রিক্ট করতে পারছি না!\n"
                    "🇬🇧 You crossed the limit, but I lack admin permissions to restrict you!",
                    parse_mode="Markdown"
                )

    except Exception as db_error:
        logger.error(f"Database error: {db_error}")
    finally:
        session.close()

# ---------------------------------------------------------------------------
# MAIN APPLICATION INITIALIZATION
# ---------------------------------------------------------------------------
def main():
    # Start web server thread for Koyeb health check
    server_thread = Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logger.info(f"Flask health-check server started on port {PORT}")

    # Build bot application
    application = ApplicationBuilder().token(API_TOKEN).build()

    # Handlers setup
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("panel", panel_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CallbackQueryHandler(admin_callback_handler))
    
    # Welcome new member handler
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    
    # Message tracking handler
    application.add_handler(
        MessageHandler(filters.TEXT | filters.Document.ALL | filters.PHOTO | filters.VIDEO, track_messages_and_enforce_limit)
    )

    logger.info("Starting upgraded multilingual Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
  
