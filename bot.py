# -*- coding: utf-8 -*-
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re, secrets, string, threading, time
from urllib.parse import urlparse
import database as db

BOT_TOKEN = "8670627875:AAGScMvzRFgBHb6ARdVGGIp27oNm0Ywmdq8"
DEVELOPER_ID = 8772508181
DEVELOPER_NAME = "𝑬𝑳𝑩𝑨𝑩𝑨 𝑬𝑳𝑮𝑬𝑵𝑬𝑹𝑨𝑳"
DEVELOPER_USERNAME = "@ELBABAELGRNERAL"
BOT_USERNAME = "YourBotUsername"

FOOTER = "\n\n━━━━━━━━━━━━━━━━━━\n👨‍💻 " + DEVELOPER_NAME + "\n📩 " + DEVELOPER_USERNAME

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
db.init_db()
user_states = {}

GENERAL_TIPS = (
    "🛡️ *نصائح لحماية نفسك:*\n\n"
    "1️⃣ استخدم كلمة مرور قوية وفريدة لكل حساب (12-15 حرف).\n\n"
    "2️⃣ فعّل التحقق بخطوتين (2FA).\n\n"
    "3️⃣ احذر روابط التصيد.\n\n"
    "4️⃣ استخدم مدير كلمات مرور.\n\n"
    "5️⃣ راجع الأجهزة المتصلة بحساباتك.\n\n"
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
        score += 4; reasons.append("⚠️ قصير (" + str(length) + " أحرف) — سهل تخمينه.")
    if re.search(r"[a-z]", u) and re.search(r"[A-Z]", u): score += 15
    else: tips.append("اخلط بين حروف كبيرة وصغيرة (Aa).")
    if re.search(r"\d", u): score += 10
    else: tips.append("أضف أرقام (بدون تسلسل).")
    if re.search(r"[._\-]", u): score += 10
    else: tips.append("أضف رمز (نقطة أو شرطة) لزيادة الأمان.")
    if any(w in ul for w in COMMON_WORDS):
        score -= 20; reasons.append("⚠️ يحتوي على كلمة شائعة (admin, ahmed...).")
    if any(s in ul for s in COMMON_SEQ):
        score -= 20; reasons.append("⚠️ يحتوي على تسلسل (123، abc).")
    if re.search(r"(.)\1{2,}", u):
        score -= 10; reasons.append("⚠️ حرف مكرر 3+ مرات.")
    if re.search(r"(19|20)\d{2}", u):
        score -= 10; reasons.append("⚠️ يبدو فيه سنة ميلاد.")
    if u and (u[0].isdigit() or u[-1].isdigit()):
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

def analyze_password_strength(pwd):
    score = 0
    reasons, tips = [], []
    length = len(pwd)
    if length >= 16: score += 30
    elif length >= 12: score += 22
    elif length >= 8: score += 12
    else:
        score += 3; reasons.append("⚠️ قصيرة (" + str(length) + " حرف).")
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
    charset = 0
    if re.search(r"[a-z]", pwd): charset += 26
    if re.search(r"[A-Z]", pwd): charset += 26
    if re.search(r"\d", pwd): charset += 10
    if re.search(r"[^a-zA-Z0-9]", pwd): charset += 32
    if charset == 0: charset = 26
    try:
        combinations = charset ** length
        seconds = combinations / 1e10 / 2
    except:
        seconds = 0
    if seconds < 60: time_str = "⚡ فورًا (أقل من دقيقة)"
    elif seconds < 3600: time_str = "⏱️ " + str(int(seconds/60)) + " دقيقة"
    elif seconds < 86400: time_str = "🕐 " + str(int(seconds/3600)) + " ساعة"
    elif seconds < 31536000: time_str = "📅 " + str(int(seconds/86400)) + " يوم"
    elif seconds < 31536000*1000: time_str = "📆 " + str(int(seconds/31536000)) + " سنة"
    elif seconds < 31536000*1e9: time_str = "🌌 " + str(int(seconds/31536000/1e6)) + " مليون سنة"
    else: time_str = "🌠 ملايين السنين"
    if score >= 70: level = "🟢 قوية جدًا"
    elif score >= 45: level = "🟡 متوسطة"
    else: level = "🔴 ضعيفة"
    if not reasons: reasons.append("✅ مفيش علامات ضعف.")
    if not tips: tips.append("✅ ممتاز!")
    return score, level, time_str, reasons, tips

def generate_password(length=16, easy=False):
    if easy:
        words = ["Tiger","Rocket","Coffee","Sunset","Panda","Ninja","Dragon","Storm","Ocean","Moon","Fire","Cloud","River","Star","Falcon","Wolf"]
        p1, p2, p3 = secrets.choice(words), secrets.choice(words), secrets.choice(words)
        num = secrets.randbelow(100)
        sym = secrets.choice("!@#$%&*")
        return p1 + "-" + p2 + "-" + p3 + "-" + str(num) + sym
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return "".join(secrets.choice(alphabet) for _ in range(length))

SUSPICIOUS_KEYWORDS = ["login","verify","secure","update","account","confirm","free","winner","claim","prize","urgent","signin","wallet","bonus","gift"]
SHORTENERS = ["bit.ly","tinyurl.com","goo.gl","t.co","ow.ly","is.gd","buff.ly","rb.gy","cutt.ly"]
LOOKALIKE_PATTERNS = [
    (r"g[o0]{2}gle", "Google"), (r"faceb[o0]{2}k", "Facebook"),
    (r"whatsap{1,2}", "WhatsApp"), (r"instagr[ae]m", "Instagram"),
    (r"tik{1,2}tok", "TikTok"), (r"telegr[ae]m", "Telegram"),
    (r"paypa[1l]", "PayPal"), (r"amaz[o0]n", "Amazon"),
]
DANGEROUS_TLDS = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".work", ".click"]

