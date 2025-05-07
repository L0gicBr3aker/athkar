from pyrogram import Client, filters, idle, types, errors, enums
from pyromod import listen
from datetime import datetime
from pytz import timezone
import asyncio, re, random, json, os
import redis.asyncio as redis


TIME_ZONE = "Asia/Riyadh"
TOKEN = "TOKEN_HERE"
SUDO_ID = 827315 # Use your telegram id
POST_TIME = 14400 # Post timing , in seconds (the default post time is 4hrs)
db = redis.Redis(decode_responses=True)
app = Client(
    "azkar-bot",
    api_id=API_ID_HERE, # use ur api id here
    api_hash="HASH_HERE", # use ur api hash here
    bot_token=TOKEN,
    in_memory=True
)
bot_id = app.bot_token.split(':')[0]
START_TEXT = """
↢ اهلًا بك {mention}

↢ في بوت الاذكار

↢ البوت يرسل اذكار وصوتيات دينية عشوائية كل 4 ساعات لجميع المشتركين بالخاص وجميع المجموعات المفعلة
↢ لتفعيلي بالمجموعة بس ضيفني وارفعني مشرف

↢ لايقاف الاشتراك برسائل البوت ارسل : /stop
↢ للاشتراك ارسل : /broad
"""

async def addUserToDataBase(user: types.User) -> bool:
    if not await db.sismember(bot_id+"users", user.id):
        await db.sadd(bot_id+"users", user.id)
        await db.sadd(bot_id+"broad", user.id)
        admins = [SUDO_ID]
        if await db.smembers(bot_id+"admins"):
            for admin in await db.smembers(bot_id+"admins"):
                admins.append(int(admin))
        if user.username:
            reply_markup = types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            user.first_name, url=f"https://t.me/{user.username}"
                        )
                    ]
                ]
            )
        else:
            reply_markup = None
        notify = (
            "↢ شخص جديد دخل الى البوت\n"
            f"↢ اسمه ( {user.mention} )\n"
            f"↢ ايديه ( `{user.id}` )\n"
            f"↢ يوزره ( {'@'+user.username if user.username else 'ماعنده يوزر'} )\n"
            f"↢ احصائيات المستخدمين ( {len(await db.smembers(bot_id+'users'))} )\n"
        )
        for admin in admins:
            try:
                await app.send_message(
                    admin,
                    notify,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            except errors.FloodWait as flood:
                await asyncio.sleep(flood.value)
            except Exception as e:
                print(e)
        return True
    else:
        return False
    
async def addChatToDataBase(chat: types.Chat) -> bool:
    if not await db.sismember(bot_id+"chats", chat.id):
        await db.sadd(bot_id+"chats", chat.id)
        await db.sadd(bot_id+"broad", chat.id)
        admins = [SUDO_ID]
        if await db.smembers(bot_id+"admins"):
            for admin in await db.smembers(bot_id+"admins"):
                admins.append(int(admin))
        if chat.username:
            reply_markup = types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            chat.title, url=f"https://t.me/{chat.username}"
                        )
                    ]
                ]
            )
        else:
            reply_markup = None
        notify = (
            "↢ تم تفعيل البوت بقروب جديد\n"
            f"↢ اسمه ( {chat.title} )\n"
            f"↢ ايدي ( `{chat.id}` )\n"
            f"↢ يوزر ( {'@'+chat.username if chat.username else 'مافي يوزر'} )\n"
            f"↢ احصائيات القروبات ( {len(await db.smembers(bot_id+'chats'))} )\n"
        )
        for admin in admins:
            try:
                await app.send_message(
                    admin,
                    notify,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            except errors.FloodWait as flood:
                await asyncio.sleep(flood.value)
            except Exception:
                pass
        return True
    else:
        return False

async def isAdmin(user_id: int) -> bool:
    admins = [SUDO_ID]
    if await db.smembers(bot_id+"admins"):
        for admin in await db.smembers(bot_id+"admins"):
            admins.append(int(admin))
    if user_id in admins:
        return True
    else:
        return False

async def checkGroupAdmin(user_id: int, chat_id: int) -> bool:
    status = (await app.get_chat_member(chat_id, user_id)).status
    if status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] and not await isAdmin(user_id):
        return False
    else:
        return True

