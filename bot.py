#native imports
from native.encrypt import encrypt, decrypt
from native.genwallet import gen_mnemonics, import_wallet,  get_addr
from native.jet_upd import update
from native.deploy import deploy
from native.transfer_jet import transfer_jet
from native.transfer_ton import send_ton
from native.wallet_bal import jetton_bal, ton_bal
from native import position


#swap import
from swap.jetton_ton import ton_swap
from swap.ton_jetton import jetton_swap
from swap.prices import main_price
from swap.info import get_symbol, get_decimal, get_mc, get_name, get_pool, get_price, get_url, get_lp, get_pair

#db import 
from database.db import User, Trade, UserData, Bridge, Airdrop

from database.trades import Trades

from bridge.bridge import exchange, minimum, exchange_status, output

from airdrop import airdrop
import re
from pnl import pnlpic
from fees import bot_fees, ref_fees, sell_fees
import telebot
from telebot import types
from telebot.util import antiflood, extract_arguments
import time
import json
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

"""
Initialising database
"""
db_trades = Trades()
db_user = User()
db_trade = Trade()
db_userd = UserData()
db_bridge = Bridge()
db_airdrop = Airdrop()


db_user.setup()
db_trade.setup()
db_userd.setup()
db_trades.setup()
db_bridge.setup()



FEES_ADDRESS = 'UQB9dNq-m1ZGrlLMgujPeQP6sIyKTKMUeWWO0ImWPtIEuQi9'

TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)

bot_info = bot.get_me()


def extract_ca(url: str):
    pattern = r"track-(.*)"
    
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else: 
        return None
    
def extract_ca_pnl(url: str):
    pattern = r"genpnl-(.*)"
    
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    else: 
        return None
    
def GenPnL(message, token):
    owner = message.chat.id
    name = get_name(token)
    symbol = get_symbol(token)
    buyamt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
    buymc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner, token)
    pnl = 1 if round((get_mc(token)-buymc)/buymc*100, 2) > 10000 else round((get_mc(token)-buymc)/buymc*100, 2)
    worth = 1 if round((get_mc(token)/buymc)*buyamt, 2) > 10000 else round((get_mc(token)/buymc)*buyamt, 2)
    
    pnlpic(pnl,symbol,buyamt, worth, owner)
    
    photo = open(f'media/output{owner}.jpg', 'rb')
    
    msg = f"""{'💀' if pnl < 0 else '🚀'} {1 if pnl > 10000 else round(pnl, 2)}% {symbol}/TON 

Earn 20% commissions by sharing your referral link 

`https://t.me/{bot_info.username}?start={owner}-{token}`
    
    """
    bot.send_photo(owner, photo, msg, 'Markdown')
    

def abbreviate(x):
    abbreviations = ["", "K", "M", "B", "T", "Qd", "Qn", "Sx", "Sp", "O", "N", 
    "De", "Ud", "DD"]
    
    if x < 1000:
        return str(x)
    
    a = 0
    while x >= 1000 and a < len(abbreviations) - 1:
        x /= 1000.0
        a += 1
    
    return f"{x:.2f} {abbreviations[a]}"


def sbuy(message, token, amt):
    owner = message.chat.id
    slip = db_user.get_slippage(owner=owner)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    wallet = db_user.get_wallet(owner)
    bal = asyncio.run(ton_bal(mnemonics))
    if bal > amt:
        asyncio.run(deploy(mnemonics))
        amount = bot_fees(amt, owner)
        x = bot.send_message(owner, f"Attempting a buy at ${abbreviate(get_mc(token))} MCap")
        buy = asyncio.run(jetton_swap(token, mnemonics, amount))
        time.sleep(25)
        if buy == 1:
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amount)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            bot.delete_message(owner, x.message_id)
            bot.send_message(owner, f"Bought {get_name(token)} at ${abbreviate(get_mc(token))}")
        else:
            bot.send_message(owner, "⚠️ Buy failed")
            
    else:
        bot.send_message(owner, "⚠️ Balance is low")
        
def sell(message, addr, amount):
    owner = message.chat.id
    slip = db_user.get_slippage(owner=owner)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    wallet = db_user.get_wallet(owner)
    j_bal = asyncio.run(jetton_bal(addr, wallet))
    t_bal = asyncio.run(ton_bal(mnemonics))
    if j_bal >= amount and t_bal > 0.3:
        x  = bot.send_message(owner, f"Attempting a sell at ${abbreviate(get_mc(addr))} MCap")
        dec1 = asyncio.run(update(addr))
        dec = int(dec1['decimals'])
        print(type(dec))
        decimal = 10**dec
        print(decimal)
        j_price = asyncio.run(main_price(amount, addr, decimal))
        print(j_price)
        selled = asyncio.run(ton_swap(addr,mnemonics,amount))
        time.sleep(30)
        x = bot_fees(j_price, owner)
        amt = sell_fees(j_price)
        
        if selled == 1:
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amt)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amt + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            
            bot.send_message(owner, f"Successfully sold {amount} tokens")
        else:
            bot.send_message(owner, "⚠️ Failed to swap tokens")
            
    else:
        bot.send_message(owner, "⚠️Swap failed make sure there's enough Ton for gas or token amount is enough")


