#native imports
from native.encrypt import encrypt, decrypt
from native.genwallet import gen_mnemonics, import_wallet,  get_addr
from native.jet_upd import update
from native.deploy import deploy
from native.transfer_jet import transfer_jet
from native.transfer_ton import send_ton
from native.wallet_bal import jetton_bal, ton_bal


#swap import
from swap.jetton_ton import ton_swap
from swap.ton_jetton import jetton_swap
from swap.prices import main_price
from swap.info import get_symbol, get_decimal, get_mc, get_name, get_pool, get_price, get_url, get_lp, get_pair

#db import 
from database.db import User, Trade, UserData, Bridge

from bridge.bridge import exchange, minimum, exchange_status, output

from fees import bot_fees, ref_fees
import telebot
from telebot import types
from telebot.util import antiflood, extract_arguments
import time
import json
import asyncio
from dotenv import load_dotenv
import os
"""
Initialising database
"""
db_user = User()
db_trade = Trade()
db_userd = UserData()
db_bridge = Bridge()

db_user.setup()
db_trade.setup()
db_userd.setup()


TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)


def sell(message, addr, amount):
    owner = message.chat.id
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    wallet = db_user.get_wallet(owner)
    j_bal = asyncio.run(jetton_bal(addr, wallet))
    t_bal = asyncio.run(ton_bal(mnemonics))
    if j_bal >= amount and t_bal > 0.5:
        x  = bot.send_message(owner, f"Attempting a sell at ${get_mc(addr):,} MCap")
        dec1 = asyncio.run(update(addr))
        dec = dec1['decimals']
        decimal = 10**dec
        j_price = asyncio.run(main_price(amount, addr, decimal))
        sell = asyncio.run(ton_swap(addr,mnemonics,amount))
        time.sleep(30)
        amt = bot_fees(j_price, owner)
        ref = db_userd.get_referrer(owner)
        ref_fee = ref_fees(amt)
        get_ref_vol = db_userd.get_referrals_vol(ref)
        add_ref_vol = get_ref_vol + ref_fee
        db_userd.update_referrals_vol(add_ref_vol, ref)
        get_trad = db_userd.get_trading_vol(owner)
        add_trad = amt + get_trad
        db_userd.update_trading_vol(add_trad, owner)
        if sell == 1:
            bot.send_message(owner, f"Successfully sold {amount} tokens")
        else:
            bot.send_message(owner, "Failed to swap tokens")
            
    else:
        bot.send_message(owner, "Swap failed make sure there's enough Ton for gas or token amount is enough")



#Dev commands 

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        send = bot.send_message(message.chat.id,"Enter message to broadcast")
        bot.register_next_step_handler(send,sendall)
        
    else:
        bot.reply_to(message, "You're not allowed to use this command")
        
        

db_userd.add_user(username_= 7034272819, wallet="UQDLzebYWhJaIt5YbZ5vz_glIbfqP7PxNg9V54HW3jSIhDPe", referrer=7034272819)
      
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
    welcom = f"""Welcome to Maximus Trade Bot!
The fastest Ton trading bot.

wallet address : `{wallet_address}` has been generated for you.

Use the wallet button below to view your 24 words key phrase.

Paste a jetton contract address to trade....
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton(f"{wallet_address}", callback_data="wal")
    btn2 = types.InlineKeyboardButton(f"{asyncio.run(ton_bal(mnemonics))} Ton", callback_data='us')
    btn3 = types.InlineKeyboardButton("Wallet", callback_data='wallett')
    btn4 = types.InlineKeyboardButton("Positions", callback_data="position")
    btn7 = types.InlineKeyboardButton("Bridge", callback_data='bridge')
    btn5 = types.InlineKeyboardButton("Support Community", url="https://t.me/zerohexdave")
    btn6 = types.InlineKeyboardButton("Bot Manual", url="https://t.me/zerohexdave")
    #btn6 = types.InlineKeyboardButton("Close ", callback_data="cancel")
    
    markup.add(btn1, btn2, btn3, btn4,btn7, btn5, btn6)
    new_nmemonics = encrypt(mnemonics)
    referrer = extract_arguments(message.text)
    if extract_arguments(message.text):
        if referrer == owner:
            bot.send_message(owner, "You can't be your own referrer")
            db_userd.add_user(owner, wallet_address, 7034272819)
        else:
            if db_userd.get_referrer(referrer) == None:
                bot.send_message(owner, "Referrer not in database")
                db_userd.add_user(owner, wallet_address, 7034272819)
            else:
                db_userd.add_user(owner, wallet_address, referrer=referrer)
                ref = db_userd.get_referrals(referrer)
                reff = ref + 1
                db_userd.update_referrals(reff, referrer)
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
    new = decrypt(mnemonics)
    msg = f"""
    Wallet Address: `{wallet}`
    