@app.on_message(filters.private, group=1)
async def onPrivate(c: Client,m: types.Message):
    text = m.text
    admin = await isAdmin(m.from_user.id)
    await addUserToDataBase(m.from_user)
    
    if text and text == "/stop":
        await db.srem(bot_id+"broad", m.from_user.id)
        return await m.reply("↢ تم الغاء اشتراكك بالبوت , لن تتلقلى اي اذكار")
    
    if text == "/broad":
        await db.sadd(bot_id+"broad", m.from_user.id)
        return await m.reply("↢ تم اشتراكك بخدمة الاذكار ستتلقى الاذكار يوميا كل 4 ساعات")
    
    if text and text == "/start":
        if not admin:
            return await m.reply(START_TEXT.format(mention=m.from_user.mention), disable_web_page_preview=True, quote=True)
        else:
            reply_markup = types.ReplyKeyboardMarkup(
                [
                    [
                        types.KeyboardButton("الاحصائيات")
                    ],
                    [
                        types.KeyboardButton("تفعيل التواصل"),
                        types.KeyboardButton("تعطيل التواصل")
                    ],
                    [
                        types.KeyboardButton("رفع ادمن"),
                        types.KeyboardButton("تنزيل ادمن")
                    ],
                    [
                            types.KeyboardButton("الادمنية")
                    ],
                    [
                        types.KeyboardButton("اذاعة بالمجموعات"),
                        types.KeyboardButton("اذاعة بالخاص")
                    ],
                    [
                        types.KeyboardButton("تعيين قناة الصوتيات"),
                        types.KeyboardButton("جلب نسخة احتياطية")
                    ],
                    [
                        types.KeyboardButton("اضافة اذكار")
                    ],
                    [
                        types.KeyboardButton("الغاء")
                    ]
                ]
            )
            return await m.reply(
                "↢ اليك لوحة الادمن",
                reply_markup=reply_markup,
                quote=True,
                disable_web_page_preview=True
            )
    if text and admin:
        if re.match("^الاحصائيات$", text):
            chats = len(await db.smembers(bot_id+"chats"))
            users = len(await db.smembers(bot_id+"users"))
            broad = len(await db.smembers(bot_id+"broad"))
            return await m.reply(
                (
                    f"↢ المجموعات : ( {chats} )\n"
                    f"↢ المستخدمين : ( {users} )\n"
                    f"↢ المشتركين بالبوت : ( {broad} )\n"
                ),
                disable_web_page_preview=True,
                quote=True
            )
            
        if re.match("^تفعيل التواصل$", text):
            if await db.hget(bot_id, "ena-contact"):
                return await m.reply(
                    "↢ تم تفعيل التواصل من قبل",
                    quote=True
                )
            else:
                await db.hset(bot_id, "ena-contact", 1)
                return await m.reply(
                    "↢ تم تفعيل التواصل بنجاح",
                    quote=True
                )
                
        if re.match("^تعطيل التواصل$", text):
            if not await db.hget(bot_id, "ena-contact"):
                return await m.reply(
                    "↢ تم تعطيل التواصل من قبل",
                    quote=True
                )
            else:
                await db.hdel(bot_id, "ena-contact")
                return await m.reply(
                    "↢ تم تعطيل التواصل بنجاح",
                    quote=True
                )
                
        if re.match("^رفع ادمن$", text):
            admin_rep = await m.chat.ask(
                "↢ ارسل الان ايدي او يوزر الادمن",
                filters=filters.text
            )
            admin_id = admin_rep.text
            if admin_id == "الغاء":
                return await admin_rep.reply("↢ تم الغاء الامر", quote=True)
            if admin_id.isdigit():
                admin_id = int(admin_id)
            else:
                admin_id = admin_id.replace("@", "")
            try:
                user = await c.get_users(admin_id)
            except:
                return await admin_id.reply("↢ ايدي|يوزر الشخص غلط")
            if await db.sismember(bot_id+"admins", user.id):
                return await admin_rep.reply(
                    (
                        f"↢ المستخدم ( {user.mention} )\n"
                        "↢ ادمن من قبل"
                    ),
                    quote=True
                )
            else:
                await db.sadd(bot_id+"admins", user.id)
                return await admin_rep.reply(
                    (
                        f"↢ المستخدم ( {user.mention} )\n"
                        "↢ رفعته ادمن بالبوت"
                    ),
                    quote=True
                )
        
        if re.match("^تنزيل ادمن$", text):
            admin_rep = await m.chat.ask(
                "↢ ارسل الان ايدي او يوزر الادمن",
                filters=filters.text
            )
            admin_id = admin_rep.text
            if admin_id == "الغاء":
                return await admin_rep.reply("↢ تم الغاء الامر", quote=True)
            if admin_id.isdigit():
                admin_id = int(admin_id)
                if not await db.sismember(bot_id+"admins", admin_id):
                    return await admin_rep.reply(
                        (
                            f"↢ المستخدم ( [{admin_id}](tg://user?id={admin_id}) )\n"
                            "↢ مو ادمن من قبل"
                        ),
                        quote=True
                    )
                else:
                    await db.srem(bot_id+"admins", admin_id)
                    return await admin_rep.reply(
                        (
                            f"↢ المستخدم ( [{admin_id}](tg://user?id={admin_id}) )\n"
                            "↢ نزلته من ادمن البوت"
                        ),
                        quote=True
                    )
            else:
                admin_id = admin_id.replace("@", "")
            try:
                user = await c.get_users(admin_id)
            except:
                return await admin_id.reply("↢ ايدي|يوزر الشخص غلط")
            if not await db.sismember(bot_id+"admins", user.id):
                return await admin_rep.reply(
                    (
                        f"↢ المستخدم ( {user.mention} )\n"
                        "↢ مو ادمن من قبل"
                    ),
                    quote=True
                )
            else:
                await db.srem(bot_id+"admins", user.id)
                return await admin_rep.reply(
                    (
                        f"↢ المستخدم ( {user.mention} )\n"
                        "↢ نزلته من ادمن البوت"
                    ),
                    quote=True
                )
        
        if re.match("^الادمنية$", text):
            if not await db.smembers(bot_id+"admins"):
                return await m.reply(
                    "↢ ما في ادمن بالبوت",
                    quote=True
                )
            else:
                count = 1
                admins = "قائمة الادمن :\n"
                for admin in await db.smembers(bot_id+"admins"):
                    try:
                        user = await c.get_users(int(admin))
                        admins += f"{count} ) {user.mention}\n"
                        count += 1
                    except:
                        admins += f"{count} ) [{admin}](tg://user?id={admin})\n"
                        count += 1
                return await m.reply(
                    admins,
                    quote=True
                )
        
        if re.match("^اذاعة بالمجموعات$", text):
            ask_rep = await m.chat.ask(
                "↢ ارسل الاذاعة الحين"
            )
            if ask_rep.text and ask_rep.text == "الغاء":
                return await ask_rep.reply(
                    "↢ تم الغاء الامر",
                    quote=True
                )
            await ask_rep.reply("↢ يتم الاذاعة بالمجموعات الان , سيتم اعلامك فور انتهاء الاذاعة", quote=True)
            successed = 0
            failed = 0
            for group in await db.smembers(bot_id+"chats"):
                try:
                    await c.copy_message(
                        int(group),
                        m.chat.id,
                        ask_rep.id
                    )
                    successed += 1
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except:
                    failed += 1
            return await ask_rep.reply(
                f"↢ تم الاذاعة الى {successed} مجموعة\n↢ فشلت الاذاعة في {failed} مجموعة",
                quote=True
            )
        
        if re.match("^اذاعة بالخاص$", text):
            ask_rep = await m.chat.ask(
                "↢ ارسل الاذاعة الحين"
            )
            if ask_rep.text and ask_rep.text == "الغاء":
                return await ask_rep.reply(
                    "↢ تم الغاء الامر",
                    quote=True
                )
            await ask_rep.reply("↢ يتم الاذاعة بالخاص الان , سيتم اعلامك فور انتهاء الاذاعة", quote=True)
            successed = 0
            failed = 0
            for user in await db.smembers(bot_id+"users"):
                try:
                    await c.copy_message(
                        int(user),
                        m.chat.id,
                        ask_rep.id,
                    )
                    successed += 1
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except:
                    failed += 1
            return await ask_rep.reply(
                f"↢ تم الاذاعة الى {successed} شخص\n↢ فشلت الاذاعة الى {failed} شخص",
                quote=True
            )
        
        if re.match("^تعيين قناة الصوتيات$", text):
            channel = await m.chat.ask(
                "↢ ارسل اخر رابط رسالة من القناة الحين",
                filters=filters.text
            )
            if channel.text == "الغاء":
                return await channel.reply(
                    "↢ تم الغاء الامر",
                    quote=True
                )
            urls = re.findall("((www\.|http://|https://)(www\.)*.*?(?=(www\.|http://|https://|$)))", channel.text)
            if not urls:
                return await channel.reply(
                    "↢ لازم رابط",
                    quote=True
                )
            url = urls[0][0]
            username = url.split("/")[-2]
            msg_id = url.split("/")[-1]
            await db.set(bot_id+"channel", f"{username}&&&{msg_id}")
            return await channel.reply(
                f"↢ تم تعيين القناة ( @{username} )"
            )
        
        if re.match("^جلب نسخة احتياطية$", text):
            users = []
            chats = []
            admins = []
            broads = []
            for user in await db.smembers(bot_id+"users"):
                users.append(int(user))
            for chat in await db.smembers(bot_id+"chats"):
                chats.append(int(chat))
            for admin in await db.smembers(bot_id+"admins"):
                admins.append(int(admin))
            for broad in await db.smembers(bot_id+"broad"):
                broads.append(int(broad))
            data = {
                "bot_id": int(bot_id),
                "sudo_id": SUDO_ID,
                "data":{
                    "users": users,
                    "chats": chats,
                    "admins": admins,
                    "broads": broads
                }
            }
            file_id = random.randint(100,200)
            with open(f"./data{file_id}.json", "w+", encoding="utf-8") as f:
                f.write(json.dumps(data, indent=4, ensure_ascii=False))
            await m.reply_document(f"./data{file_id}.json")
            os.remove(f"./data{file_id}.json")
            return True
        
        if re.match("^اضافة اذكار$", text):
            zkr = await m.chat.ask(
                "↢ ارسل نص الاذكار الحين",
                filters=filters.text
            )
            if zkr.text == "الغاء":
                return await channel.reply(
                    "↢ تم الغاء الامر",
                    quote=True
                )
            with open("./azkar.json", "r", encoding="utf-8") as f:
                data = json.loads(f.read())
            data["azkar"].append(zkr.text)
            with open("./azkar.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(data, indent=4, ensure_ascii=False))
            return await zkr.reply("↢ تم اضافة الذكر الى قاعدة البيانات بنجاح", quote=True)



@app.on_message(filters.group, group=2)
async def onGroupChat(c: Client, m: types.Message):
    await addChatToDataBase(m.chat)
    if m.text and m.text == "تفعيل الاذكار":
        if not await checkGroupAdmin(m.from_user.id, m.chat.id):
            return await m.reply("↢ الأمر للمشرفين بش")
        else:
            if await db.sismember(bot_id+"broad", m.chat.id):
                return await m.reply("↢ الاذكار مفعلة من قبل")
            else:
                await db.sadd(bot_id+"broad", m.chat.id)
                return await m.reply("↢ تم تفعيل الأذكار بنجاح")
    
    if m.text and m.text == "تعطيل الاذكار":
        if not await checkGroupAdmin(m.from_user.id, m.chat.id):
            return await m.reply("↢ الأمر للمشرفين بش")
        else:
            if not await db.sismember(bot_id+"broad", m.chat.id):
                return await m.reply("↢ الاذكار معطلة من قبل")
            else:
                await db.srem(bot_id+"broad", m.chat.id)
                return await m.reply("↢ تم تعطيل الأذكار بنجاح")

async def autoPost():
    while not await asyncio.sleep(2.5):
        for broad in await db.smembers(bot_id+"broad"):
            now_utc = datetime.now(timezone('UTC'))
            now_ksa = now_utc.astimezone(timezone('Asia/Riyadh'))
            day = now_ksa.strftime("%A")
            hour = now_ksa.strftime("%I %p")
            if (str(day) == "Friday") and not await db.get(bot_id+f"b-{broad}-f"):
                try:
                    Surah_Alkahf = "/root/athkar/assets/Alkahf.pdf"
                    await app.send_document(
                        int(broad),
                        document=Surah_Alkahf,
                        caption="{إِنَّ اللَّهَ وَمَلَـٰٓئِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ يَـٰٓأَيُّهَا الَّذِينَ ءامَنُوا صَلُّوا عَلَيْهِ وَسَلِّمُوا تَسْلِيمًا}"
                    )
                    await db.set(bot_id+f"b-{broad}-f", 1, ex=86400)
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except Exception:
                    pass
            if str(hour) == "07 AM" and not await db.get(bot_id+f"b-{broad}-7"):
                try:
                    morning_image = "/root/athkar/assets/morning_image.png"
                    await app.send_photo(
                        int(broad),
                        photo=morning_image,
                    )
                    await db.set(bot_id+f"b-{broad}-7", 1, ex=3600)
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except Exception:
                    pass
            if str(hour) == "12 AM" and not await db.get(bot_id+f"b-{broad}-12"):
                try:
                    alwatr = """
                    من سجدَ وجد، ومن ألحّ على الله أُجيب!
                    ومن اتقى أُعطي، ومن صبرَ جُبر .. 
                    ولا يخذلُ ربك أحدًا.

                    أوترو فإن الله يحب الوتر : 🗯️
                    """
                    await app.send_message(
                        int(broad),
                        text=alwatr,
                    )
                    await db.set(bot_id+f"b-{broad}-12", 1, ex=3600)
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except Exception:
                    pass
            if str(hour) == "07 PM" and not await db.get(bot_id+f"b-{broad}-7"):
                try:
                    evening_image = "/root/athkar/assets/evening_image.png"
                    await app.send_photo(
                        int(broad),
                        photo=evening_image,
                    )
                    await db.set(bot_id+f"b-{broad}-7", 1, ex=3600)
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except Exception:
                    pass
            if not await db.get(bot_id+f"b-{broad}"):
                await db.set(bot_id+f"b-{broad}", 1, ex=POST_TIME)
                with open("./azkar.json", "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                try:
                    await app.send_message(
                        int(broad),
                        random.choice(data["azkar"]),
                        disable_web_page_preview=True
                    )
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except:
                    pass
                if await db.get(bot_id+"channel"):
                    spl = str(await db.get(bot_id+"channel")).split("&&&")
                    last_msg_id = int(spl[1])
                    try:
                        await app.send_audio(
                            int(broad),
                            f"https://t.me/{spl[0]}/{random.randint(last_msg_id-100, last_msg_id)}",
                        )
                    except errors.FloodWait as flood:
                        await asyncio.sleep(flood.value)
                    except:
                        pass
                try:
                    await app.send_message(
                        int(broad),
                        "-",
                        disable_web_page_preview=True
                    )
                except errors.FloodWait as flood:
                    await asyncio.sleep(flood.value)
                except:
                    pass

async def main():
    await app.start()
    print("Client @"+ app.me.username +" Started")
    asyncio.create_task(autoPost())
    print("Task Created")
    await idle()

asyncio.get_event_loop().run_until_complete(main())
