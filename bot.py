import logging
import re
import secrets
import string
import asyncio
from urllib.parse import urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
import database as db

# ============ الإعدادات ============
BOT_TOKEN = "8670627875:AAGScMvzRFgBHb6ARdVGGIp27oNm0Ywmdq8"
DEVELOPER_ID = 8772508181
DEVELOPER_NAME = "𝑬𝑳𝑩𝑨𝑩𝑨 𝑬𝑳𝑮𝑬𝑵𝑬𝑹𝑨𝑳"
DEVELOPER_USERNAME = "@ELBABAELGRNERAL"
BOT_USERNAME = "YourBotUsername"  # ← غيّرها لليوزرنيم البوت بدون @

FOOTER = f"\n\n━━━━━━━━━━━━━━━━━━\n👨‍💻 {DEVELOPER_NAME}\n📩 {DEVELOPER_USERNAME}"

logging.basicConfig(level=logging.INFO)
db.init_db()

# ============ محتوى ============
GENERAL_TIPS = (
    "🛡️ *نصائح لحماية نفسك:*\n\n"
    "1️⃣ كلمة مرور قوية وفريدة لكل حساب (12-15 حرف).\n\n"
    "2️⃣ فعّل التحقق بخطوتين (2FA).\n\n"
    "3️⃣ احذر روابط التصيد.\n\n"
    "4️⃣ استخدم مدير كلمات مرور.\n\n"
    "5️⃣ راجع الأجهزة المتصلة.\n\n"
    "6️⃣ لا تشارك OTP مع أي شخص.\n\n"
    "7️⃣ حدّث تطبيقاتك باستمرار."
)

SYSTEM_GUIDES = {
    "google": "🔐 *حماية Google:*\n\n• فعّل 2FA من الإعدادات > الأمان.\n• استخدم Google Authenticator.\n• راجع الأجهزة والتطبيقات.",
    "tiktok": "🔐 *حماية TikTok:*\n\n• فعّل 2FA من الإعدادات > الأمان.\n• لا تشارك كود التحقق.\n• راجع الأجهزة المسجلة.",
    "instagram": "🔐 *حماية Instagram:*\n\n• فعّل المصادقة الثنائية.\n• استخدم تطبيق مصادقة.\n• راجع نشاط تسجيل الدخول.",
    "facebook": "🔐 *حماية Facebook:*\n\n• فعّل 2FA من الأمان.\n• راجع الأجهزة المتصلة.\n• احذر رسائل التصيد.",
    "whatsapp": "🔐 *حماية WhatsApp:*\n\n• فعّل 2FA من الإعدادات > الحساب.\n• لا تشارك كود التحقق.\n• فعّل قفل بصمة.",
    "telegram": "🔐 *حماية Telegram:*\n\n• فعّل 2FA من الخصوصية والأمان.\n• فعّل قفل التطبيق.\n• راجع الأجهزة النشطة.",
}

# ============ محرك تحليل اليوزرنيم ============
COMMON_WORDS = {"admin","user","test","guest","root","login","account","ahmed","mohamed","ali","omar","sara","nour","hassan","egypt","cairo","alex","king","queen","master","boss","love","cool","pro","super","dark","light"}
COMMON_SEQ = ["123","1234","12345","111","000","abc","qwerty","asdf"]

def analyze_username_security(username):
    u = username.strip()
    ul = u.lower()
    reasons, tips = [], []
    score = 0
    length = len(u)
    if length >= 12: score += 30
    elif length >= 9: score += 22
    elif length >= 6:
        score += 14; tips.append("زد الطول لـ 9 أحرف على الأقل.")
    else:
        score += 4; reasons.append(f"⚠️ قصير ({length} أحرف) — سهل تخمينه.")
    has_lower = bool(re.search(r"[a-z]", u))
    has_upper = bool(re.search(r"[A-Z]", u))
    has_digit = bool(re.search(r"\d", u))
    has_symbol = bool(re.search(r"[._\-]", u))
    if has_lower and has_upper: score += 15
    else: tips.append("اخلط بين حروف كبيرة وصغيرة (Aa).")
    if has_digit: score += 10
    else: tips.append("أضف أرقام (بدون تسلسل).")
    if has_symbol: score += 10
    else: tips.append("أضف رمز `_` أو `.` أو `-`.")
    if any(w in ul for w in COMMON_WORDS):
        score -= 20; reasons.append("⚠️ يحتوي على كلمة شائعة (admin, ahmed...).")
    if any(s in ul for s in COMMON_SEQ):
        score -= 20; reasons.append("⚠️ يحتوي على تسلسل (123، abc).")
    if re.search(r"(.)\1{2,}", u):
        score -= 10; reasons.append("⚠️ حرف مكرر 3+ مرات.")
    if re.search(r"(19|20)\d{2}", u):
        score -= 10; reasons.append("⚠️ يبدو فيه سنة ميلاد.")
    if u[0].isdigit() or u[-1].isdigit():
        score -= 5; tips.append("ابدأ وانتهي بحرف مش رقم.")
    if " " in u:
        score -= 10; reasons.append("⚠️ فيه مسافات.")
    score = max(0, min(score, 100))
    if score >= 70:
        level = "🟢 قوي"; decision = "✅ *الحساب ده قوي.* لا داعي لتغييره."
    elif score >= 45:
        level = "🟡 متوسط"; decision = "⚠️ *الحساب متوسط.* يفضل تغييره."
    else:
        level = "🔴 ضعيف"; decision = "🚨 *الحساب ده سهل اختراقه.* غيّره فورًا!"
    if not reasons: reasons.append("✅ مفيش علامات خطر.")
    if not tips: tips.append("✅ ممتاز!")
    return score, level, decision, reasons, tips