def track(message, token):
    owner = message.chat.id
    #token = db_trades.get_last_ca(owner)
    wallet = db_user.get_wallet(owner)
    token_bal = asyncio.run(jetton_bal(token, wallet))
    slip = db_user.get_slippage(owner)
    name = get_name(token)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    symbol = get_symbol(token)
    pool = get_pool(token)
    lp = get_lp(token)
    pair = get_pair(token)
    if token_bal > 0:
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})
                """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
        btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
        btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh1')
        btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
        markup.add(btn1,btn12,btn13)
        markup.add(btn11, row_width=1)
        markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
        bot.send_message(owner, msg, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)
        #bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(owner, "Zero Token Balance")

#Dev commands 

@bot.message_handler(commands=['getstats'])
def getstats(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        msg = ""
        stats = db_userd.get_users()
        for stat in stats:
            if stat[4] >= 1.0: 
                msg += f"{stat[1]}, {stat[4]}\n"
                db_userd.update_referrals_vol(0.0, stat[0])
            print(msg)    
        with open('pays.txt', 'w') as f:
            f.writelines(msg)
        doc = open('pays.txt', 'r')
        bot.send_document(messager,doc)
        
                


@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        send = bot.send_message(message.chat.id,"Enter message to broadcast")
        bot.register_next_step_handler(send,sendall)
        
    else:
        bot.reply_to(message, "You're not allowed to use this command")
        
        

db_userd.add_user(username_= 7034272819, wallet="UQCs_PQIq-FjctnPvWq8756ohqzIsDWYCvm4SjfpAy-SpDxG", referrer=7034272819)
      
def sendall(message):
    users = db_user.get_users()
    for chatid in users:
        try:
            msg = antiflood(bot.send_message, chatid, message.text)
        except Exception as e:
            print(e)
        
    bot.send_message(message.chat.id, "done")
    

@bot.message_handler(commands=['userno'])
def userno(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        x = db_user.get_users()
        bot.reply_to(message,f"Total bot users: {len(x)}")
    else:
        bot.reply_to(message, "admin command")


@bot.message_handler(commands=['start'])
def start(message):
    owner = message.chat.id
    mnemonics = gen_mnemonics() if db_user.get_wallet(owner) == None else eval(decrypt(db_user.get_mnemonics(owner)))
    wallet_address = get_addr(mnemonics)
    welcom = f"""*Welcome to NeuTon Trade Bot !*

Experience the fastest Ton Blockchain trading bot.

*Your Wallet Address:* `{wallet_address}`

Has been automatically generated for you

To view your 24-word key phrase, click the wallet button below.

*Ready to trade?*

Simply paste a jetton contract address to get started.
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton(f"{wallet_address[:10]}...", callback_data="wal")
    btn2 = types.InlineKeyboardButton(f"{asyncio.run(ton_bal(mnemonics))} Ton", callback_data='us')
    btn3 = types.InlineKeyboardButton("💳 Wallet", callback_data='wallett')
    btn4 = types.InlineKeyboardButton("Positions", callback_data="position")
    btn7 = types.InlineKeyboardButton("Bridge", callback_data='bridge')
    btn5 = types.InlineKeyboardButton("Support Community", url="https://t.me/neuton_support")
    btn6 = types.InlineKeyboardButton("💡Bot Manual", url="https://neuton-bot.gitbook.io/neuton-trade-bot")
    btn8 = types.InlineKeyboardButton("Referrals", callback_data="reff")
    btn9 = types.InlineKeyboardButton('Mass Airdrop', callback_data='airdrop')
    
    
    markup.add(btn1, btn2, btn3, btn4,btn7,btn8,btn9, btn5, btn6)
    new_nmemonics = encrypt(mnemonics)
    referrer = extract_arguments(message.text)
    if extract_arguments(message.text):
        if str(referrer).startswith('track'):
            ca = extract_ca(referrer)
            track(message, ca)
        elif str(referrer).startswith('genpnl'):
            ca = extract_ca_pnl(referrer)
            GenPnL(message, ca)
            bot.delete_message(owner, message.message_id)    
        elif str(referrer).isdigit():
            if referrer == owner:
                bot.send_message(owner, "You can't be your own referrer")
                db_userd.add_user(owner, wallet_address, 7034272819)
                db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
            else:
                if db_userd.get_referrer(referrer) == None:
                    bot.send_message(owner, "Referrer not in database")
                    db_userd.add_user(owner, wallet_address, 7034272819)
                    db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                    bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
                else:
                    if db_userd.get_referrer(owner) == None:
                        db_userd.add_user(owner, wallet_address, referrer=referrer)
                        ref = db_userd.get_referrals(referrer)
                        reff = ref + 1
                        db_userd.update_referrals(reff, referrer)
                        db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                        bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
                    else:
                        db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                        bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
        else:
            pass
    else:
        db_userd.add_user(owner, wallet_address, 7034272819)
        db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
        bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
    
    