def analyze_link(url):
    url_l = url.lower().strip()
    if not url_l.startswith(("http://", "https://")):
        url_l = "http://" + url_l
    try:
        parsed = urlparse(url_l)
        host = parsed.netloc.lower()
    except:
        return 0, "⚠️ مشبوه", ["رابط غير صالح."], ["تأكد من الرابط."]
    risk = 0
    reasons, tips = [], []
    if re.match(r"^\d+\.\d+\.\d+\.\d+", host):
        risk += 40; reasons.append("⚠️ الدومين عنوان IP — علامة خطيرة.")
    if any(s in host for s in SHORTENERS):
        risk += 20; reasons.append("⚠️ رابط مختصر — ممكن يخفي وجهة خطيرة.")
    found_kw = [k for k in SUSPICIOUS_KEYWORDS if k in url_l]
    if found_kw:
        risk += 15; reasons.append("⚠️ كلمات مشبوهة: " + ", ".join(found_kw) + ".")
    for pattern, brand in LOOKALIKE_PATTERNS:
        if re.search(pattern, host) and brand.lower().replace(" ","") not in host:
            risk += 25; reasons.append("⚠️ يحاول تقليد " + brand + ".")
            break
    for tld in DANGEROUS_TLDS:
        if host.endswith(tld):
            risk += 15; reasons.append("⚠️ امتداد خطير (" + tld + ").")
            break
    if parsed.scheme != "https":
        risk += 10; reasons.append("⚠️ الرابط مش HTTPS.")
    if host.count("-") >= 3:
        risk += 10; reasons.append("⚠️ شرطات كثيرة في الدومين.")
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

QUIZ_QUESTIONS = [
    {"q":"جالك إيميل من 'البنك' يقولك اضغط على لينك لتحديث بياناتك، تعمل إيه؟",
     "options":["أضغط على اللينك فورًا","أتجاهل الإيميل وأدخل على موقع البنك بنفسي","أرد على الإيميل وأطلب تأكيد"], "correct":1},
    {"q":"صاحبك بعتلك لينك على واتساب يقولك 'شوف الصورة دي'، تعمل إيه؟",
     "options":["أفتحها فورًا","أسأله الأول لو هو بعت اللينك فعلاً","أشاركها مع أصدقائي"], "correct":1},
    {"q":"حد اتصل بيك يقول إنه من الدعم الفني وبيطلب كود OTP، تعمل إيه؟",
     "options":["أديله الكود","أرفض وأقفل الخط","أديله جزء من الكود"], "correct":1},
    {"q":"كلمة المرور 'Ahmed@2024'، إيه رأيك فيها؟",
     "options":["قوية جدًا","متوسطة — يفضل تغييرها","ضعيفة جدًا"], "correct":1},
    {"q":"إيه أفضل طريقة لحماية حسابك؟",
     "options":["كلمة مرور بسيطة عشان مفتكرهاش","كلمة مرور قوية + 2FA","نفس الباسورد لكل حساباتي"], "correct":1},
]

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

def main_menu(is_dev=False):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("🔍 فحص الحساب", callback_data="security_check"),
           InlineKeyboardButton("🔑 فحص كلمة المرور", callback_data="password_check"))
    kb.add(InlineKeyboardButton("🔗 فحص رابط", callback_data="phishing_check"),
           InlineKeyboardButton("🎲 توليد كلمة مرور", callback_data="gen_password"))
    kb.add(InlineKeyboardButton("💡 نصائح", callback_data="tips"),
           InlineKeyboardButton("🔐 حماية الأنظمة", callback_data="systems"))
    kb.add(InlineKeyboardButton("🧠 اختبار الوعي", callback_data="quiz_start"),
           InlineKeyboardButton("📊 نقاطي", callback_data="my_points"))
    kb.add(InlineKeyboardButton("🏆 الصدارة", callback_data="leaderboard"),
           InlineKeyboardButton("📜 سجلي", callback_data="my_history"))
    kb.add(InlineKeyboardButton("🚨 إبلاغ", callback_data="report_start"),
           InlineKeyboardButton("📤 مشاركة", callback_data="share_bot"))
    kb.add(InlineKeyboardButton("👨‍💻 المطور", url="https://t.me/" + DEVELOPER_USERNAME[1:]))
    kb.add(InlineKeyboardButton("ℹ️ عن البوت", callback_data="about"))
    if is_dev:
        kb.add(InlineKeyboardButton("🛠️ لوحة التحكم", callback_data="dev_panel"))
    return kb