Pass Phrase: `{new}`

*Please delete this message after copying your pass phrase!!!*
    """
    bot.send_message(owner, msg, 'Markdown')
    
    
@bot.message_handler(commands=['support'])
def support(message):
    bot.reply_to(message, "For help or support join the official support community @zerohexdave")
    
    
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
            asyncio.run(send_ton(dest=wallet, amount=amount,mnemonics=mnemonics))
            time.sleep(15)
            msg = f"""Sent {amount} Ton to {wallet} with [Tx Hash]("https://tonscan.org/address/{wallet}#transactions")"""
            bot.send_message(message.chat.id, msg, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "Amount higher than Wallet Balance")
            
    except Exception as e:
        bot.send_message(message.chat.id, "Transaction could not be prossesed")
        
    
    

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
        
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn1 = types.InlineKeyboardButton("Refresh", callback_data='refresh_view')
        btn2 = types.InlineKeyboardButton("Chart", url=f"{chart}")
        btn3 = types.InlineKeyboardButton('Scan', url="https://t.me/zerohexdave")
        btn4 = types.InlineKeyboardButton('Buy 1 Ton', callback_data='buy1')
        btn5 = types.InlineKeyboardButton('Buy 5 Ton', callback_data='buy5')
        btn6 = types.InlineKeyboardButton('Buy 10 Ton', callback_data='buy10')
        btn7 = types.InlineKeyboardButton('Buy 15 Ton', callback_data='buy15', )
        btn8 = types.InlineKeyboardButton('Buy 20 Ton', callback_data='buy20')
        btn9 = types.InlineKeyboardButton('Buy X Ton', callback_data='buyx')
        btn10 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        
        markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9,btn10)
        
        
        msg = f"""
💎 {name} ({symbol}): 🌐 {pool}

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 *Liquidity*: {lp} TON

*Balance*: 