# ============ فحص كلمة المرور ============
def analyze_password_strength(pwd):
    score = 0
    reasons, tips = [], []
    length = len(pwd)
    if length >= 16: score += 30
    elif length >= 12: score += 22
    elif length >= 8: score += 12
    else:
        score += 3; reasons.append(f"⚠️ قصيرة ({length} حرف).")
    if re.search(r"[a-z]", pwd) and re.search(r"[A-Z]", pwd): score += 15
    else: tips.append("اخلط حروف كبيرة وصغيرة.")
    if re.search(r"\d", pwd): score += 10
    else: tips.append("أضف أرقام.")
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};:,.<>?/\\|`~]", pwd): score += 15
    else: tips.append("أضف رموز (!@#$).")
    if re.search(r"(.)\1{2,}", pwd):
        score -= 10; reasons.append("⚠️ حروف مكررة.")
    if any(s in pwd.lower() for s in ["123","abc","qwerty","password","admin","111","000"]):
        score -= 25; reasons.append("⚠️ كلمة شائعة أو تسلسل.")
    if re.search(r"(19|20)\d{2}", pwd):
        score -= 10; reasons.append("⚠️ فيه سنة.")
    score = max(0, min(score, 100))
    # تخمين وقت الاختراق
    charset = 0
    if re.search(r"[a-z]", pwd): charset += 26
    if re.search(r"[A-Z]", pwd): charset += 26
    if re.search(r"\d", pwd): charset += 10
    if re.search(r"[^a-zA-Z0-9]", pwd): charset += 32
    if charset == 0: charset = 26
    import math
    try:
        combinations = charset ** length
        guesses_per_sec = 1e10  # 10 مليار/ثانية
        seconds = combinations / guesses_per_sec / 2
    except:
        seconds = 0
    if seconds < 60: time_str = "⚡ فورًا (أقل من دقيقة)"
    elif seconds < 3600: time_str = f"⏱️ {int(seconds/60)} دقيقة"
    elif seconds < 86400: time_str = f"🕐 {int(seconds/3600)} ساعة"
    elif seconds < 31536000: time_str = f"📅 {int(seconds/86400)} يوم"
    elif seconds < 31536000*1000: time_str = f"📆 {int(seconds/31536000)} سنة"
    elif seconds < 31536000*1e9: time_str = f"🌌 {int(seconds/31536000/1e6)} مليون سنة"
    else: time_str = "🌠 ملايين السنين"
    if score >= 70: level = "🟢 قوية جدًا"
    elif score >= 45: level = "🟡 متوسطة"
    else: level = "🔴 ضعيفة"
    if not reasons: reasons.append("✅ مفيش علامات ضعف.")
    if not tips: tips.append("✅ ممتاز!")
    return score, level, time_str, reasons, tips

# ============ مولّد كلمات المرور ============
def generate_password(length=16, easy=False):
    if easy:
        words = ["Tiger","Rocket","Coffee","Sunset","Panda","Ninja","Dragon","Storm","Ocean","Moon","Fire","Cloud","River","Star","Falcon","Wolf"]
        p1, p2, p3 = secrets.choice(words), secrets.choice(words), secrets.choice(words)
        num = secrets.randbelow(100)
        sym = secrets.choice("!@#$%&*")
        return f"{p1}-{p2}-{p3}-{num}{sym}"
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return "".join(secrets.choice(alphabet) for _ in range(length))

# ============ فحص الروابط المشبوهة ============
SUSPICIOUS_KEYWORDS = ["login","verify","secure","update","account","confirm","free","winner","claim","prize","urgent","signin","wallet","bonus","gift"]
SHORTENERS = ["bit.ly","tinyurl.com","goo.gl","t.co","ow.ly","is.gd","buff.ly","rb.gy","cutt.ly"]
LOOKALIKE_PATTERNS = [
    (r"g[o0]{2}gle", "Google"),
    (r"faceb[o0]{2}k", "Facebook"),
    (r"whatsap{1,2}", "WhatsApp"),
    (r"instagr[ae]m", "Instagram"),
    (r"tik{1,2}tok", "TikTok"),
    (r"telegr[ae]m", "Telegram"),
    (r"paypa[1l]", "PayPal"),
    (r"amaz[o0]n", "Amazon"),
]
DANGEROUS_TLDS = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".work", ".click"]

def analyze_link(url):
    url_l = url.lower().strip()
    if not url_l.startswith(("http://", "https://")):
        url_l = "http://" + url_l
    try:
        parsed = urlparse(url_l)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
    except:
        return 0, "⚠️ مشبوه", ["رابط غير صالح."], ["تأكد من الرابط."]
    risk = 0
    reasons, tips = [], []
    # IP بدل دومين
    if re.match(r"^\d+\.\d+\.\d+\.\d+", host):
        risk += 40; reasons.append("⚠️ الدومين عنوان IP — علامة خطيرة.")
    # اختصارات
    if any(s in host for s in SHORTENERS):
        risk += 20; reasons.append("⚠️ رابط مختصر — ممكن يخفي وجهة خطيرة.")
    # كلمات مشبوهة
    found_kw = [k for k in SUSPICIOUS_KEYWORDS if k in url_l]
    if found_kw:
        risk += 15; reasons.append(f"⚠️ كلمات مشبوهة: {', '.join(found_kw)}.")
    # تقليد ماركات
    for pattern, brand in LOOKALIKE_PATTERNS:
        if re.search(pattern, host) and brand.lower().replace(" ","") not in host:
            risk += 25; reasons.append(f"⚠️ يحاول تقليد {brand}.")
            break
    # امتدادات خطيرة
    for tld in DANGEROUS_TLDS:
        if host.endswith(tld):
            risk += 15; reasons.append(f"⚠️ امتداد خطير ({tld}).")
            break
    # HTTPS
    if parsed.scheme != "https":
        risk += 10; reasons.append("⚠️ الرابط مش HTTPS.")
    # شرطات كتيرة
    if host.count("-") >= 3:
        risk += 10; reasons.append("⚠️ شرطات كثيرة في الدومين.")
    # طول غريب
    if len(host) > 30:
        risk += 5; reasons.append("⚠️ دومين طويل بشكل غريب.")
    risk = max(0, min(risk, 100))
    if risk >= 60:
        level = "🚨 خطير جدًا — لا تضغط!"
        tips.append("🚫 لا تفتح الرابط نهائيًا.")
    elif risk >= 30:
        level = "⚠️ مشبوه — تجنب الضغط"
        tips.append("افتح الموقع الرسمي بنفسك من المتصفح.")
    else:
        level = "✅ آمن نسبيًا"
        tips.append("لو مش متأكد، لا تدخل بياناتك.")
    if not reasons: reasons.append("✅ مفيش علامات خطر واضحة.")
    return risk, level, reasons, tips

# ============ اختبار الوعي ============
QUIZ_QUESTIONS = [
    {"q":"جالك إيميل من 'البنك' يقولك اضغط على لينك لتحديث بياناتك، تعمل إيه؟",
     "options":["أضغط على اللينك فورًا","أتجاهل الإيميل وأدخل على موقع البنك بنفسي","أرد على الإيميل وأطلب تأكيد"],
     "correct":1},
    {"q":"صاحبك بعتلك لينك على واتساب يقولك 'شوف الصورة دي'، تعمل إيه؟",
     "options":["أفتحها فورًا","أسأله الأول لو هو بعت اللينك فعلاً","أشاركها مع أصدقائي"],
     "correct":1},
    {"q":"حد اتصل بيك يقول إنه من الدعم الفني وبيطلب كود OTP، تعمل إيه؟",
     "options":["أديله الكود","أرفض وأقفل الخط","أديله جزء من الكود"],
     "correct":1},
    {"q":"كلمة المرور 'Ahmed@2024'، إيه رأيك فيها؟",
     "options":["قوية جدًا","متوسطة — يفضل تغييرها","ضعيفة جدًا"],
     "correct":1},
    {"q":"إيه أفضل طريقة لحماية حسابك؟",
     "options":["كلمة مرور بسيطة عشان مفتكرهاش","كلمة مرور قوية + 2FA","نفس الباسورد لكل حساباتي"],
     "correct":1},
]

# ============ نظام النقاط والمستويات ============
def get_level(points):
    if points >= 300: return "🛡️ محترف"
    if points >= 150: return "🦅 خبير"
    if points >= 50: return "🐣 متوسط"
    return "🥚 مبتدئ"

def get_next_level_points(points):
    if points < 50: return 50
    if points < 150: return 150
    if points < 300: return 300
    return None

# ============ القوائم ============
def main_menu(is_dev=False):
    rows = [
        [InlineKeyboardButton("🔍 فحص الحساب الأمني", callback_data="security_check")],
        [InlineKeyboardButton("🔑 فحص كلمة المرور", callback_data="password_check")],
        [InlineKeyboardButton("🔗 فحص رابط مشبوه", callback_data="phishing_check")],
        [InlineKeyboardButton("🎲 توليد كلمة مرور قوية", callback_data="gen_password")],
        [InlineKeyboardButton("💡 نصائح لحماية نفسك", callback_data="tips")],
        [InlineKeyboardButton("🔐 حماية الأنظمة", callback_data="systems")],
        [InlineKeyboardButton("🧠 اختبار الوعي الأمني", callback_data="quiz_start")],
        [InlineKeyboardButton("📊 نقاطي ومستواي", callback_data="my_points")],
        [InlineKeyboardButton("🏆 لوحة الصدارة", callback_data="leaderboard")],
        [InlineKeyboardButton("📜 سجلي", callback_data="my_history")],
        [InlineKeyboardButton("🚨 إبلاغ عن نصب", callback_data="report_start")],
        [InlineKeyboardButton("📤 شارك البوت (اكسب نقاط)", callback_data="share_bot")],
        [InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")],
        [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")],
    ]
    if is_dev:
        rows.append([InlineKeyboardButton("🛠️ لوحة التحكم", callback_data="dev_panel")])
    return InlineKeyboardMarkup(rows)

def systems_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Google", callback_data="sys_google"),
         InlineKeyboardButton("TikTok", callback_data="sys_tiktok")],
        [InlineKeyboardButton("Instagram", callback_data="sys_instagram"),
         InlineKeyboardButton("Facebook", callback_data="sys_facebook")],
        [InlineKeyboardButton("WhatsApp", callback_data="sys_whatsapp"),
         InlineKeyboardButton("Telegram", callback_data="sys_telegram")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ])

def dev_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="dev_stats")],
        [InlineKeyboardButton("➕ إضافة اشتراك", callback_data="dev_add_sub")],
        [InlineKeyboardButton("📋 عرض الاشتراكات", callback_data="dev_list_subs")],
        [InlineKeyboardButton("🚨 البلاغات", callback_data="dev_reports")],
        [InlineKeyboardButton("📢 بث رسالة", callback_data="dev_broadcast")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ])

def sub_types_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 قناة", callback_data="stype_channel")],
        [InlineKeyboardButton("👥 جروب", callback_data="stype_group")],
        [InlineKeyboardButton("🤖 بوت", callback_data="stype_bot")],
        [InlineKeyboardButton("🔗 لينك", callback_data="stype_link")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel")],
    ])

def back_btn(target="back_main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=target)]])

# ============ الاشتراك الإجباري ============
async def is_subscribed(context, user_id):
    subs = db.get_force_subs()
    if not subs: return True, []
    missing = []
    for sid, stype, chat_id, title, link in subs:
        if stype == "link":
            missing.append((sid, title, link)); continue
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                missing.append((sid, title, link or chat_id))
        except:
            missing.append((sid, title, link or chat_id))
    return (len(missing) == 0), missing

def sub_keyboard(missing):
    rows = []
    for sid, title, link in missing:
        url = link if link and link.startswith("http") else f"https://t.me/{str(link).lstrip('@')}"
        rows.append([InlineKeyboardButton(f"➡️ {title}", url=url)])
    rows.append([InlineKeyboardButton("✅ تحققت", callback_data="check_sub")])
    return InlineKeyboardMarkup(rows)

# ============ الأوامر ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    ref_by = None
    if args:
        try:
            rid = int(args[0])
            if rid != user.id: ref_by = rid
        except: pass
    is_new = db.add_user(user.id, user.username or "", user.first_name or "", ref_by)
    if is_new:
        db.add_points(user.id, 1)
        if ref_by:
            db.add_points(ref_by, 20)
            try:
                await context.bot.send_message(ref_by, "🎉 حد دخل البوت من لينكك! خدت 20 نقطة.")
            except: pass

    ok, missing = await is_subscribed(context, user.id)
    if not ok:
        await update.message.reply_text("⚠️ *لازم تشترك الأول:*" + FOOTER,
            reply_markup=sub_keyboard(missing), parse_mode="Markdown")
        return
    is_dev = (user.id == DEVELOPER_ID)
    await update.message.reply_text(
        f"👋 أهلاً *{user.first_name}*!\n\n🛡️ بوت التوعية الأمنية\nاختر من القائمة:" + FOOTER,
        reply_markup=main_menu(is_dev), parse_mode="Markdown")

async def dev_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DEVELOPER_ID: return
    await update.message.reply_text("🛠️ *لوحة التحكم*" + FOOTER,
        reply_markup=dev_menu(), parse_mode="Markdown")

# ============ معالج الأزرار ============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id
    is_dev = (uid == DEVELOPER_ID)

    if data == "noop": return

    if data == "check_sub":
        ok, missing = await is_subscribed(context, uid)
        if ok:
            await q.edit_message_text("✅ تم التحقق!" + FOOTER,
                reply_markup=main_menu(is_dev), parse_mode="Markdown")
        else:
            await q.edit_message_text("❌ لسه فيه قنوات:" + FOOTER,
                reply_markup=sub_keyboard(missing), parse_mode="Markdown")
        return

    ok, missing = await is_subscribed(context, uid)
    if not ok:
        await q.edit_message_text("⚠️ اشترك الأول:" + FOOTER,
            reply_markup=sub_keyboard(missing), parse_mode="Markdown")
        return

    if data == "back_main":
        await q.edit_message_text("القائمة الرئيسية:" + FOOTER,
            reply_markup=main_menu(is_dev), parse_mode="Markdown")
        return

    if data == "tips":
        await q.edit_message_text(GENERAL_TIPS + FOOTER, parse_mode="Markdown", reply_markup=back_btn())
        return

    if data == "systems":
        await q.edit_message_text("🔐 اختر النظام:" + FOOTER, reply_markup=systems_menu(), parse_mode="Markdown")
        return

    if data.startswith("sys_"):
        key = data[4:]
        text = SYSTEM_GUIDES.get(key, "لا يوجد دليل.")
        await q.edit_message_text(text + FOOTER, reply_markup=back_btn("systems"), parse_mode="Markdown")
        return

    if data == "about":
        await q.edit_message_text(
            "ℹ️ *عن البوت:*\n\nبوت توعية أمنية يهدف لحماية المستخدمين.\n\n"
            "🛡️ لا نخزن أي كلمات مرور.\n🎯 الهدف: نشر الوعي." + FOOTER,
            reply_markup=back_btn(), parse_mode="Markdown")
        return

    # فحص الحساب
    if data == "security_check":
        context.user_data["awaiting"] = "security_check"
        await q.edit_message_text(
            "🔍 *فحص الحساب الأمني*\n\nابعت اليوزرنيم (مثال: `ahmed_123`).\n"
            "⚠️ متبعتش كلمة المرور." + FOOTER,
            parse_mode="Markdown", reply_markup=back_btn())
        return

    # فحص كلمة المرور
    if data == "password_check":
        context.user_data["awaiting"] = "password_check"
        await q.edit_message_text(
            "🔑 *فحص كلمة المرور*\n\nابعت كلمة مرور *تجريبية* (مش حقيقية).\n"
            "⚠️ البوت مش هيحفظها، بس هيحللها ويحذفها." + FOOTER,
            parse_mode="Markdown", reply_markup=back_btn())
        return

    # فحص رابط
    if data == "phishing_check":
        context.user_data["awaiting"] = "phishing_check"
        await q.edit_message_text(
            "🔗 *فحص رابط مشبوه*\n\nابعت اللينك اللي عايز تفحصه.\n"
            "مثال: `http://g00gle-login.tk`" + FOOTER,
            parse_mode="Markdown", reply_markup=back_btn())
        return

    # توليد كلمة مرور
    if data == "gen_password":
        pwd_strong = generate_password(16, easy=False)
        pwd_easy = generate_password(easy=True)
        await q.edit_message_text(
            f"🎲 *كلمات مرور مقترحة:*\n\n"
            f"🔒 *عشوائية قوية:*\n`{pwd_strong}`\n\n"
            f"🧠 *سهلة الحفظ:*\n`{pwd_easy}`\n\n"
            f"💡 انسخها واحفظها في مدير كلمات مرور." + FOOTER,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 ولّد تاني", callback_data="gen_password")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
            ]))
        db.add_points(uid, 3)
        db.add_history(uid, "توليد كلمة مرور", "")
        return

    # نقاطي
    if data == "my_points":
        pts = db.get_points(uid)
        lvl = get_level(pts)
        nxt = get_next_level_points(pts)
        txt = f"📊 *نقاطك:* {pts}\n🏅 *مستواك:* {lvl}\n"
        if nxt: txt += f"🎯 المستوى التالي عند {nxt} نقطة (فاضل {nxt-pts})."
        else: txt += "🎉 وصلت لأعلى مستوى!"
        await q.edit_message_text(txt + FOOTER, parse_mode="Markdown", reply_markup=back_btn())
        return

    # لوحة الصدارة
    if data == "leaderboard":
        top = db.get_leaderboard(10)
        if not top:
            await q.edit_message_text("لسه مفيش مستخدمين." + FOOTER, parse_mode="Markdown", reply_markup=back_btn())
            return
        medals = ["🥇","🥈","🥉"] + ["🔹"]*7
        txt = "🏆 *أعلى 10 مستخدمين:*\n\n"
        for i, (name, pts) in enumerate(top):
            txt += f"{medals[i]} {name or 'مستخدم'} — *{pts}* نقطة\n"
        await q.edit_message_text(txt + FOOTER, parse_mode="Markdown", reply_markup=back_btn())
        return

    # سجلي
    if data == "my_history":
        hist = db.get_history(uid, 10)
        if not hist:
            await q.edit_message_text("لسه مفيش سجل." + FOOTER, parse_mode="Markdown", reply_markup=back_btn())
            return
        txt = "📜 *آخر 10 عمليات:*\n\n"
        for act, det, ts in hist:
            txt += f"• {act} {('- '+det) if det else ''}\n"
        await q.edit_message_text(txt + FOOTER, parse_mode="Markdown", reply_markup=back_btn())
        return

    # إبلاغ
    if data == "report_start":
        context.user_data["awaiting"] = "report_target"
        await q.edit_message_text(
            "🚨 *إبلاغ عن نصب*\n\nابعت رقم/حساب/لينك النصاب." + FOOTER,
            parse_mode="Markdown", reply_markup=back_btn())
        return

    # مشاركة البوت
    if data == "share_bot":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        share_url = f"https://t.me/share/url?url={link}&text=جرب بوت التوعية الأمنية!"
        await q.edit_message_text(
            f"📤 *شارك البوت واكسب 20 نقطة* لكل شخص يدخل من لينكك.\n\n"
            f"🔗 لينكك الخاص:\n`{link}`" + FOOTER,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 شارك الآن", url=share_url)],
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
            ]))
        return

    # اختبار الوعي
    if data == "quiz_start":
        await start_quiz(q, context, uid, is_dev)
        return

    if data.startswith("quiz_"):
        await handle_quiz_answer(q, context, uid, data, is_dev)
        return

    # ======== لوحة المطور ========
    if not is_dev: return

    if data == "dev_panel":
        await q.edit_message_text("🛠️ *لوحة التحكم*" + FOOTER,
            reply_markup=dev_menu(), parse_mode="Markdown")
        return

    if data == "dev_stats":
        count = db.get_users_count()
        subs = db.get_force_subs()
        reports = db.get_reports()
        await q.edit_message_text(
            f"📊 *الإحصائيات:*\n\n"
            f"👥 المستخدمين: *{count}*\n"
            f"🔒 الاشتراكات: *{len(subs)}*\n"
            f"🚨 البلاغات: *{len(reports)}*" + FOOTER,
            reply_markup=dev_menu(), parse_mode="Markdown")
        return

    if data == "dev_reports":
        reports = db.get_reports()
        if not reports:
            await q.edit_message_text("مفيش بلاغات." + FOOTER, parse_mode="Markdown", reply_markup=dev_menu())
            return
        txt = "🚨 *آخر البلاغات:*\n\n"
        for rid, uid_, target, reason, ts in reports[:20]:
            txt += f"#{rid} | من `{uid_}`\n🎯 {target}\n📝 {reason}\n\n"
        await q.edit_message_text(txt + FOOTER, parse_mode="Markdown", reply_markup=dev_menu())
        return

    if data == "dev_add_sub":
        await q.edit_message_text("اختر النوع:" + FOOTER, reply_markup=sub_types_menu(), parse_mode="Markdown")
        return

    if data.startswith("stype_"):
        stype = data[6:]
        context.user_data["new_sub"] = {"type": stype}
        context.user_data["awaiting"] = "sub_chat_id"
        hint = {"channel":"معرف القناة (`@my` أو `-100...`).","group":"معرف الجروب.","bot":"معرف البوت (`@mybot`).","link":"اللينك الكامل (`https://t.me/...`)."}[stype]
        await q.edit_message_text(f"📝 {hint}\n\n/cancel للإلغاء." + FOOTER, parse_mode="Markdown")
        return

    if data == "dev_list_subs":
        subs = db.get_force_subs()
        if not subs:
            await q.edit_message_text("مفيش اشتراكات." + FOOTER, parse_mode="Markdown", reply_markup=dev_menu())
            return
        rows = []
        txt = "📋 *الاشتراكات:*\n\n"
        for sid, stype, chat_id, title, link in subs:
            txt += f"• `{sid}` — {title} ({stype})\n"
            rows.append([InlineKeyboardButton(f"❌ حذف {title}", callback_data=f"del_{sid}")])
        rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel")])
        await q.edit_message_text(txt + FOOTER, reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")
        return

    if data.startswith("del_"):
        sid = int(data[4:])
        db.delete_force_sub(sid)
        await q.edit_message_text("✅ تم الحذف." + FOOTER, parse_mode="Markdown", reply_markup=dev_menu())
        return

    if data == "dev_broadcast":
        context.user_data["awaiting"] = "broadcast"
        await q.edit_message_text("📢 ابعت الرسالة.\n\n/cancel للإلغاء." + FOOTER, parse_mode="Markdown")
        return

# ============ الاختبار ============
async def start_quiz(q, context, uid, is_dev):
    idx = 0
    context.user_data["quiz"] = {"idx": idx, "correct": 0, "total": 0}
    await send_quiz_question(q, context, uid)

async def send_quiz_question(q, context, uid):
    quiz = context.user_data.get("quiz", {"idx":0,"correct":0,"total":0})
    idx = quiz["idx"]
    if idx >= len(QUIZ_QUESTIONS):
        correct = quiz["correct"]
        total = len(QUIZ_QUESTIONS)
        pts = correct * 10
        db.add_points(uid, pts)
        db.add_history(uid, "اختبار وعي", f"{correct}/{total}")
        emoji = "🏆" if correct == total else "🎯" if correct >= total//2 else "📚"
        await q.edit_message_text(
            f"{emoji} *انتهى الاختبار!*\n\n"
            f"✅ صح: *{correct}*\n❌ غلط: *{total-correct}*\n"
            f"🎁 كسبت: *{pts}* نقطة" + FOOTER,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 جرب تاني", callback_data="quiz_start")],
                [InlineKeyboardButton("🔙 القائمة", callback_data="back_main")],
            ]),
            parse_mode="Markdown")
        context.user_data.pop("quiz", None)
        return
    question = QUIZ_QUESTIONS[idx]
    rows = []
    for i, opt in enumerate(question["options"]):
        rows.append([InlineKeyboardButton(opt, callback_data=f"quiz_{idx}_{i}")])
    await q.edit_message_text(
        f"🧠 *سؤال {idx+1}/{len(QUIZ_QUESTIONS)}*\n\n{question['q']}" + FOOTER,
        reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")

async def handle_quiz_answer(q, context, uid, data, is_dev):
    parts = data.split("_")
    idx = int(parts[1])
    ans = int(parts[2])
    quiz = context.user_data.get("quiz")
    if not quiz or quiz.get("idx") != idx:
        await q.edit_message_text("انتهت الجلسة. ابدأ من جديد." + FOOTER, reply_markup=back_btn())
        return
    correct = QUIZ_QUESTIONS[idx]["correct"]
    if ans == correct:
        quiz["correct"] += 1
        feedback = "✅ *إجابة صحيحة!*"
    else:
        feedback = f"❌ *غلط.* الصح: *{QUIZ_QUESTIONS[idx]['options'][correct]}*"
    quiz["idx"] = idx + 1
    context.user_data["quiz"] = quiz
    await q.edit_message_text(feedback + FOOTER, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("التالي ▶️", callback_data="quiz_next")]]))
    # نخزن مؤقتاً عشان quiz_next
    context.user_data["_quiz_pending"] = True