@bot.message_handler(commands=['wallet'])
def view_wallet(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    print(wallet)
    mnemonics = db_user.get_mnemonics(owner)
    ne = eval(decrypt(mnemonics))
    new = ' '.join(ne)
    msg = f"""
    Wallet Address: `{wallet}`
    
Pass Phrase:

`{new}`

⚠️ *Please delete this message after copying your pass phrase!!!*
    """
    bot.send_message(owner, msg, 'Markdown')
    
    
@bot.message_handler(commands=['support'])
def support(message):
    bot.reply_to(message, "For help or support join the official support community https://t.me/neuton_support\n You can read the docs for detailed example on bot usage https://neuton-bot.gitbook.io/neuton-trade-bot")

@bot.message_handler(commands=['referrals'])
def ree(message):
    owner = message.chat.id
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('❌️ Close', callback_data='cancel')
    markup.add(btn)
    msg = f"""*Referral Program*
        
Join our Referral program and earn 20% From your referrers trading fees.
        
How It Works:

Join our platform and get your unique referral link. 

`https://t.me/{bot_info.username}?start={owner}`

Invite others to trade with us by sharing your referral link via social media, email, or word of mouth.

Once your referrals start trading, you'll receive 20% of their trading fees, directly credited to your wallet.

*Referral Stats*

*Referrals*: {db_userd.get_referrals(owner)}

*Rewards*: {round(db_userd.get_referrals_vol(owner), 2)}
"""

    bot.send_message(owner, msg, 'Markdown',reply_markup=markup)

@bot.message_handler(commands=['positions'])
def pos(message):
    owner = message.chat.id 
    wallet = db_user.get_wallet(owner)
    msg = "Open Positions\n\n"
    pos = asyncio.run(position.main(wallet))
    for i in pos:
            msg += f"[${i['jetton']['name']}](https://t.me/{bot_info.username}?start=track-{position.str_addr(i['jetton']['address'])}) *$ 0.0 Ton *\n"
    markup = types.InlineKeyboardMarkup()
    btn= types.InlineKeyboardButton('❌️ Close', callback_data="cancel")
    markup.add(btn)
    bot.send_message(owner, msg, parse_mode='Markdown', reply_markup=markup)
    
    
@bot.message_handler(commands=['bridge'])
def brid(message):
        owner = message.chat.id
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton('Ton to others', callback_data='tonbridge')
        btn2 = types.InlineKeyboardButton('ETH --> TON', callback_data='ethton')
        btn3 = types.InlineKeyboardButton('SOL --> TON', callback_data='solton')
        btn4 = types.InlineKeyboardButton('BASE --> TON', callback_data='baseton')
        btn5 = types.InlineKeyboardButton('BTC --> TON', callback_data='btcton')
        btn6 = types.InlineKeyboardButton('BNB --> TON', callback_data='bnbton')
        btn7 = types.InlineKeyboardButton('USDT(ERC20) --> TON', callback_data='ercton')
        btn8 = types.InlineKeyboardButton('USDT(TRC20) --> TON', callback_data='trcton')
        btn9 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        
        msg = """
        Bridge from one network to Ton using the built in Bridge Mode
        
Select the chain you're bridging from and follow the prompt after

Tap on *Ton to others* To bridge from Ton to other chains         

        """
        
        markup.add(btn1, btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9)
        
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
          

@bot.message_handler(commands=['airdrop'])
def airdroped(message):
    owner = message.chat.id
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    msg = f"""

Easily transfer tokens to up to 256 TON addresses, each with a different amount.


⚠️ Ensure your TON Wallet has at least 2 TON to cover both Bot Fees (1 TON) and Network Fees.
Your airdrop wallet for this operation is:
`{asyncio.run(airdrop.get_wallet(mnemonics))}` (same mnemonics as your bot wallet).

⚠️ Make sure all tokens are sent to the designated wallet 
`{asyncio.run(airdrop.get_wallet(mnemonics))}` 

⚠️ before proceeding to avoid errors and unnecessary bot fees.
Send the wallet addresses and corresponding amounts, separated by commas, as shown in the example below. Ensure the list contains fewer than 256 addresses.
Example:

```
address1, amount
address2, amount
address3, amount
```

Click the button below to continue.
        """
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("✅️ Continue", callback_data='startmass')
    btn2 = types.InlineKeyboardButton('❌️ Cancel', callback_data='cancel')
        
    markup.add(btn1,btn2)
    bot.send_message(owner, msg, 'Markdown', reply_markup=markup)

@bot.message_handler(commands=['withdraw'])
def withdraw(message):
    bot.reply_to(message, "Reply to this message with the wallet address to withdraw to and ton amount seperated by comma\nExample: WITHDRAW-WALLET, 10")
    bot.register_next_step_handler(message, tonwithdraw)
    
def tonwithdraw(message):
    msg = message.text
    all = msg.split(",")
    owner = message.chat.id
    mn = db_user.get_mnemonics(owner)
    mnemonics = eval(decrypt(mn))
    wallet = all[0]
    amount = float(all[1])
    print(wallet)
    print(amount)
    bal = asyncio.run(ton_bal(mnemonics))
    try:
        if bal >= amount:
            asyncio.run(send_ton(wallet, amount,mnemonics))
            time.sleep(15)
            msg = f"""Sent {amount} Ton to {wallet} with [Tx Hash](https://tonscan.org/address/{wallet}#transactions)"""
            bot.send_message(message.chat.id, msg, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(message.chat.id, "⚠️ Amount higher than Wallet Balance")
            
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "⚠️ Transaction could not be prossesed")
        
    
    

"""
This part of the code deals with Token Buy or Sell
"""
@bot.message_handler(func=lambda message: True)
def trade(message):
    try:
        token = message.text
        print(token)
        name = get_name(token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        owner = message.chat.id
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        #decimal = get_decimal(token)
        symbol = get_symbol(token)
        pool = get_pool(token)
        mc = get_mc(token)
        price = get_price(token)
        lp = get_lp(token)
        pair = get_pair(token)
        wallet = db_user.get_wallet(owner)
        slip = db_user.get_slippage(owner)
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn1 = types.InlineKeyboardButton("🔃 Refresh", callback_data='refresh_view')
        btn2 = types.InlineKeyboardButton("📊 Chart", url=f"{chart}")
        btn3 = types.InlineKeyboardButton('🔎 Scan', url=f"https://t.me/TonChainScannerBot?start={token}")
        btn4 = types.InlineKeyboardButton('💰Buy 1 Ton', callback_data='buy1')
        btn5 = types.InlineKeyboardButton('💰 Buy 5 Ton', callback_data='buy5')
        btn6 = types.InlineKeyboardButton('💰 Buy 10 Ton', callback_data='buy10')
        btn7 = types.InlineKeyboardButton('💰 Buy 15 Ton', callback_data='buy15', )
        btn8 = types.InlineKeyboardButton('💰 Buy 20 Ton', callback_data='buy20')
        btn9 = types.InlineKeyboardButton('💰 Buy X Ton', callback_data='buyx')
        btn10 = types.InlineKeyboardButton('❌️ Cancel', callback_data='cancel')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        btn12 = types.InlineKeyboardButton("Slippage ⚙", callback_data='s')
        
        
        markup.add(btn2,btn1,btn3)
        markup.add(btn11)
        markup.add(btn4,btn5,btn6,btn7,btn8,btn9,btn10)
        
        
        msg = f""" 
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
 
Ton: {asyncio.run(ton_bal(mnemonics))}
 
💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}`
 
📈 *M Cap*: ${abbreviate(get_mc(token))} |💵 ${get_price(token)} 
 
♻️ *Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 
 
        """
       
        bot.send_message(message.chat.id, msg, 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
        #db_trades.add(owner, name, token)
        db_trades.add(owner, name, token)
        
    except Exception as e:
        bot.send_message(message.chat.id, "Invalid Token")
        print(e)



@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    owner = call.message.chat.id
    token = 'EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE' if db_trades.get_last_ca(owner) == None else db_trades.get_last_ca(owner)
    name = get_name(token)
    symbol = get_symbol(token)
    lp = get_lp(token)
    pair = get_pair(token)
    pool = get_pool(token)
    wallet = db_user.get_wallet(owner)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    slip = db_user.get_slippage(owner)
    
    if call.data == 'wallett':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss: `{db_user.get_wallet(owner)}`
        
Balance: *{asyncio.run(ton_bal(mnemonics))} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🏦 Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('🏦 Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('🔎 Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('🔃 Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('🔙 Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
    elif call.data == 'track':
        bot.pin_chat_message(owner, call.message.message_id)
        
    
    elif call.data =='wwithdraw':
        withdraw(call.message)
        
    elif call.data == 'deposit':
        print(call.data)
        msg = f"""Deposit Ton into your address
        
        
`{db_user.get_wallet(owner)}` (tap to copy)

Manually Send ton to the address above 
        """
        
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Back', callback_data='back')
        markup.add(btn)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup, parse_mode='Markdown')
        
        
    elif call.data == 'view':
        view_wallet(call.message)
        
    elif call.data == 'airdrop':
        msg = f"""

Easily transfer tokens to up to 256 TON addresses, each with a different amount.


⚠️ Ensure your TON Wallet has at least 2 TON to cover both Bot Fees (1 TON) and Network Fees.
Your airdrop wallet for this operation is:
`{asyncio.run(airdrop.get_wallet(mnemonics))}` (same mnemonics as your bot wallet).

⚠️ Make sure all tokens are sent to the designated wallet 
`{asyncio.run(airdrop.get_wallet(mnemonics))}` 

⚠️ before proceeding to avoid errors and unnecessary bot fees.
Send the wallet addresses and corresponding amounts, separated by commas, as shown in the example below. Ensure the list contains fewer than 256 addresses.
Example:

```
address1, amount
address2, amount
address3, amount
```

Click the button below to continue.
        """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("✅️ Continue", callback_data='startmass')
        btn2 = types.InlineKeyboardButton('❌️ Cancel', callback_data='cancel')
        
        markup.add(btn1,btn2)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
    elif call.data == 'startmass':
        send = bot.send_message(owner, "send Jetton Address")
        bot.register_next_step_handler(send, air)
        
        
    elif call.data == 'wrefresh':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss : `{db_user.get_wallet(owner)}`
        
Balance : *{asyncio.run(ton_bal(mnemonics))} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🏦 Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('🏦 Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('🔎 Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('🔃 Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('🔙 Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
    elif call.data == 'home':
        bot.delete_message(owner, call.message.message_id)
        start(call.message)
    
    
    elif call.data == 'back':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss : `{db_user.get_wallet(owner)}`
        
Balance : *{asyncio.run(ton_bal(mnemonics))} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🏦 Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('🏦 Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('🔎 Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('🔃 Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('🔙 Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
    elif call.data == 'position':
        msg = "Open Positions\n\n"
        pos = asyncio.run(position.main(wallet))
        for i in pos:
            msg += f"[${i['jetton']['name']}](https://t.me/{bot_info.username}?start=track-{position.str_addr(i['jetton']['address'])}) *$ 0.0 Ton *\n"
        markup = types.InlineKeyboardMarkup()
        btn= types.InlineKeyboardButton('❌️ Close', callback_data="cancel")
        markup.add(btn)
        bot.send_message(owner, msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == "reff":
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('❌️ Close', callback_data='cancel')
        markup.add(btn)
        msg = f"""*Referral Program*
        
Join our Referral program and earn 20% From your referrers trading fees.
        
How It Works:

Join our platform and get your unique referral link. 

`https://t.me/{bot_info.username}?start={owner}`

Invite others to trade with us by sharing your referral link via social media, email, or word of mouth.

Once your referrals start trading, you'll receive 20% of their trading fees, directly credited to your wallet.

*Referral Stats*

*Referrals*: {db_userd.get_referrals(owner)}

*Rewards*: {round(db_userd.get_referrals_vol(owner), 2)}
"""

        bot.send_message(owner, msg, 'Markdown',reply_markup=markup)
        
        
    elif call.data == 'cancel':
        bot.delete_message(owner, call.message.message_id)
        
    elif call.data == 'buy1':
        bal = asyncio.run(ton_bal(mnemonics))
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 1:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(1, owner)
            
            x = bot.send_message(owner, f"Attempting a buy at ${abbreviate(get_mc(token))} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                ref_fee = ref_fees(amount)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {abbreviate(get_mc(token))}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 1
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})
   
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
                btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
                btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
                btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
                btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
                markup.add(btn1,btn12,btn13)
                markup.add(btn11, row_width=1)
                markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview= True,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "⚠️ Swap Failed")
        else:
            bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == 'buy5':
        bal = asyncio.run(ton_bal(mnemonics))
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 5:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(5, owner)
            x = bot.send_message(owner, f"Attempting a buy at ${abbreviate(get_mc(token))} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                ref_fee = ref_fees(amount)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {abbreviate(get_mc(token))}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 5
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})  
 
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
                btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
                btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
                btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
                btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
                markup.add(btn1,btn12,btn13)
                markup.add(btn11, row_width=1)
                markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)                
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview= True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "⚠️ Swap Failed")
        else:
            bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == "buy10":
        bal = asyncio.run(ton_bal(mnemonics))
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 10:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(10, owner)
            x = bot.send_message(owner, f"Attempting a buy at ${abbreviate(get_mc(token))} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                ref_fee = ref_fees(amount)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {abbreviate(get_mc(token))}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 10
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})   
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
                btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
                btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
                btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
                btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
                markup.add(btn1,btn12,btn13)
                markup.add(btn11, row_width=1)
                markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "⚠️ Swap Failed")
        else:
            bot.send_message(owner, "⚠️ Not Enough Balance.")
            
    
    
    elif call.data == "buy15":
        bal = asyncio.run(ton_bal(mnemonics))
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 15:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(15, owner)
            
            x = bot.send_message(owner, f"Attempting a buy at ${abbreviate(get_mc(token))} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                ref_fee = ref_fees(amount)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {abbreviate(get_mc(token))}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 15
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})  
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
                btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
                btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
                btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
                btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
                markup.add(btn1,btn12,btn13)
                markup.add(btn11, row_width=1)
                markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id,disable_web_page_preview= True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "⚠️ Swap Failed")
        else:
            bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == "buy20":
        bal = asyncio.run(ton_bal(mnemonics))
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 20:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(20, owner)
            
            x = bot.send_message(owner, f"Attempting a buy at ${abbreviate(get_mc(token))} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                ref_fee = ref_fees(amount)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {abbreviate(get_mc(token))}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 20
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})   
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
                btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
                btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
                btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
                btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
                markup.add(btn1,btn12,btn13)
                markup.add(btn11, row_width=1)
                markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "⚠️ Swap Failed")
        else:
            bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == "buyx":
        send = bot.send_message(owner, "Enter buy amount")
        bot.register_next_step_handler(send, buy_x)
        
    
    elif call.data == "refresh_view":
        x = get_url(token)
        chart = x['pairs'][0]['url']
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn1 = types.InlineKeyboardButton("🔃 Refresh", callback_data='refresh_view1')
        btn2 = types.InlineKeyboardButton("📊 Chart", url=f"{chart}")
        btn3 = types.InlineKeyboardButton('🔎 Scan', url=f"https://t.me/TonChainScannerBot?start={token}")
        btn4 = types.InlineKeyboardButton('💰Buy 1 Ton', callback_data='buy1')
        btn5 = types.InlineKeyboardButton('💰 Buy 5 Ton', callback_data='buy5')
        btn6 = types.InlineKeyboardButton('💰 Buy 10 Ton', callback_data='buy10')
        btn7 = types.InlineKeyboardButton('💰 Buy 15 Ton', callback_data='buy15', )
        btn8 = types.InlineKeyboardButton('💰 Buy 20 Ton', callback_data='buy20')
        btn9 = types.InlineKeyboardButton('💰 Buy X Ton', callback_data='buyx')
        btn10 = types.InlineKeyboardButton('❌️ cancel', callback_data='cancel')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        
        markup.add(btn2,btn1,btn3)
        markup.add(btn11)
        markup.add(btn4,btn5,btn6,btn7,btn8,btn9,btn10)
        
        
        msg = f""" 
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
 
Ton: {asyncio.run(ton_bal(mnemonics))}
 
💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *M Cap*: ${abbreviate(get_mc(token))} |💵 ${get_price(token)} 
 
♻️ *Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 
 
        """
       
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text= msg, parse_mode = 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
        db_trades.add(owner, name, token)
    
    elif call.data == "refresh_view1":
        print('rvf1')
        x = get_url(token)
        chart = x['pairs'][0]['url']
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn1 = types.InlineKeyboardButton("🔃 Refresh", callback_data='refresh_view')
        btn2 = types.InlineKeyboardButton("📊 Chart", url=f"{chart}")
        btn3 = types.InlineKeyboardButton('🔎 Scan', url=f"https://t.me/TonChainScannerBot?start={token}")
        btn4 = types.InlineKeyboardButton('💰Buy 1 Ton', callback_data='buy1')
        btn5 = types.InlineKeyboardButton('💰 Buy 5 Ton', callback_data='buy5')
        btn6 = types.InlineKeyboardButton('💰 Buy 10 Ton', callback_data='buy10')
        btn7 = types.InlineKeyboardButton('💰 Buy 15 Ton', callback_data='buy15', )
        btn8 = types.InlineKeyboardButton('💰 Buy 20 Ton', callback_data='buy20')
        btn9 = types.InlineKeyboardButton('💰 Buy X Ton', callback_data='buyx')
        btn10 = types.InlineKeyboardButton('❌️ Cancel', callback_data='cancel')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        
        markup.add(btn2,btn1,btn3)
        markup.add(btn11)
        markup.add(btn4,btn5,btn6,btn7,btn8,btn9,btn10)

        msg = f""" 
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
 
Ton: {asyncio.run(ton_bal(mnemonics))}
 
💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *M Cap*: ${abbreviate(get_mc(token))} |💵 ${get_price(token)} 
 
♻️ *Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 
 
        """
       
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text= msg, parse_mode = 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
        db_trades.add(owner, name, token)
        
        
    elif call.data == "sellrefresh":
        token_bal = asyncio.run(jetton_bal(token, wallet))
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})  
                """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
        btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
        btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh1')
        btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
        markup.add(btn1,btn12,btn13)
        markup.add(btn11, row_width=1)
        markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
    
    elif call.data == "sellrefresh1":
        print("sell11111111111111111111111111")
        token_bal = asyncio.run(jetton_bal(token, wallet))
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})
                """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
        btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
        btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
        btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
        markup.add(btn1,btn12,btn13)
        markup.add(btn11, row_width=1)
        markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
    
     
    elif call.data == 'sell25':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 0.25
        sell(call.message, token, amount)
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

 📊 [Dexscreener]({chart})
                """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
        btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
        btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
        btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
        markup.add(btn1,btn12,btn13)
        markup.add(btn11, row_width=1)
        markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    
    elif call.data == 'sell50':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 0.5
        sell(call.message, token, amount)
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart}) 
                """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
        btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
        btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
        btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
        markup.add(btn1,btn12,btn13)
        markup.add(btn11, row_width=1)
        markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)

        
    elif call.data == 'sell75':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 0.75
        sell(call.message, token, amount)
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

 📊 [Dexscreener]({chart})   
                """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
        btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
        btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
        btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
        btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
        markup.add(btn1,btn12,btn13)
        markup.add(btn11, row_width=1)
        markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == 'sell100':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 1
        sell(call.message, token, amount)
        time.sleep(10)
        bot.delete_message(owner, call.message.message_id)
        
    elif call.data == 'sellx':
        send = bot.send_message(owner, "send Number of tokens you want to sell: ")
        bot.register_next_step_handler(send, sellix)
        
        
    elif call.data == 'set_slip':
        send = bot.send_message(owner, "Enter slippage:")
        bot.register_next_step_handler(send,setslip)
        
    
    elif call.data == "buysx":
        s = bot.send_message(owner, "Enter buy amount: ")
        bot.register_next_step_handler(s, buy_sx)
    
    elif call.data == "buys5":
        sbuy(call.message, token, 5)
        
        
    elif call.data == 'buys10':
        sbuy(call.message, token, 10)
        
            
    elif call.data == 'bridge':
        bot.delete_message(owner, call.message.message_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton('Ton to others', callback_data='tonbridge')
        btn2 = types.InlineKeyboardButton('ETH --> TON', callback_data='ethton')
        btn3 = types.InlineKeyboardButton('SOL --> TON', callback_data='solton')
        btn4 = types.InlineKeyboardButton('BASE --> TON', callback_data='baseton')
        btn5 = types.InlineKeyboardButton('BTC --> TON', callback_data='btcton')
        btn6 = types.InlineKeyboardButton('BNB --> TON', callback_data='bnbton')
        btn7 = types.InlineKeyboardButton('USDT(ERC20) --> TON', callback_data='ercton')
        btn8 = types.InlineKeyboardButton('USDT(TRC20) --> TON', callback_data='trcton')
        btn9 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        
        msg = """
        Bridge from one network to Ton using the built in Bridge Mode
        