def systems_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("Google", callback_data="sys_google"),
           InlineKeyboardButton("TikTok", callback_data="sys_tiktok"))
    kb.add(InlineKeyboardButton("Instagram", callback_data="sys_instagram"),
           InlineKeyboardButton("Facebook", callback_data="sys_facebook"))
    kb.add(InlineKeyboardButton("WhatsApp", callback_data="sys_whatsapp"),
           InlineKeyboardButton("Telegram", callback_data="sys_telegram"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return kb

def dev_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("📊 الإحصائيات", callback_data="dev_stats"))
    kb.add(InlineKeyboardButton("➕ إضافة اشتراك", callback_data="dev_add_sub"))
    kb.add(InlineKeyboardButton("📋 عرض الاشتراكات", callback_data="dev_list_subs"))
    kb.add(InlineKeyboardButton("🚨 البلاغات", callback_data="dev_reports"))
    kb.add(InlineKeyboardButton("📢 بث رسالة", callback_data="dev_broadcast"))
    kb.add(InlineKeyboardButton("💰 إضافة نقاط", callback_data="dev_add_points"))
    kb.add(InlineKeyboardButton("➖ خصم نقاط", callback_data="dev_remove_points"))
    kb.add(InlineKeyboardButton("💵 أسعار الأزرار", callback_data="dev_button_costs"))
    kb.add(InlineKeyboardButton("🎁 نقاط الإحالة", callback_data="dev_referral_points"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return kb

def sub_types_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("📢 قناة", callback_data="stype_channel"),
           InlineKeyboardButton("👥 جروب", callback_data="stype_group"))
    kb.add(InlineKeyboardButton("🤖 بوت", callback_data="stype_bot"),
           InlineKeyboardButton("🔗 لينك", callback_data="stype_link"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel"))
    return kb

def back_btn(target="back_main"):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data=target))
    return kb

def is_subscribed(user_id):
    subs = db.get_force_subs()
    if not subs: return True, []
    missing = []
    for row in subs:
        sid, stype, chat_id, title, link = row
        if stype in ("link", "bot"):
            continue
        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status in ["left", "kicked"]:
                missing.append((sid, title, link or chat_id))
        except:
            missing.append((sid, title, link or chat_id))
    return (len(missing) == 0), missing

def sub_keyboard(missing):
    kb = InlineKeyboardMarkup(row_width=1)
    for sid, title, link in missing:
        url = link if link and link.startswith("http") else "https://t.me/" + str(link).lstrip("@")
        kb.add(InlineKeyboardButton("➡️ " + title, url=url))
    kb.add(InlineKeyboardButton("✅ تحققت", callback_data="check_sub"))
    return kb

@bot.message_handler(commands=['start'], func=lambda m: m.chat.type == "private")
def cmd_start(message):
    user = message.from_user
    args = message.text.split()
    ref_by = None
    if len(args) > 1:
        try:
            rid = int(args[1])
            if rid != user.id: ref_by = rid
        except Exception as _e: print("BT_ERR:", _e)
    is_new = db.add_user(user.id, user.username or "", user.first_name or "", ref_by)
    if is_new:
        db.add_points(user.id, 1)
        if ref_by:
            db.add_points(ref_by, get_referral_points())
            try:
                bot.send_message(ref_by, "🎉 حد دخل البوت من لينكك! خدت " + str(get_referral_points()) + " نقطة.")
            except Exception as _e: print("BT_ERR:", _e)
    ok, missing = is_subscribed(user.id)
    if not ok:
        bot.send_message(message.chat.id, "⚠️ *لازم تشترك الأول:*" + FOOTER, reply_markup=sub_keyboard(missing))
        return
    is_dev = (user.id == DEVELOPER_ID)
    bot.send_message(message.chat.id, "👋 أهلاً *" + (user.first_name or "") + "*!\n\n🛡️ بوت التوعية الأمنية\nاختر من القائمة:" + FOOTER, reply_markup=main_menu(is_dev))

@bot.message_handler(commands=['dev'], func=lambda m: m.chat.type == "private")
def cmd_dev(message):
    if message.from_user.id != DEVELOPER_ID: return
    bot.send_message(message.chat.id, "🛠️ *لوحة التحكم*" + FOOTER, reply_markup=dev_menu())

@bot.callback_query_handler(func=lambda call: call.message.chat.type == "private")
def handle_callback(call):
    data = call.data
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    is_dev = (uid == DEVELOPER_ID)
    try: bot.answer_callback_query(call.id)
    except Exception as _e: print("BT_ERR:", _e)
    
    if data == "check_sub":
        ok, missing = is_subscribed(uid)
        if ok:
            try: bot.edit_message_text("✅ تم التحقق!" + FOOTER, cid, mid, reply_markup=main_menu(is_dev))
            except Exception as _e: print("BT_ERR:", _e)
        else:
            try: bot.edit_message_text("❌ لسه فيه قنوات:" + FOOTER, cid, mid, reply_markup=sub_keyboard(missing))
            except Exception as _e: print("BT_ERR:", _e)
        return
    
    ok, missing = is_subscribed(uid)
    if not ok:
        try: bot.edit_message_text("⚠️ اشترك الأول:" + FOOTER, cid, mid, reply_markup=sub_keyboard(missing))
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "back_main":
        try: bot.edit_message_text("القائمة الرئيسية:" + FOOTER, cid, mid, reply_markup=main_menu(is_dev))
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "tips":
        try: bot.edit_message_text(GENERAL_TIPS + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "systems":
        try: bot.edit_message_text("🔐 اختر النظام:" + FOOTER, cid, mid, reply_markup=systems_menu())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data.startswith("sys_"):
        key = data[4:]
        text = SYSTEM_GUIDES.get(key, "لا يوجد دليل.")
        try: bot.edit_message_text(text + FOOTER, cid, mid, reply_markup=back_btn("systems"))
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "about":
        try: bot.edit_message_text("ℹ️ *عن البوت:*\n\nبوت توعية أمنية لحماية المستخدمين.\n\n🛡️ لا نخزن كلمات المرور.\n🎯 الهدف: نشر الوعي." + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "security_check":
        user_states[uid] = {"awaiting": "security_check"}
        try: bot.edit_message_text("🔍 *فحص الحساب الأمني*\n\nابعت اليوزرنيم (مثال: ahmed123).\n\n⚠️ متبعتش كلمة المرور." + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "password_check":
        user_states[uid] = {"awaiting": "password_check"}
        try: bot.edit_message_text("🔑 *فحص كلمة المرور*\n\nابعت كلمة مرور تجريبية (مش حقيقية).\n\n⚠️ البوت مش هيحفظها." + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "phishing_check":
        user_states[uid] = {"awaiting": "phishing_check"}
        try: bot.edit_message_text("🔗 *فحص رابط مشبوه*\n\nابعت اللينك.\nمثال: http://g00gle-login.tk" + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "gen_password":
        pwd_strong = generate_password(16, easy=False)
        pwd_easy = generate_password(easy=True)
        text = "🎲 *كلمات مرور مقترحة:*\n\n🔒 *عشوائية قوية:*\n`" + pwd_strong + "`\n\n🧠 *سهلة الحفظ:*\n`" + pwd_easy + "`\n\n💡 احفظها في مدير كلمات مرور." + FOOTER
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎲 ولّد تاني", callback_data="gen_password"))
        kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        try: bot.edit_message_text(text, cid, mid, reply_markup=kb)
        except Exception as _e: print("BT_ERR:", _e)
        db.add_points(uid, 3)
        db.add_history(uid, "توليد كلمة مرور", "")
        return
    
    if data == "my_points":
        pts = db.get_points(uid)
        lvl = get_level(pts)
        nxt = get_next_level_points(pts)
        txt = "📊 *نقاطك:* " + str(pts) + "\n🏅 *مستواك:* " + lvl + "\n"
        if nxt: txt += "🎯 المستوى التالي عند " + str(nxt) + " نقطة (فاضل " + str(nxt-pts) + ")."
        else: txt += "🎉 وصلت لأعلى مستوى!"
        try: bot.edit_message_text(txt + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "leaderboard":
        top = db.get_leaderboard(10)
        if not top:
            try: bot.edit_message_text("لسه مفيش مستخدمين." + FOOTER, cid, mid, reply_markup=back_btn())
            except Exception as _e: print("BT_ERR:", _e)
            return
        medals = ["🥇","🥈","🥉"] + ["🔹"]*7
        txt = "🏆 *أعلى 10 مستخدمين:*\n\n"
        for i, (name, pts) in enumerate(top):
            txt += medals[i] + " " + (name or "مستخدم") + " — *" + str(pts) + "* نقطة\n"
        try: bot.edit_message_text(txt + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "my_history":
        hist = db.get_history(uid, 10)
        if not hist:
            try: bot.edit_message_text("لسه مفيش سجل." + FOOTER, cid, mid, reply_markup=back_btn())
            except Exception as _e: print("BT_ERR:", _e)
            return
        txt = "📜 *آخر 10 عمليات:*\n\n"
        for act, det, ts in hist:
            txt += "• " + act + (" - " + det if det else "") + "\n"
        try: bot.edit_message_text(txt + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "report_start":
        user_states[uid] = {"awaiting": "report_target"}
        try: bot.edit_message_text("🚨 *إبلاغ عن نصب*\n\nابعت رقم/حساب/لينك النصاب." + FOOTER, cid, mid, reply_markup=back_btn())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "share_bot":
        link = "https://t.me/" + BOT_USERNAME + "?start=" + str(uid)
        share_url = "https://t.me/share/url?url=" + link + "&text=" + "جرب بوت التوعية الأمنية!"
        txt = "📤 *شارك البوت واكسب " + str(get_referral_points()) + " نقطة* لكل شخص يدخل من لينكك.\n\n🔗 لينكك الخاص:\n`" + link + "`" + FOOTER
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📤 شارك الآن", url=share_url))
        kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        try: bot.edit_message_text(txt, cid, mid, reply_markup=kb)
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "quiz_start":
        user_states[uid] = {"quiz_idx": 0, "quiz_correct": 0}
        send_quiz_question(cid, mid, uid)
        return
    
    if data.startswith("quiz_ans_"):
        parts = data.split("_")
        ans = int(parts[2])
        state = user_states.get(uid, {})
        idx = state.get("quiz_idx", 0)
        if idx >= len(QUIZ_QUESTIONS): return
        correct = QUIZ_QUESTIONS[idx]["correct"]
        if ans == correct:
            state["quiz_correct"] = state.get("quiz_correct", 0) + 1
            feedback = "✅ *إجابة صحيحة!*"
        else:
            feedback = "❌ *غلط.* الصح: *" + QUIZ_QUESTIONS[idx]["options"][correct] + "*"
        state["quiz_idx"] = idx + 1
        user_states[uid] = state
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("التالي ▶️", callback_data="quiz_next"))
        try: bot.edit_message_text(feedback + FOOTER, cid, mid, reply_markup=kb)
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "quiz_next":
        send_quiz_question(cid, mid, uid)
        return
    
    if not is_dev: return
    
    if data == "dev_add_points":
        user_states[uid] = {"awaiting": "add_points_target"}
        try: bot.edit_message_text("💰 *إضافة نقاط*\n\nابعت ID المستخدم أو @username." + FOOTER, cid, mid, reply_markup=back_btn("dev_panel"))
        except: pass
        return
    
    if data == "dev_remove_points":
        user_states[uid] = {"awaiting": "remove_points_target"}
        try: bot.edit_message_text("➖ *خصم نقاط*\n\nابعت ID المستخدم أو @username." + FOOTER, cid, mid, reply_markup=back_btn("dev_panel"))
        except: pass
        return
    
    if data == "dev_button_costs":
        txt = "💵 *أسعار الأزرار بالنقاط:*\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for key, name in BUTTON_NAMES.items():
            cost = db.get_setting("cost_" + key, "0")
            txt += "• " + name + ": *" + cost + "* نقطة\n"
            kb.add(InlineKeyboardButton(name + " (" + cost + ")", callback_data="setcost_" + key))
        kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel"))
        try: bot.edit_message_text(txt + "\nاختر زر لتعديل سعره (0-100)." + FOOTER, cid, mid, reply_markup=kb)
        except: pass
        return
    
    if data.startswith("setcost_"):
        key = data[8:]
        user_states[uid] = {"awaiting": "set_cost_amount", "cost_key": key}
        try: bot.edit_message_text("💵 اكتب سعر " + BUTTON_NAMES.get(key, key) + " من 0 لـ 100." + FOOTER, cid, mid, reply_markup=back_btn("dev_button_costs"))
        except: pass
        return
    
    if data == "dev_referral_points":
        current = db.get_setting("referral_points", "20")
        user_states[uid] = {"awaiting": "set_referral_amount"}
        try: bot.edit_message_text("🎁 *نقاط الإحالة*\n\nالسعر الحالي: *" + current + "* نقطة\n\nاكتب الرقم الجديد (0-100)." + FOOTER, cid, mid, reply_markup=back_btn("dev_panel"))
        except: pass
        return
    
    if data == "dev_panel":
        try: bot.edit_message_text("🛠️ *لوحة التحكم*" + FOOTER, cid, mid, reply_markup=dev_menu())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "dev_stats":
        count = db.get_users_count()
        subs = db.get_force_subs()
        reports = db.get_reports()
        txt = "📊 *الإحصائيات:*\n\n👥 المستخدمين: *" + str(count) + "*\n🔒 الاشتراكات: *" + str(len(subs)) + "*\n🚨 البلاغات: *" + str(len(reports)) + "*" + FOOTER
        try: bot.edit_message_text(txt, cid, mid, reply_markup=dev_menu())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "dev_reports":
        reports = db.get_reports()
        if not reports:
            try: bot.edit_message_text("مفيش بلاغات." + FOOTER, cid, mid, reply_markup=dev_menu())
            except Exception as _e: print("BT_ERR:", _e)
            return
        txt = "🚨 *آخر البلاغات:*\n\n"
        for rid, uid_, target, reason, ts in reports[:20]:
            txt += "#" + str(rid) + " | من `" + str(uid_) + "`\n🎯 " + str(target) + "\n📝 " + str(reason) + "\n\n"
        try: bot.edit_message_text(txt + FOOTER, cid, mid, reply_markup=dev_menu())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "dev_add_sub":
        try: bot.edit_message_text("اختر النوع:" + FOOTER, cid, mid, reply_markup=sub_types_menu())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data.startswith("stype_"):
        stype = data[6:]
        user_states[uid] = {"new_sub": {"type": stype}, "awaiting": "sub_chat_id"}
        hint = {"channel":"معرف القناة (@my أو -100...).","group":"معرف الجروب.","bot":"معرف البوت (@mybot).","link":"اللينك الكامل (https://t.me/...)."}[stype]
        try: bot.edit_message_text("📝 " + hint + "\n\n/cancel للإلغاء." + FOOTER, cid, mid)
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "dev_list_subs":
        subs = db.get_force_subs()
        if not subs:
            try: bot.edit_message_text("مفيش اشتراكات." + FOOTER, cid, mid, reply_markup=dev_menu())
            except Exception as _e: print("BT_ERR:", _e)
            return
        txt = "📋 *الاشتراكات:*\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for sid, stype, chat_id, title, link in subs:
            txt += "• `" + str(sid) + "` — " + title + " (" + stype + ")\n"
            kb.add(InlineKeyboardButton("❌ حذف " + title, callback_data="del_" + str(sid)))
        kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="dev_panel"))
        try: bot.edit_message_text(txt + FOOTER, cid, mid, reply_markup=kb)
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data.startswith("del_"):
        sid = int(data[4:])
        db.delete_force_sub(sid)
        try: bot.edit_message_text("✅ تم الحذف." + FOOTER, cid, mid, reply_markup=dev_menu())
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if data == "dev_broadcast":
        user_states[uid] = {"awaiting": "broadcast"}
        try: bot.edit_message_text("📢 ابعت الرسالة.\n\n/cancel للإلغاء." + FOOTER, cid, mid)
        except Exception as _e: print("BT_ERR:", _e)
        return

def send_quiz_question(cid, mid, uid):
    state = user_states.get(uid, {})
    idx = state.get("quiz_idx", 0)
    if idx >= len(QUIZ_QUESTIONS):
        correct = state.get("quiz_correct", 0)
        total = len(QUIZ_QUESTIONS)
        pts = correct * 10
        db.add_points(uid, pts)
        db.add_history(uid, "اختبار وعي", str(correct) + "/" + str(total))
        emoji = "🏆" if correct == total else "🎯" if correct >= total//2 else "📚"
        txt = emoji + " *انتهى الاختبار!*\n\n✅ صح: *" + str(correct) + "*\n❌ غلط: *" + str(total-correct) + "*\n🎁 كسبت: *" + str(pts) + "* نقطة" + FOOTER
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔁 جرب تاني", callback_data="quiz_start"))
        kb.add(InlineKeyboardButton("🔙 القائمة", callback_data="back_main"))
        try: bot.edit_message_text(txt, cid, mid, reply_markup=kb)
        except Exception as _e: print("BT_ERR:", _e)
        user_states.pop(uid, None)
        return
    q = QUIZ_QUESTIONS[idx]
    kb = InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(q["options"]):
        kb.add(InlineKeyboardButton(opt, callback_data="quiz_ans_" + str(i)))
    txt = "🧠 *سؤال " + str(idx+1) + "/" + str(len(QUIZ_QUESTIONS)) + "*\n\n" + q["q"] + FOOTER
    try: bot.edit_message_text(txt, cid, mid, reply_markup=kb)
    except Exception as _e: print("BT_ERR:", _e)

@bot.message_handler(func=lambda m: m.chat.type == "private")
def handle_message(message):
    uid = message.from_user.id
    state = user_states.get(uid, {})
    awaiting = state.get("awaiting")
    if not awaiting: return
    text = message.text.strip() if message.text else ""
    
    if text == "/cancel":
        user_states.pop(uid, None)
        bot.reply_to(message, "تم الإلغاء." + FOOTER)
        return
    
    if awaiting == "security_check":
        if len(text) > 50 or "\n" in text:
            bot.reply_to(message, "⚠️ ده مش يوزرنيم صحيح." + FOOTER); return
        if len(text) > 25 and any(c in text for c in "!@#$%^&*()+=[]{}|;:,<>?/\"'`~"):
            bot.reply_to(message, "🚨 شكلها كلمة مرور، مش يوزرنيم.\n❗ متبعتش كلمة المرور." + FOOTER); return
        score, level, decision, reasons, tips = analyze_username_security(text)
        out = "🔍 *نتيجة الفحص:* `" + text + "`\n\n📊 " + level + "  (" + str(score) + "/100)\n\n📌 *القرار:*\n" + decision + "\n\n📋 *الأسباب:*\n" + "\n".join(reasons) + "\n\n💡 *نصائح:*\n" + "\n".join("• " + t for t in tips) + FOOTER
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔍 فحص تاني", callback_data="security_check"))
        kb.add(InlineKeyboardButton("🔙 القائمة", callback_data="back_main"))
        bot.send_message(message.chat.id, out, reply_markup=kb)
        db.add_points(uid, 5)
        db.add_history(uid, "فحص حساب", text[:20])
        user_states.pop(uid, None)
        return
    
    if awaiting == "password_check":
        if len(text) > 100:
            bot.reply_to(message, "⚠️ كلمة المرور طويلة بشكل غريب." + FOOTER); return
        score, level, time_str, reasons, tips = analyze_password_strength(text)
        out = "🔑 *تحليل كلمة المرور*\n\n📊 " + level + "  (" + str(score) + "/100)\n\n⏱️ *وقت الاختراق المتوقع:* " + time_str + "\n\n📋 *الملاحظات:*\n" + "\n".join(reasons) + "\n\n💡 *نصائح:*\n" + "\n".join("• " + t for t in tips) + "\n\n⚠️ *البوت مش بيحفظ الكلمة دي.*" + FOOTER
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔑 فحص تاني", callback_data="password_check"))
        kb.add(InlineKeyboardButton("🔙 القائمة", callback_data="back_main"))
        bot.send_message(message.chat.id, out, reply_markup=kb)
        db.add_points(uid, 5)
        db.add_history(uid, "فحص كلمة مرور", "")
        try: bot.delete_message(message.chat.id, message.message_id)
        except Exception as _e: print("BT_ERR:", _e)
        user_states.pop(uid, None)
        return
    
    if awaiting == "phishing_check":
        risk, level, reasons, tips = analyze_link(text)
        out = "🔗 *فحص الرابط:*\n`" + text[:80] + "`\n\n📊 " + level + "  (" + str(risk) + "/100)\n\n📋 *التفاصيل:*\n" + "\n".join(reasons) + "\n\n💡 *نصائح:*\n" + "\n".join("• " + t for t in tips) + FOOTER
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔗 فحص تاني", callback_data="phishing_check"))
        kb.add(InlineKeyboardButton("🔙 القائمة", callback_data="back_main"))
        bot.send_message(message.chat.id, out, reply_markup=kb)
        db.add_points(uid, 5)
        db.add_history(uid, "فحص رابط", text[:30])
        user_states.pop(uid, None)
        return
    
    if awaiting == "report_target":
        state["report_target"] = text
        state["awaiting"] = "report_reason"
        user_states[uid] = state
        bot.reply_to(message, "📝 اكتب تفاصيل النصب." + FOOTER)
        return
    
    if awaiting == "report_reason":
        target = state.get("report_target", "")
        db.add_report(uid, target, text)
        db.add_points(uid, 5)
        db.add_history(uid, "إبلاغ", target[:20])
        user_states.pop(uid, None)
        bot.send_message(message.chat.id, "✅ تم استلام البلاغ. شكرًا!" + FOOTER, reply_markup=back_btn())
        try:
            bot.send_message(DEVELOPER_ID, "🚨 *بلاغ جديد:*\nمن: `" + str(uid) + "`\n🎯 " + target + "\n📝 " + text + FOOTER)
        except Exception as _e: print("BT_ERR:", _e)
        return
    
    if awaiting == "add_points_target":
        u = db.find_user(text)
        if not u:
            bot.reply_to(message, "❌ المستخدم مش موجود." + FOOTER); return
        state["target_uid"] = u[0]
        state["target_name"] = u[1] or ""
        state["awaiting"] = "add_points_amount"
        user_states[uid] = state
        bot.reply_to(message, "✅ " + (u[1] or "المستخدم") + " عنده دلوقتي *" + str(u[2]) + "* نقطة.\n\nاكتب عدد النقاط اللي عايز تضيفها." + FOOTER)
        return
    
    if awaiting == "add_points_amount":
        try: amt = int(text)
        except:
            bot.reply_to(message, "⚠️ اكتب رقم صحيح." + FOOTER); return
        if amt < 1 or amt > 100000:
            bot.reply_to(message, "⚠️ الرقم لازم من 1 لـ 100000." + FOOTER); return
        db.add_points(state["target_uid"], amt)
        new_pts = db.get_points(state["target_uid"])
        bot.reply_to(message, "✅ تم إضافة *" + str(amt) + "* نقطة لـ " + (state.get("target_name") or "المستخدم") + ".\nالرصيد الجديد: *" + str(new_pts) + "*" + FOOTER)
        try:
            bot.send_message(state["target_uid"], "🎁 *تم إضافة " + str(amt) + " نقطة لحسابك* من المطور!\n\nرصيدك الحالي: *" + str(new_pts) + "* نقطة" + FOOTER)
        except: pass
        user_states.pop(uid, None)
        return
    
    if awaiting == "remove_points_target":
        u = db.find_user(text)
        if not u:
            bot.reply_to(message, "❌ المستخدم مش موجود." + FOOTER); return
        state["target_uid"] = u[0]
        state["target_name"] = u[1] or ""
        state["awaiting"] = "remove_points_amount"
        user_states[uid] = state
        bot.reply_to(message, "✅ " + (u[1] or "المستخدم") + " عنده *" + str(u[2]) + "* نقطة.\n\nاكتب عدد النقاط اللي عايز تخصمها." + FOOTER)
        return
    
    if awaiting == "remove_points_amount":
        try: amt = int(text)
        except:
            bot.reply_to(message, "⚠️ اكتب رقم صحيح." + FOOTER); return
        if amt < 1:
            bot.reply_to(message, "⚠️ الرقم لازم أكبر من 0." + FOOTER); return
        db.deduct_points(state["target_uid"], amt)
        new_pts = db.get_points(state["target_uid"])
        bot.reply_to(message, "✅ تم خصم *" + str(amt) + "* نقطة من " + (state.get("target_name") or "المستخدم") + ".\nالرصيد الجديد: *" + str(new_pts) + "*" + FOOTER)
        try:
            bot.send_message(state["target_uid"], "⚠️ *تم خصم " + str(amt) + " نقطة من حسابك*\n\nرصيدك الحالي: *" + str(new_pts) + "* نقطة" + FOOTER)
        except: pass
        user_states.pop(uid, None)
        return
    
    if awaiting == "set_cost_amount":
        try: amt = int(text)
        except:
            bot.reply_to(message, "⚠️ اكتب رقم صحيح." + FOOTER); return
        if amt < 0 or amt > 100:
            bot.reply_to(message, "⚠️ الرقم لازم من 0 لـ 100." + FOOTER); return
        key = state.get("cost_key", "")
        db.set_setting("cost_" + key, str(amt))
        bot.reply_to(message, "✅ تم تحديد سعر " + BUTTON_NAMES.get(key, key) + ": *" + str(amt) + "* نقطة." + FOOTER)
        user_states.pop(uid, None)
        return
    
    if awaiting == "set_referral_amount":
        try: amt = int(text)
        except:
            bot.reply_to(message, "⚠️ اكتب رقم صحيح." + FOOTER); return
        if amt < 0 or amt > 100:
            bot.reply_to(message, "⚠️ الرقم لازم من 0 لـ 100." + FOOTER); return
        db.set_setting("referral_points", str(amt))
        bot.reply_to(message, "✅ تم تحديد نقاط الإحالة: *" + str(amt) + "* نقطة." + FOOTER)
        user_states.pop(uid, None)
        return
    
    if awaiting == "sub_chat_id":
        ns = state.get("new_sub", {})
        ns["chat_id"] = text
        title = text
        try:
            chat = bot.get_chat(text)
            title = chat.title or chat.username or chat.first_name or text
        except:
            pass
        ns["title"] = title
        db.add_force_sub(ns["type"], ns["chat_id"], title, "")
        user_states.pop(uid, None)
        bot.reply_to(message, "✅ تم إضافة: *" + title + "*" + FOOTER)
        return
    
    if awaiting == "sub_title":
        ns = state.get("new_sub", {})
        ns["title"] = text
        state["new_sub"] = ns
        if ns.get("type") == "link":
            state["awaiting"] = "sub_link"
            user_states[uid] = state
            bot.reply_to(message, "🔗 ابعت اللينك الكامل." + FOOTER)
        else:
            state["awaiting"] = "sub_link_optional"
            user_states[uid] = state
            bot.reply_to(message, "🔗 ابعت لينك الدعوة أو skip." + FOOTER)
        return
    
    if awaiting in ("sub_link", "sub_link_optional"):
        ns = state.get("new_sub", {})
        ns["link"] = "" if text.lower() == "skip" else text
        db.add_force_sub(ns["type"], ns["chat_id"], ns["title"], ns["link"])
        user_states.pop(uid, None)
        bot.reply_to(message, "✅ تم إضافة: *" + ns["title"] + "*" + FOOTER)
        return
    
    if awaiting == "broadcast":
        if uid != DEVELOPER_ID: return
        users = db.get_all_users()
        sent = failed = 0
        for u in users:
            try:
                bot.copy_message(u, message.chat.id, message.message_id)
                sent += 1
            except: failed += 1
        bot.reply_to(message, "✅ نجح: " + str(sent) + "\n❌ فشل: " + str(failed) + FOOTER)
        user_states.pop(uid, None)
        return

def daily_tip_loop():
    tips_pool = [
        "💡 فعّل التحقق بخطوتين على كل حساباتك.",
        "🔑 كلمة مرور قوية = 12 حرف على الأقل + حروف كبيرة وصغيرة + أرقام + رموز.",
        "⚠️ متضغطش على لينكات مشبوهة.",
        "🔐 استخدم كلمات مرور مختلفة لكل حساب.",
        "🚨 أي حد يطلب منك كود OTP = نصاب.",
        "📱 راجع الأجهزة المتصلة بحساباتك.",
        "🛡️ استخدم مدير كلمات مرور.",
    ]
    time.sleep(3600)
    while True:
        try:
            tip = secrets.choice(tips_pool)
            users = db.get_all_users()
            for u in users:
                try:
                    bot.send_message(u, "🔔 *نصيحة اليوم:*\n\n" + tip + FOOTER)
                except Exception as _e: print("BT_ERR:", _e)
        except Exception as _e: print("BT_ERR:", _e)
        time.sleep(86400)

threading.Thread(target=daily_tip_loop, daemon=True).start()

print("✅ البوت شغال...")
bot.infinity_polling()