Ton: {asyncio.run(ton_bal(mnemonics))}


        """
       
        bot.send_message(message.chat.id, msg, 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
        db_trade.add_trade(owner, token)
        
    except Exception as e:
        bot.send_message(message.chat.id, "Please make sure you paste a valid contract :) ")
        print(e)



@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    owner = call.message.chat.id
    token = 'EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE' if db_trade.retrieve_last_ca(owner) == None else db_trade.retrieve_last_ca(owner)
    name = get_name(token)
    symbol = get_symbol(token)
    lp = get_lp(token)
    pair = get_pair(token)
    pool = get_pool(token)
    wallet = db_user.get_wallet(owner)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    
    if call.data == 'wallett':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss: `{db_user.get_wallet(owner)}`
        
Balance: *{asyncio.run(ton_bal(mnemonics))} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
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
        
    elif call.data == 'wrefresh':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss : `{db_user.get_wallet(owner)}`
        
Balance : *{asyncio.run(ton_bal(mnemonics))} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('Back', callback_data='home')
        
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
        btn1 = types.InlineKeyboardButton('Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
    elif call.data == 'position':
        bot.send_message(owner, "Work on this")
        
        
    elif call.data == 'cancel':
        bot.delete_message(owner, call.message.message_id)
        
    elif call.data == 'buy1':
        bal = asyncio.run(ton_bal(mnemonics))
        #print(call.data)
        if bal > 1:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(1, owner)
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amount)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 1
                db_trade.update_trade(owner, token, buy_mc, buy_amount=amt)
                msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
💰 *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*1, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
                markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview= True,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "Swap Failed")
        else:
            bot.send_message(owner, "Not Enough Balance.")
            
            
    elif call.data == 'buy5':
        bal = asyncio.run(ton_bal(mnemonics))
        #print(call.data)
        if bal > 5:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(5, owner)
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amount)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 5
                db_trade.update_trade(owner, token, buy_mc, buy_amount=amt)
                msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
💰 *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*5, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
                markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview= True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "Swap Failed")
        else:
            bot.send_message(owner, "Not Enough Balance.")
            
            
    elif call.data == "buy10":
        bal = asyncio.run(ton_bal(mnemonics))
        #print(call.data)
        if bal > 10:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(10, owner)
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amount)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 10
                db_trade.update_trade(owner, token, buy_mc, buy_amount=amt)
                msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
💰 *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*10, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
                markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "Swap Failed")
        else:
            bot.send_message(owner, "Not Enough Balance.")
            
    
    
    elif call.data == "buy15":
        bal = asyncio.run(ton_bal(mnemonics))
        #print(call.data)
        if bal > 15:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(15, owner)
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amount)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 15
                db_trade.update_trade(owner, token, buy_mc, buy_amount=amt)
                msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
💰 *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*15, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
                markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id,disable_web_page_preview= True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "Swap Failed")
        else:
            bot.send_message(owner, "Not Enough Balance.")
            
            
    elif call.data == "buy20":
        bal = asyncio.run(ton_bal(mnemonics))
        #print(call.data)
        if bal > 20:
            asyncio.run(deploy(mnemonics))
            amount = bot_fees(20, owner)
            ref = db_userd.get_referrer(owner)
            ref_fee = ref_fees(amount)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 20
                db_trade.update_trade(owner, token, buy_mc, buy_amount=amt)
                msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
💰 *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*20, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
                """
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
                btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
                btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
                btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
                btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
                btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
                btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
                markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
                bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                bot.send_message(owner, "Swap Failed")
        else:
            bot.send_message(owner, "Not Enough Balance.")
            
            
    elif call.data == "buyx":
        send = bot.send_message(owner, "Enter buy amount")
        bot.register_next_step_handler(send, buy_x)
        
    
    elif call.data == "refresh_view":
        x = get_url(token)
        chart = x['pairs'][0]['url']
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn1 = types.InlineKeyboardButton("Refresh", callback_data='refresh_view')
        btn2 = types.InlineKeyboardButton("Chart", url=f"{chart}")
        btn3 = types.InlineKeyboardButton('Scan', url="https://t.me/zerohexdave")
        btn4 = types.InlineKeyboardButton('Buy 1 Ton', callback_data='buy1')
        btn5 = types.InlineKeyboardButton('Buy 5 Ton', callback_data='buy5')
        btn6 = types.InlineKeyboardButton('Buy 10 Ton', callback_data='buy10')
        btn7 = types.InlineKeyboardButton('Buy 15 Ton', callback_data='buy15', )
        btn8 = types.InlineKeyboardButton('Buy 20 Ton', callback_data='buy20')
        btn9 = types.InlineKeyboardButton('Buy X Ton', callback_data='buyx')
        btn10 = types.InlineKeyboardButton('Cancel', callback_data='cancel')
        
        markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9,btn10)
        
        
        msg = f"""
💎 {name} ({symbol}): 🌐 {pool}

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *M Cap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 *Liquidity*: {lp} TON

*Balance*: 

Ton: {asyncio.run(ton_bal(mnemonics))}


        """
       
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text= msg, parse_mode = 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
        db_trade.add_trade(owner, token)
        
        
    elif call.data == 'sell25':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 0.25
        sell(call.message, token, amount)
        buy_mc = db_trade.retrieve_last_buycap(owner)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trade.retrieve_buyamt(owner=owner) == None else db_trade.retrieve_buyamt(owner=owner)
        msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
{'🟩' if {round(pnl, 2)} >=0 else '🟥'} *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
        """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
        markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    
    elif call.data == 'sell50':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 0.5
        sell(call.message, token, amount)
        buy_mc = db_trade.retrieve_last_buycap(owner)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trade.retrieve_buyamt(owner=owner) == None else db_trade.retrieve_buyamt(owner=owner)
        msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
{'🟩' if {round(pnl, 2)} >=0 else '🟥'} *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
        """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
        markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)

        
    elif call.data == 'sell75':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 0.75
        sell(call.message, token, amount)
        buy_mc = db_trade.retrieve_last_buycap(owner)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trade.retrieve_buyamt(owner=owner) == None else db_trade.retrieve_buyamt(owner=owner)
        msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
{'🟩' if {round(pnl, 2)} >=0 else '🟥'} *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
        """
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
        btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
        btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
        btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
        btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
        btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
        btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
        markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
        bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == 'sell100':
        token_bal = asyncio.run(jetton_bal(token, wallet))
        
        amount = token_bal * 1
        sell(call.message, token, amount)
        time.sleep(10)
        bot.delete_message(owner, call.message.message_id)
        
        
        
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
        
        markup.add(btn1, btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9)
        
        bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        

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

        
def buy_x(message):
    try:
        initial = float(message.text)
    except Exception as e:
        bot.send_message(message.chat.id, "Message should be a number ")
    owner = message.chat.id
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    token = db_trade.retrieve_last_ca(owner)
    pool = get_pool(token)
    name = get_name(token)
    symbol = get_symbol(token)
    wallet = db_user.get_wallet(owner)
    pair = get_pair(token)
    lp = get_lp(token)
    bal = asyncio.run(ton_bal(mnemonics))
    #print(call.data)
    if bal > initial:
        asyncio.run(deploy(mnemonics))
        amount = bot_fees(initial, owner)
        ref = db_userd.get_referrer(owner)
        ref_fee = ref_fees(amount)
        get_ref_vol = db_userd.get_referrals_vol(ref)
        add_ref_vol = get_ref_vol + ref_fee
        db_userd.update_referrals_vol(add_ref_vol, ref)
        get_trad = db_userd.get_trading_vol(owner)
        add_trad = amount + get_trad
        db_userd.update_trading_vol(add_trad, owner)
        x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
        buy = asyncio.run(jetton_swap(token, mnemonics, amount))
        time.sleep(25)
        if buy == 1:
            bot.delete_message(owner, x.message_id)
            bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
            buy_mc = get_mc(token)
            pnl = (get_mc(token)-buy_mc)/buy_mc*100
            amt = initial
            db_trade.update_trade(owner, token, buy_mc, buy_amount=amt)
            msg = f"""💎 {name} ({symbol}): 🌐 {pool}
                