Select the chain you're bridging from and follow the prompt after

Tap on *Ton to others* To bridge from Ton to other chains         

        """
        
        markup.add(btn1, btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9)
        
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
    elif call.data == 'ethton':
        min = minimum('eth','eth','ton','ton')
        msg = f"You're Swaping from ETH to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, etht1)
        
        
    elif call.data == "confirm":
        amt = db_bridge.get_amount(owner)
        exc = exchange('eth','eth','ton','ton',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging From Eth to Ton
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)  
        
        
    elif call.data == 'solton':
        min = minimum('sol','sol','ton','ton')
        msg = f"You're Swaping from SOL to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, sol1)
        
        
    elif call.data == "confirm1":
        amt = db_bridge.get_amount(owner)
        exc = exchange('sol','sol','ton','ton',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging From Sol to Ton
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'baseton':
        min = minimum('eth','base','ton','ton')
        msg = f"You're Swaping from BASE to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, base1)
        
        
    elif call.data == "confirm2":
        amt = db_bridge.get_amount(owner)
        exc = exchange('eth','base','ton','ton',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging From Base to Ton
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'btcton':
        min = minimum('btc','btc','ton','ton')
        msg = f"You're Swaping from BTC to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, btc1)
        
        
    elif call.data == "confirm3":
        amt = db_bridge.get_amount(owner)
        exc = exchange('btc','btc','ton','ton',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging From BTC to Ton
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'bnbton':
        min = minimum('bnb','bsc','ton','ton')
        msg = f"You're Swaping from BNB to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, bnb1)
        
        
    elif call.data == "confirm4":
        amt = db_bridge.get_amount(owner)
        exc = exchange('bnb','bsc','ton','ton',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging From BNB to Ton
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'ercton':
        min = minimum('usdt','eth','ton','ton')
        msg = f"You're Swaping from USDT(ERC20) to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, erc1)
        
        
    elif call.data == "confirm5":
        amt = db_bridge.get_amount(owner)
        exc = exchange('usdt','eth','ton','ton',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging From USDT to Ton
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'trcton':
        min = minimum('usdt','trx','ton','ton')
        msg = f"You're Swaping from USDT(TRC20) to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, trc1)
        
        
    elif call.data == "confirm6":
        amt = db_bridge.get_amount(owner)
        exc = exchange('usdt','trx','ton','ton',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging From USDT(TRC20) to Ton
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)     
        
        
    elif call.data == 'tonbridge':
        bot.delete_message(owner, call.message.message_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton('Bridge to Ton', callback_data='bridge')
        btn2 = types.InlineKeyboardButton('TON --> ETH', callback_data='toneth')
        btn3 = types.InlineKeyboardButton('TON --> SOL', callback_data='tonsol')
        btn4 = types.InlineKeyboardButton('TON --> BASE', callback_data='tonbase')
        btn5 = types.InlineKeyboardButton('TON --> BTC', callback_data='tonbtc')
        btn6 = types.InlineKeyboardButton('TON --> BNB', callback_data='tonbnb')
        btn7 = types.InlineKeyboardButton('TON --> USDT(ERC20)', callback_data='tonerc')
        btn8 = types.InlineKeyboardButton('TON --> USDT(TRC20)', callback_data='tontrc')
        btn9 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        
        msg = """
        Bridge from one network to Ton using the built in Bridge Mode
        
