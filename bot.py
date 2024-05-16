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
from database.db import User, Trade

from fees import bot_fees
import telebot
from telebot import types
from telebot.util import antiflood
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

db_user.setup()
db_trade.setup()

TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)


def sell(message, addr, amount):
    owner = message.chat.id
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    wallet = db_user.get_wallet(owner)
    j_bal = asyncio.run(jetton_bal(addr, wallet))
    t_bal = asyncio.run(ton_bal(mnemonics))
    if j_bal >= amount and t_bal > 0.5:
        x  = bot.send_message(owner, f"Attempting a buy at ${get_mc(addr)} MCap")
        dec = asyncio.run(update(addr)['decimals'])
        decimal = 10**dec
        j_price = asyncio.run(main_price(amount, addr, decimal))
        sell = asyncio.run(ton_swap(addr,mnemonics,amount))
        time.sleep(30)
        bot_fees(j_price, owner)
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
    btn5 = types.InlineKeyboardButton("Support Community", url="https://t.me/zerohexdave")
    btn6 = types.InlineKeyboardButton("Bot Manual", url="https://t.me/zerohexdave")
    #btn6 = types.InlineKeyboardButton("Close ", callback_data="cancel")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    new_nmemonics = encrypt(mnemonics)
    
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
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                db_trade.update_trade(owner, token, buy_mc)
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
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                db_trade.update_trade(owner, token, buy_mc)
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
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                db_trade.update_trade(owner, token, buy_mc)
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
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                db_trade.update_trade(owner, token, buy_mc)
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
            x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
            buy = asyncio.run(jetton_swap(token, mnemonics, amount))
            time.sleep(25)
            if buy == 1:
                bot.delete_message(owner, x.message_id)
                bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                db_trade.update_trade(owner, token, buy_mc)
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
        x = bot.send_message(owner, f"Attempting a buy at ${get_mc(token)} MCap")
        buy = asyncio.run(jetton_swap(token, mnemonics, amount))
        time.sleep(25)
        if buy == 1:
            bot.delete_message(owner, x.message_id)
            bot.send_message(owner, f"Bought {get_name(token)} at {get_mc(token)}")
            buy_mc = get_mc(token)
            pnl = (get_mc(token)-buy_mc)/buy_mc*100
            db_trade.update_trade(owner, token, buy_mc)
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