💰 *profit*: {round(pnl, 2)} | 💎 {round((get_mc(token)/buy_mc)*initial, 2)} Ton

💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token})

💦 *LP*: `{pair}`

📈 *MCap*: {get_mc(token)} *USD* |💵 ${get_price(token)}

💦 * Liquidity*: {lp} TON

*Balance*: 
{name}: {asyncio.run(jetton_bal(token, wallet))}
Ton: {asyncio.run(ton_bal(mnemonics))}
                
                
                """
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Buy ", callback_data='buy')
            btn2 = types.InlineKeyboardButton("Sell 25%", callback_data='sell25')
            btn3 = types.InlineKeyboardButton("Sell 50%", callback_data='sell50')
            btn4 = types.InlineKeyboardButton("Sell 75%", callback_data='sell75')
            btn5 = types.InlineKeyboardButton("Sell 100% ", callback_data='sell100')
            btn6 = types.InlineKeyboardButton("Sell X token ", callback_data='sellx')
            btn7 = types.InlineKeyboardButton("Refresh", callback_data='sellrefresh')
            markup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7)
            bot.send_message(message.chat.id, msg, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)
                
        else:
                bot.send_message(owner, "Swap Failed")
    else:
        bot.send_message(owner, "Not Enough Balance.")

    
bot.infinity_polling()