Select the chain you're bridging from and follow the prompt after

Tap on *Bridge to Ton* To bridge from Ton to other chains         

        """
        
        markup.add(btn1, btn2,btn3,btn5,btn7,btn8,btn9)
        
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
    elif call.data == 'toneth':
        min = minimum('ton', 'ton', 'eth', 'eth')
        msg = f"Minimum bridge amount for TON to ETH is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, toneth)
    elif call.data == 'tonsol':
        min = minimum('ton', 'ton', 'sol', 'sol')
        msg = f"Minimum bridge amount for TON to SOL is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, solton)
    elif call.data == 'tonerc':
        min = minimum('ton', 'ton', 'eth', 'usdt')
        msg = f"Minimum bridge amount for TON to USDT(ERC20) is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, tonerc)
    elif call.data == 'tonbtc':
        min = minimum('ton', 'ton', 'btc', 'btc')
        msg = f"Minimum bridge amount for TON to BTC is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, tonbtc)
    elif call.data == 'tontrc':
        min = minimum('ton', 'ton', 'trx', 'usdt')
        msg = f"Minimum bridge amount for TON to USDT(TRC20) is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = bot.send_message(owner, msg)
        bot.register_next_step_handler(s, tontrc)
        
        
    elif call.data == 'tonethc':
        bot.delete_message(owner, call.message.message_id)
        amt = db_bridge.get_amount(owner)
        wallet = db_bridge.get_txid(owner)
        exc = exchange('ton','ton', 'eth', 'eth',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging from Ton to Eth
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
        
    elif call.data == 'tonbtcc':
        bot.delete_message(owner, call.message.message_id)
        amt = db_bridge.get_amount(owner)
        wallet = db_bridge.get_txid(owner)
        exc = exchange('ton','ton', 'btc', 'btc',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging from Ton to BTC
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'tonsolc':
        bot.delete_message(owner, call.message.message_id)
        amt = db_bridge.get_amount(owner)
        wallet = db_bridge.get_txid(owner)
        exc = exchange('ton','ton', 'sol', 'sol',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging from Ton to Sol
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'tonercc':
        bot.delete_message(owner, call.message.message_id)
        amt = db_bridge.get_amount(owner)
        wallet = db_bridge.get_txid(owner)
        exc = exchange('ton','ton', 'eth', 'usdt',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging from Ton to USDT(ERC20)
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
    
    elif call.data == 'tontrcc':
        bot.delete_message(owner, call.message.message_id)
        amt = db_bridge.get_amount(owner)
        wallet = db_bridge.get_txid(owner)
        exc = exchange('ton','ton', 'trx', 'usdt',amt,wallet)
        payin = exc['payinAddress']
        toamt = exc['toAmount']
        msg = f"""Bridging from Ton to USDT(TRC20)
        
