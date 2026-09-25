import telebot
import ccxt
import time

# 1. إعدادات مهلة الاتصال
telebot.apihelper.CONNECT_TIMEOUT = 30
telebot.apihelper.READ_TIMEOUT = 30

# 2. مفتاح البوت ومنصة بينانس
BOT_TOKEN = "8869967735:AAHutoQAoSlLobRNk81dZsaam5kQNpLtjSQ"
bot = telebot.TeleBot(BOT_TOKEN)
exchange = ccxt.binance()

# حساب التداول التجريبي الافتراضي
portfolio = {
    'USDT': 55.0,  # رصيد الـ USDT المتاح
    'assets': {}   # العملات المشتراة (مثال: {'BTC': {'amount': 0.001, 'buy_price': 80000}})
}

def safe_send(chat_id, text):
    try:
        bot.send_message(chat_id, str(text), parse_mode='Markdown')
    except Exception as e:
        print(f"خطأ في الإرسال: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 *بوت التداول التجريبي جاهز!*\n\n"
        "📌 *الأوامر المتاحة:*\n"
        "▫️ `/balance` - عرض رصيد USDT المتاح\n"
        "▫️ `/price BTC/USDT` - عرض سعر العملة المباشر\n"
        "▫️ `/buy BTC 20` - شراء تجريبي لمبلغ 20 USDT\n"
        "▫️ `/sell BTC` - بيع كل الكمية المملوكة من العملة\n"
        "▫️ `/portfolio` - عرض تفاصيل المحفظة والأرباح/الخسائر"
    )
    safe_send(message.chat.id, welcome_text)

@bot.message_handler(commands=['balance'])
def handle_balance(message):
    usdt = portfolio['USDT']
    msg = f"💵 *رصيدك التجريبي المتاح:* `{usdt:,.2f} USDT`"
    safe_send(message.chat.id, msg)

@bot.message_handler(commands=['price'])
def handle_price(message):
    try:
        parts = message.text.split()
        coin = parts[1].upper() if len(parts) > 1 else 'BTC'
        symbol = coin if '/' in coin else f"{coin}/USDT"
        
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        msg = f"📈 *سعر {symbol} المباشر:* `{price:,.2f} USDT`"
    except Exception as e:
        msg = "❌ حدث خطأ، تأكد من الرمز (مثال: `/price BTC` أو `/price ETH/USDT`)"
    safe_send(message.chat.id, msg)

@bot.message_handler(commands=['buy'])
def handle_buy(message):
    try:
        parts = message.text.split()
        if len(parts) < 3:
            safe_send(message.chat.id, "⚠️ *صيغة الشراء:* `/buy BTC 20` (العملة ثم المبلغ بـ USDT)")
            return
            
        coin = parts[1].upper()
        symbol = coin if '/' in coin else f"{coin}/USDT"
        base_coin = symbol.split('/')[0]
        amount_usdt = float(parts[2])

        if amount_usdt <= 0 or amount_usdt > portfolio['USDT']:
            safe_send(message.chat.id, f"❌ الرصيد غير كافٍ! رصيدك المتاح هو `{portfolio['USDT']:,.2f} USDT`")
            return

        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        crypto_amount = amount_usdt / price

        # خصم USDT وإضافة العملة للمحفظة
        portfolio['USDT'] -= amount_usdt
        if base_coin in portfolio['assets']:
            portfolio['assets'][base_coin]['amount'] += crypto_amount
        else:
            portfolio['assets'][base_coin] = {'amount': crypto_amount, 'buy_price': price}

        msg = (
            f"✅ *تم الشراء التجريبي بنجاح!*\n"
            f"🔹 العملة: `{base_coin}`\n"
            f"🔹 الكمية: `{crypto_amount:.6f}`\n"
            f"🔹 بسعر: `{price:,.2f} USDT`\n"
            f"💵 المتبقي في الرصيد: `{portfolio['USDT']:,.2f} USDT`"
        )
    except Exception as e:
        msg = "❌ حدث خطأ أثناء تنفيذ أمر الشراء، تأكد من اسم العملة والمبلغ."
    safe_send(message.chat.id, msg)

@bot.message_handler(commands=['sell'])
def handle_sell(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            safe_send(message.chat.id, "⚠️ *صيغة البيع:* `/sell BTC` (اسم العملة)")
            return
            
        coin = parts[1].upper().replace('/USDT', '')
        if coin not in portfolio['assets'] or portfolio['assets'][coin]['amount'] <= 0:
            safe_send(message.chat.id, f"❌ أنت لا تمتلك أي رصيد من عملة `{coin}`!")
            return

        symbol = f"{coin}/USDT"
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']

        crypto_amount = portfolio['assets'][coin]['amount']
        total_usdt = crypto_amount * current_price

        # إضافة USDT وإلغاء العملة من المحفظة
        portfolio['USDT'] += total_usdt
        del portfolio['assets'][coin]

        msg = (
            f"✅ *تم البيع التجريبي بنجاح!*\n"
            f"🔹 العملة: `{coin}`\n"
            f"🔹 العائد الإجمالي: `{total_usdt:,.2f} USDT`\n"
            f"🔹 بسعر البيع: `{current_price:,.2f} USDT`\n"
            f"💵 رصيدك المتاح الان: `{portfolio['USDT']:,.2f} USDT`"
        )
    except Exception as e:
        msg = "❌ حدث خطأ أثناء تنفيذ عملية البيع."
    safe_send(message.chat.id, msg)

@bot.message_handler(commands=['portfolio'])
def handle_portfolio(message):
    try:
        total_value = portfolio['USDT']
        msg = f"📊 *تفاصيل المحفظة التجريبية:*\n\n"
        msg += f"💵 *رصيد كاش:* `{portfolio['USDT']:,.2f} USDT`\n"

        if portfolio['assets']:
            msg += "\n🪙 *العملات المملوكة:*\n"
            for coin, data in portfolio['assets'].items():
                symbol = f"{coin}/USDT"
                ticker = exchange.fetch_ticker(symbol)
                curr_price = ticker['last']
                asset_value = data['amount'] * curr_price
                total_value += asset_value
                msg += f"▫️ *{coin}:* `{data['amount']:.6f}` (قيمتها: `{asset_value:,.2f} USDT`)\n"
        
        msg += f"\n💎 *القيمة الكلية للمحفظة:* `{total_value:,.2f} USDT`"
    except Exception as e:
        msg = "❌ حدث خطأ أثناء عرض المحفظة."
    safe_send(message.chat.id, msg)

def run_bot():
    while True:
        try:
            print("بوت التداول التجريبي يعمل الآن ومستقر...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"انقطع الاتصال، جاري إعادة المحاولة خلال 5 ثوانٍ... الخطأ: {e}")
            time.sleep(5)

if __name__ == '__main__':
    run_bot()
