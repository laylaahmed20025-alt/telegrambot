# 🤖 SnatchTik Telegram Bot

بوت تيليجرام يعمل بنفس الـ APIs الموجودة في `app.py` الأساسي.

---

## 📁 هيكل الملفات

```
telegram-bot/
├── bot.py              # الكود الرئيسي للبوت
├── requirements.txt    # مكتبات البوت فقط
├── Dockerfile          # Docker image مستقل
└── .env.example        # مثال على متغيرات البيئة
```

---

## ⚙️ المتطلبات

| متغير البيئة         | مصدره                          | يُستخدم لـ         |
|----------------------|-------------------------------|-------------------|
| `BOT_TOKEN`          | @BotFather على تيليجرام       | تشغيل البوت       |
| `TIKTOK_API_KEY`     | tikwmapi.com                  | تحميل TikTok      |
| `RAPIDAPI_KEY`       | rapidapi.com                  | تحميل Facebook    |
| `FASTSAVER_API_KEY`  | api.fastsaver.io              | تحميل Instagram   |

---

## 🚀 التشغيل محلياً (للاختبار)

```bash
cd telegram-bot
pip install -r requirements.txt

# Windows
set BOT_TOKEN=xxx
set TIKTOK_API_KEY=xxx
set RAPIDAPI_KEY=xxx
set FASTSAVER_API_KEY=xxx
python bot.py

# Linux/Mac
export BOT_TOKEN=xxx && python bot.py
```

---

## 🚂 النشر على Railway

### الخطوات:

1. **سجّل في Railway**: https://railway.app
2. **أنشئ مشروع جديد** → "Deploy from GitHub repo"
3. **اختر الـ repo** وضع **Root Directory = `telegram-bot`**
4. في **Variables** أضف:
   ```
   BOT_TOKEN        = xxxx
   TIKTOK_API_KEY   = xxxx
   RAPIDAPI_KEY     = xxxx
   FASTSAVER_API_KEY= xxxx
   ```
5. Railway سيكتشف الـ `Dockerfile` تلقائياً ويعمل build
6. ✅ البوت يعمل بدون أي domain أو port — لأنه يعمل بـ **Polling** مش Webhook

> ⚠️ **Railway Free Tier**: بيديك 5 دولار كريديت شهرياً — البوت البسيط ده هيشتغل شهرين-3 شهور مجاناً.

---

## ✅ المزايا (الإيجابيات)

| الميزة | التفاصيل |
|--------|----------|
| 🔁 نفس الـ API | لا تكلفة إضافية، نفس الـ keys |
| ⚡ سريع | لا UI، لا JS، طلب مباشر |
| 🆓 Polling | لا يحتاج HTTPS أو Domain |
| 🔒 آمن | env variables فقط، لا hardcoded keys |
| 📱 Mobile-first | تيليجرام نفسه mobile-first |

---

## ⚠️ السلبيات والمشاكل المتوقعة

### 1. 🔗 روابط التحميل المباشرة (أكبر مشكلة!)
**المشكلة:** الـ API بيرجع روابط CDN مؤقتة (تنتهي خلال 30-60 دقيقة).
- الـ Inline Keyboard buttons بترسل اليوزر للرابط مباشرة
- لو الرابط انتهى → "Link expired" أو فيديو مش شغال

**الحل المؤقت (المستخدم حالياً):**
بنرسل الرابط as-is، المستخدم يضغط ويحمّل فوراً.

**الحل الدائم (للمستقبل):**
استخدم `/stream` endpoint من `app.py` كـ proxy — بس ده يحتاج البوت يكون على نفس الـ server مع الـ web app، أو يكون عنده proxy مستقل.

---

### 2. 📤 رفع الفيديو مباشرة لتيليجرام
**المشكلة:** تيليجرام بوت API عنده حد أقصى **50 MB** لو رفعت file مباشرة.
معظم فيديوهات TikTok < 50MB، بس Facebook/Instagram ممكن يتعدوا ده.

**الحل الحالي:** بنرسل **InlineKeyboardButton** بـ URL مباشر (المستخدم يفتحه في browser).

**الحل الدائم:** تستخدم `send_video(url=...)` بدل رفع الملف — تيليجرام بيعمل stream مباشر (بس بيحتاج URL مستقر).

---

### 3. 🛡️ Rate Limits
**المشكلة:** لو عندك كتير مستخدمين، هتضرب rate limit للـ APIs.
- TikWM: حسب خطتك
- RapidAPI: حسب اشتراكك

**الحل:** أضف TTLCache زي app.py، أو ادفع للـ premium plan.

---

### 4. 🌐 Facebook Videos (Private)
**المشكلة:** Facebook API شغال بس مع الفيديوهات **العامة (Public)** فقط.
لو الفيديو على حساب خاص أو في group مغلق → هيفشل.

**الحل:** وضّح للمستخدم في الرد.

---

### 5. 📸 Instagram Albums
**المشكلة:** البوم الصور (10+ صور) مش ممكن يتبعت كـ media group بسهولة لأن الروابط CDN قد تنتهي.

**الحل الحالي:** بنرسل Inline Buttons بعدد الصور (max 10).

---

## 🎯 اللي بيمشي كويس

- ✅ TikTok فيديو بدون علامة مائية (HD)
- ✅ TikTok MP3 (موسيقى فقط)
- ✅ Facebook فيديو HD/SD
- ✅ Instagram فيديو
- ✅ Instagram صورة واحدة
- ✅ Instagram البوم (كـ buttons)
- ✅ رسائل خطأ واضحة بالعربي
- ✅ كاش الـ API مش مطبّق هنا (تقدر تضيفه لاحقاً)

---

## 🔮 تحسينات مستقبلية

- [ ] إضافة TTLCache لتقليل API calls
- [ ] `/stream` proxy عشان الروابط ما تنتهيش
- [ ] دعم Inline Mode (يبحث الناس بدون فتح البوت)
- [ ] إحصائيات: كم مستخدم، كم تحميل
- [ ] دعم YouTube (لو غيّرت الـ API)