Pay-in Address: `{payin}`

Pay-out Wallet: `{wallet}`

Amount-In: *{amt}*

Amount-Out: *{toamt}*

Send the amount and bridge will be completed automatically
        """
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
    
    
def toneth(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'eth', 'eth')
        if amt < min:
            bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            bot.register_next_step_handler(message, toneth)
        else:
            db_bridge.update_amount(amt, owner)
            s = bot.send_message(owner, "send Wallet to bridge to: ")
            bot.register_next_step_handler(s, toneth1y)
    except Exception as e:
        bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        bot.register_next_step_handler(message, toneth)  
        
        
def toneth1y(message):
    print(message.text)
    try:
        owner = message.chat.id
        wallet = message.text
        db_bridge.update_txid(wallet, owner) 
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        btn2 = types.InlineKeyboardButton('Confirm', callback_data='tonethc')
        markup.add(btn1,btn2)
        amt = db_bridge.get_amount(owner)
        y = output('ton','ton','eth','eth', amt)
        print(y)
        msg = f"""You're about to bridge *{amt} Ton* to *{y} Eth*
        
Hit the Confirm button to confirm swap
        
        """
        
        bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(e)
        
        
        
def solton(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'sol', 'sol')
        if amt < min:
            bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            bot.register_next_step_handler(message, solton)
        else:
            db_bridge.update_amount(amt, owner)
            s = bot.send_message(owner, "send Wallet to bridge to: ")
            bot.register_next_step_handler(s, tonsol1y)
    except Exception as e:
        bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        bot.register_next_step_handler(message, solton)  
        
        
def tonsol1y(message):
    print(message.text)
    try:
        owner = message.chat.id
        wallet = message.text
        db_bridge.update_txid(wallet, owner) 
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        btn2 = types.InlineKeyboardButton('Confirm', callback_data='tonsolc')
        markup.add(btn1,btn2)
        amt = db_bridge.get_amount(owner)
        y = output('ton','ton','sol','sol', amt)
        print(y)
        msg = f"""You're about to bridge *{amt} Ton* to *{y} Sol*
        