async def quiz_next_handler(q, context, uid):
    await send_quiz_question(q, context, uid)

# ============ استقبال الرسائل ============
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    awaiting = context.user_data.get("awaiting")
    if not awaiting: return
    text = update.message.text.strip()

    if text == "/cancel":
        context.user_data.clear()
        await update.message.reply_text("تم الإلغاء." + FOOTER, parse_mode="Markdown")
        return

    # فحص الحساب
    if awaiting == "security_check":
        if len(text) > 50 or "\n" in text:
            await update.message.reply_text("⚠️ ده مش يوزرنيم صحيح." + FOOTER, parse_mode="Markdown"); return
        if len(text) > 25 and any(c in text for c in "!@#$%^&*()+=[]{}|;:,<>?/\"'`~"):
            await update.message.reply_text("🚨 شكلها كلمة مرور، مش يوزرنيم.\n❗ متبعتش كلمة المرور." + FOOTER, parse_mode="Markdown"); return
        score, level, decision, reasons, tips = analyze_username_security(text)
        out = (f"🔍 *نتيجة الفحص:* `{text}`\n\n📊 {level}  ({score}/100)\n\n"
               f"📌 *القرار:*\n{decision}\n\n📋 *الأسباب:*\n" + "\n".join(reasons) +
               "\n\n💡 *نصائح:*\n" + "\n".join(f"• {t}" for t in tips) + FOOTER)
        await update.message.reply_text(out, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 فحص تاني", callback_data="security_check")],
                [InlineKeyboardButton("🔙 القائمة", callback_data="back_main")]]))
        db.add_points(user.id, 5)
        db.add_history(user.id, "فحص حساب", text[:20])
        context.user_data.pop("awaiting", None)
        return

    # فحص كلمة المرور
    if awaiting == "password_check":
        if len(text) > 100:
            await update.message.reply_text("⚠️ كلمة المرور طويلة بشكل غريب." + FOOTER, parse_mode="Markdown"); return
        score, level, time_str, reasons, tips = analyze_password_strength(text)
        out = (f"🔑 *تحليل كلمة المرور*\n\n📊 {level}  ({score}/100)\n\n"
               f"⏱️ *وقت الاختراق المتوقع:* {time_str}\n\n"
               f"📋 *الملاحظات:*\n" + "\n".join(reasons) +
               "\n\n💡 *نصائح:*\n" + "\n".join(f"• {t}" for t in tips) +
               "\n\n⚠️ *البوت مش بيحفظ الكلمة دي.*" + FOOTER)
        msg = await update.message.reply_text(out, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 فحص تاني", callback_data="password_check")],
                [InlineKeyboardButton("🔙 القائمة", callback_data="back_main")]]))
        db.add_points(user.id, 5)
        db.add_history(user.id, "فحص كلمة مرور", "")
        # نخلي المستخدم يمسح رسالته للخصوصية
        try: await update.message.delete()
        except: pass
        context.user_data.pop("awaiting", None)
        return

    # فحص رابط
    if awaiting == "phishing_check":
        risk, level, reasons, tips = analyze_link(text)
        out = (f"🔗 *فحص الرابط:*\n`{text[:80]}`\n\n📊 {level}  ({risk}/100)\n\n"
               f"📋 *التفاصيل:*\n" + "\n".join(reasons) +
               "\n\n💡 *نصائح:*\n" + "\n".join(f"• {t}" for t in tips) + FOOTER)
        await update.message.reply_text(out, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 فحص تاني", callback_data="phishing_check")],
                [InlineKeyboardButton("🔙 القائمة", callback_data="back_main")]]))
        db.add_points(user.id, 5)
        db.add_history(user.id, "فحص رابط", text[:30])
        context.user_data.pop("awaiting", None)
        return

    # إبلاغ
    if awaiting == "report_target":
        context.user_data["report_target"] = text
        context.user_data["awaiting"] = "report_reason"
        await update.message.reply_text("📝 اكتب تفاصيل النصب." + FOOTER, parse_mode="Markdown")
        return

    if awaiting == "report_reason":
        target = context.user_data.get("report_target", "")
        db.add_report(user.id, target, text)
        db.add_points(user.id, 5)
        db.add_history(user.id, "إبلاغ", target[:20])
        context.user_data.clear()
        await update.message.reply_text("✅ تم استلام البلاغ. شكرًا!" + FOOTER, parse_mode="Markdown",
            reply_markup=back_btn())
        # إشعار المطور
        try:
            await context.bot.send_message(DEVELOPER_ID,
                f"🚨 *بلاغ جديد:*\nمن: `{user.id}`\n🎯 {target}\n📝 {text}" + FOOTER,
                parse_mode="Markdown")
        except: pass
        return

    # إضافة اشتراك
    if awaiting == "sub_chat_id":
        ns = context.user_data.get("new_sub", {})
        ns["chat_id"] = text
        context.user_data["new_sub"] = ns
        context.user_data["awaiting"] = "sub_title"
        await update.message.reply_text("📝 اكتب الاسم الظاهر." + FOOTER, parse_mode="Markdown")
        return

    if awaiting == "sub_title":
        ns = context.user_data.get("new_sub", {})
        ns["title"] = text
        context.user_data["new_sub"] = ns
        if ns.get("type") == "link":
            context.user_data["awaiting"] = "sub_link"
            await update.message.reply_text("🔗 ابعت اللينك الكامل." + FOOTER, parse_mode="Markdown")
        else:
            context.user_data["awaiting"] = "sub_link_optional"
            await update.message.reply_text("🔗 ابعت لينك الدعوة أو `skip`." + FOOTER, parse_mode="Markdown")
        return

    if awaiting in ("sub_link", "sub_link_optional"):
        ns = context.user_data.get("new_sub", {})
        ns["link"] = "" if text.lower() == "skip" else text
        db.add_force_sub(ns["type"], ns["chat_id"], ns["title"], ns["link"])
        context.user_data.clear()
        await update.message.reply_text(f"✅ تم إضافة: *{ns['title']}*" + FOOTER, parse_mode="Markdown")
        return

    # بث
    if awaiting == "broadcast":
        if user.id != DEVELOPER_ID: return
        users = db.get_all_users()
        sent = failed = 0
        for uid in users:
            try:
                await update.message.copy(chat_id=uid); sent += 1
            except: failed += 1
        await update.message.reply_text(f"✅ نجح: {sent}\n❌ فشل: {failed}" + FOOTER, parse_mode="Markdown")
        context.user_data.clear()
        return