Hit the Confirm button to confirm swap
        
        """
        
        bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(e)
        
        
        
def tonbtc(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'btc', 'btc')
        if amt < min:
            bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            bot.register_next_step_handler(message, tonbtc)
        else:
            db_bridge.update_amount(amt, owner)
            s = bot.send_message(owner, "send Wallet to bridge to: ")
            bot.register_next_step_handler(s, tonbtc1y)
    except Exception as e:
        bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        bot.register_next_step_handler(message, tonbtc)  
        
        
def tonbtc1y(message):
    print(message.text)
    try:
        owner = message.chat.id
        wallet = message.text
        db_bridge.update_txid(wallet, owner) 
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        btn2 = types.InlineKeyboardButton('Confirm', callback_data='tonbtcc')
        markup.add(btn1,btn2)
        amt = db_bridge.get_amount(owner)
        y = output('ton','ton','btc','btc', amt)
        print(y)
        msg = f"""You're about to bridge *{amt} Ton* to *{y} BTC*
        
Hit the Confirm button to confirm swap
        
        """
        
        bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(e)
        
        
        
def tonerc(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'eth', 'usdt')
        if amt < min:
            bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            bot.register_next_step_handler(message, tonerc)
        else:
            db_bridge.update_amount(amt, owner)
            s = bot.send_message(owner, "send Wallet to bridge to: ")
            bot.register_next_step_handler(s, tonerc1y)
    except Exception as e:
        bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        bot.register_next_step_handler(message, tonerc)  
        
        
def tonerc1y(message):
    print(message.text)
    try:
        owner = message.chat.id
        wallet = message.text
        db_bridge.update_txid(wallet, owner) 
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        btn2 = types.InlineKeyboardButton('Confirm', callback_data='tonercc')
        markup.add(btn1,btn2)
        amt = db_bridge.get_amount(owner)
        y = output('ton','ton','eth','usdt', amt)
        print(y)
        msg = f"""You're about to bridge *{amt} Ton* to *{y} USDT(ERC20)*
        
Hit the Confirm button to confirm swap
        
        """
        
        bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(e)
        
        
def tontrc(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'trx', 'usdt')
        if amt < min:
            bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            bot.register_next_step_handler(message, tontrc)
        else:
            db_bridge.update_amount(amt, owner)
            s = bot.send_message(owner, "send Wallet to bridge to: ")
            bot.register_next_step_handler(s, tontrc1y)
    except Exception as e:
        bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        bot.register_next_step_handler(message, tontrc)  
        
        
def tontrc1y(message):
    print(message.text)
    try:
        owner = message.chat.id
        wallet = message.text
        db_bridge.update_txid(wallet, owner) 
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        btn2 = types.InlineKeyboardButton('Confirm', callback_data='tontrcc')
        markup.add(btn1,btn2)
        amt = db_bridge.get_amount(owner)
        y = output('ton','ton','trx','usdt', amt)
        print(y)
        msg = f"""You're about to bridge *{amt} Ton* to *{y} USDT(TRC20)*
        
Hit the Confirm button to confirm swap
        
        """
        
        bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(e)
        
        
def buy_sx(message):
    owner = message.chat.id
    token = db_trades.get_last_ca(owner)
    try:
        amount = float(message.text)
        
        sbuy(message, token, amount)
    except Exception as e:
        bot.send_message(owner, "⚠️ Invalid amount!")

def etht1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('eth','eth','ton','ton')
    if initial < min:
        s = bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        bot.register_next_step_handler(s, etht1)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm')
        out = output('eth','eth','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} ETH* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
def sol1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('sol','sol','ton','ton')
    if initial < min:
        s = bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        bot.register_next_step_handler(s, sol1)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm1')
        out = output('sol','sol','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} SOL* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
def base1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('eth','base','ton','ton')
    if initial < min:
        s = bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        bot.register_next_step_handler(s, base1)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm2')
        out = output('eth','base','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} Base* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
def btc1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('btc','btc','ton','ton')
    if initial < min:
        s = bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        bot.register_next_step_handler(s, btc1)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm3')
        out = output('btc','btc','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} BTC* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
def bnb1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('bnb','bsc','ton','ton')
    if initial < min:
        s = bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        bot.register_next_step_handler(s, bnb1)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm4')
        out = output('bnb','bsc','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} BNB* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
def erc1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('usdt','eth','ton','ton')
    if initial < min:
        s = bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        bot.register_next_step_handler(s, erc1)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm5')
        out = output('usdt','eth','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} USDT(ERC20)* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
def trc1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('usdt','trx','ton','ton')
    if initial < min:
        s = bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        bot.register_next_step_handler(s, trc1)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm6')
        out = output('usdt','trx','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} USDT(TRC20)* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)


def sellix(message):
    owner = message.chat.id
    try:
        initial = float(message.text)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Message should be a number ")
    owner = message.chat.id
    token = db_trades.get_last_ca(owner)
    wallet = db_user.get_wallet(owner)
    bal = asyncio.run(jetton_bal(token,wallet))
    #print(call.data)
    if bal > initial:
        sell(message, token, initial)
        time.sleep(25)
        
        
def buy_x(message):
    try:
        initial = float(message.text)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
    owner = message.chat.id
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    token = db_trades.get_last_ca(owner)
    print(token)
    pool = get_pool(token)
    print(pool)
    name = get_name(token)
    symbol = get_symbol(token)
    wallet = db_user.get_wallet(owner)
    pair = get_pair(token)
    lp = get_lp(token)
    bal = asyncio.run(ton_bal(mnemonics))
    #print(call.data)
    slip = db_user.get_slippage(owner)
    if bal > initial:
        asyncio.run(deploy(mnemonics))
        amount = bot_fees(initial, owner)
        
        x = bot.send_message(owner, f"Attempting a buy at ${abbreviate(get_mc(token))} MCap")
        buy = asyncio.run(jetton_swap(token, mnemonics, amount))
        time.sleep(25)
        if buy == 1:
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amount)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            bot.delete_message(owner, x.message_id)
            bot.send_message(owner, f"Bought {get_name(token)} at ${abbreviate(get_mc(token))}")
            buy_mc = get_mc(token)
            pnl = (get_mc(token)-buy_mc)/buy_mc*100
            amt = initial
            db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
            x = get_url(token)
            chart = x['pairs'][0]['url']
            msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {asyncio.run(jetton_bal(token, wallet))} 
Ton: {asyncio.run(ton_bal(mnemonics))} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=track-{token}) | 💎 {round((get_mc(token)/buy_mc)*initial, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 

📊 [Dexscreener]({chart})  
                """
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Buy 5 Ton ", callback_data='buys5')
            btn12 = types.InlineKeyboardButton("Buy 10 Ton ", callback_data='buys10')
            btn13 = types.InlineKeyboardButton("Buy X ✏", callback_data='buysx')
            btn11 = types.InlineKeyboardButton(f'✏ Slippage % ({slip * 100})', callback_data="set_slip")
            btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
            btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
            btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
            btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
            btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
            btn7 = types.InlineKeyboardButton("🔃 Refresh", callback_data='sellrefresh')
            btn14 = types.InlineKeyboardButton('📌 Track', callback_data='track')
            markup.add(btn1,btn12,btn13)
            markup.add(btn11, row_width=1)
            markup.add(btn2,btn3,btn4,btn5,btn6,btn14,btn7)
            bot.send_message(message.chat.id, msg, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)
                
        else:
                bot.send_message(owner, "Swap Failed")
    else:
        bot.send_message(owner, "Not Enough Balance.")

def setslip(message):
    owner = message.chat.id
    try:
        new_sli = float(message.text)
        new_slip = new_sli / 100
    except Exception as e:
        bot.send_message(owner, "Invalid Number")
        
    db_user.update_slippage(new_slip, owner)
    bot.send_message(owner, "Slippage updated")

def air(message):
    jetton = message.text
    owner = message.chat.id
    send = bot.send_message(message.chat.id,"Send Wallet and amount list seperated by comma: ")
    bot.register_next_step_handler(send, drop)
    db_airdrop.add_user(owner, jetton)
    #bot.delete_message(message.chat.id, message.message_id)
    
    
def drop(message):
    try:
        owner = message.chat.id
        x = message.text
        jetton = db_airdrop.get_address(owner)
        lines = x.strip().split('\n')
        db_airdrop.delete_user(owner)
        destinations = {}
        
        for line in lines:
            key, value = line.split(',')
            destinations[key.strip()] = int(value.strip())
    except Exception as e:
        bot.send_message(owner, "An error occurred\n Check your wallet list and try again")
        
    try:
        mn = db_user.get_mnemonics(owner)
        mnemonics = eval(decrypt(mn))
        address = db_airdrop.get_address(owner)
        asyncio.run(airdrop.main(mnemonics, address, destinations))
        bot.send_message(owner, "Done")
        db_airdrop.delete_user(owner)
    except Exception as e:
        bot.send_message(owner, "Failed To Send Tokens")
        print(e)
    
    
    
bot.infinity_polling()