# ============ quiz_next منفصل ============
async def quiz_next_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await send_quiz_question(q, context, q.from_user.id)

# ============ التنبيهات الدورية ============
async def daily_tip(context: ContextTypes.DEFAULT_TYPE):
    tips_pool = [
        "💡 فعّل التحقق بخطوتين على كل حساباتك — بتحميك حتى لو كلمة المرور اتسرقت.",
        "🔑 كلمة مرور قوية = 12 حرف على الأقل + حروف كبيرة وصغيرة + أرقام + رموز.",
        "⚠️ متضغطش على لينكات مشبوهة، حتى لو جاتلك من صاحبك.",
        "🔐 استخدم كلمات مرور مختلفة لكل حساب.",
        "🚨 أي حد يطلب منك كود OTP = نصاب. مهما كان.",
        "📱 راجع الأجهزة المتصلة بحساباتك من وقت للتاني.",
        "🛡️ استخدم مدير كلمات مرور بدل ما تحفظهم في دماغك.",
    ]
    import random as rnd
    tip = rnd.choice(tips_pool)
    users = db.get_all_users()
    for uid in users:
        try:
            await context.bot.send_message(uid, f"🔔 *نصيحة اليوم:*\n\n{tip}" + FOOTER, parse_mode="Markdown")
        except: pass

# ============ التشغيل ============
def main():
    import asyncio
    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
    except: pass

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dev", dev_command))
    app.add_handler(CallbackQueryHandler(quiz_next_cb, pattern="^quiz_next$"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # تنبيه يومي كل 24 ساعة
    if app.job_queue:
        app.job_queue.run_repeating(daily_tip, interval=86400, first=3600)

    print("✅ البوت شغال...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
