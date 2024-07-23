#native imports
from native.encrypt import encrypt, decrypt
from native.genwallet import gen_mnemonics, import_wallet,  get_addr
from native.jet_upd import update
from native.deploy import deploy
from native.transfer_jet import transfer_jet
from native.transfer_ton import send_ton
from native.wallet_bal import jetton_bal, ton_bal
from native import position
from native import tx_hash
from native import metadata


#swap import
from swap.jetton_ton import ton_swap
from swap.ton_jetton import jetton_swap
from swap.prices import main_price

from swap.info import (get_symbol, get_decimal, get_mc, 
                       get_name, get_pool, get_price, 
                       get_url, get_lp, get_pair
)
#db import 
from database.db import User, Trade, UserData, Bridge, Airdrop

from database.trades import Trades

from bridge.bridge import exchange, minimum, exchange_status, output

from airdrop import airdrop
import re
from pnl import pnlpic
from fees import bot_fees, ref_fees, sell_fees
import asset_price
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.util import antiflood, extract_arguments
import time
import json
import asyncio
from dotenv import load_dotenv
import os
from telebot import asyncio_filters
from telebot.asyncio_storage import StateMemoryStorage
from tg_states import (BroadcastState, AirdropState, BuyXState, 
                       SellXState, SlippageState, WithdrawState, 
                       BuySXState, TonBridgeEthState,OthersEthBridgeState,
                       TonBridgeSolState, TonBridgeBaseState, TonBridgeBtcState,
                       TonBridgeUsdt1State,TonBridgeUsdt2State, TonBridgeBnbState,
                       OthersBtcBridgeState, OthersSolBridgeState, OthersUsdt1BridgeState,
                       OthersUsdt2BridgeState,
)


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

bot = AsyncTeleBot(TOKEN, state_storage=StateMemoryStorage(), parse_mode='Markdown')


async def bot_info_():
    return await bot.get_me()



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

async def calculate_slipage(owner, token, buyamt=1):
    get_slip = db_user.get_slippage(owner)
    token_price = await asset_price.main(token)
    ton_price = await asset_price.main('TON')
    
    expected_out = (buyamt*ton_price)/token_price
    limit = expected_out*(1-get_slip)
    
    return round(limit)

  
async def GenPnL(message, token):
    bot_info = await bot_info_()
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
    await bot.send_photo(owner, photo, msg, 'Markdown')
    

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


async def sbuy(message, token, amt):
    owner = message.chat.id
    slip = db_user.get_slippage(owner=owner)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    wallet = db_user.get_wallet(owner)
    bal = ton_bal(wallet)
    if bal > amt + 0.3 :
        await deploy(mnemonics)
        amount = await bot_fees(amt, owner)
        limit = await calculate_slipage(owner, token, amount)
        x = await bot.send_message(owner, f"Sent a buy transaction at ${abbreviate(get_mc(token))} MCap")
        buy = await jetton_swap(token, mnemonics, amount, limit)
        await asyncio.sleep(20)
        if buy == 1:
            ref = db_userd.get_referrer(owner)
            am = sell_fees(amt)
            ref_fee = ref_fees(am)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            await bot.delete_message(owner, x.message_id)
            await bot.send_message(owner, f"Bought {await jetton_bal(token,wallet)} of [{get_name(token)}](https://tonviewer.com/transaction/{await tx_hash.main(wallet)})", parse_mode='Markdown')
        else:
            await bot.send_message(owner, "⚠️ Buy failed")
            
    else:
        await bot.send_message(owner, "⚠️ Balance is low")
        
        
        
async def sell(message, addr, amount):
    owner = message.chat.id
    slip = db_user.get_slippage(owner=owner)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    wallet = db_user.get_wallet(owner)
    j_bal = await jetton_bal(addr, wallet)
    t_bal = ton_bal(wallet)
    if j_bal >= amount and t_bal > 0.3:
        x  = await bot.send_message(owner, f"Sent a sell transaction at ${abbreviate(get_mc(addr))} MCap")
        dec1 = await update(addr)
        dec = int(dec1['decimals'])
        print(type(dec))
        decimal = 10**dec
        print(decimal)
        j_price = await main_price(amount, addr, decimal)
        print(j_price)
        limit = await calculate_slipage(owner, addr, j_price)
        selled = await ton_swap(addr,mnemonics,amount, limit)
        await asyncio.sleep(20)
        await bot_fees(j_price, owner)
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
            
            await bot.send_message(owner, f"Successfully sold {amount} tokens")
        else:
            await bot.send_message(owner, "⚠️ Failed to swap tokens")
            
    else:
        await bot.send_message(owner, "⚠️Swap failed make sure there's enough Ton for gas or token amount is enough")


async def track(message, token):
    bot_info = await bot_info_()
    owner = message.chat.id
    #token = db_trades.get_last_ca(owner)
    wallet = db_user.get_wallet(owner)
    token_bal = await jetton_bal(token, wallet)
    slip = db_user.get_slippage(owner)
    name = get_name(token)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    symbol = get_symbol(token)
    pool = get_pool(token)
    lp = get_lp(token)
    pair = get_pair(token)
    mintable = await metadata.mint(token)
    renounce = await metadata.owner(token)
    if token_bal > 0:
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
        await bot.send_message(owner, msg, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)
        #bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
    else:
        await bot.send_message(owner, "Zero Token Balance")
        
        
#Dev commands 

@bot.message_handler(commands=['getstats'])
async def getstats(message):
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
        await bot.send_document(messager,doc)
        
                

@bot.message_handler(commands=['broadcast'])
async def broadcast(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        await bot.set_state(message.from_user.id, BroadcastState.msg, message.chat.id)

        send = await bot.send_message(message.chat.id,"Enter message to broadcast")
        print("ok")
        
    else:
        await bot.reply_to(message, "You're not allowed to use this command")
        
        

db_userd.add_user(username_= 7034272819, wallet="UQCs_PQIq-FjctnPvWq8756ohqzIsDWYCvm4SjfpAy-SpDxG", referrer=7034272819)

@bot.message_handler(state = BroadcastState.msg)     
async def sendall(message):
    print("ok")
    users = db_user.get_users()
    print(message.text)
    for chatid in users:
        try:
            msg = await antiflood(bot.send_message, chatid, message.text)
        except Exception as e:
            print(e)
        
    await bot.send_message(message.chat.id, "done")
    await bot.delete_state(message.from_user.id, message.chat.id)
    

@bot.message_handler(commands=['userno'])
async def userno(message):
    print(message.from_user.id)
    messager = message.chat.id
    if str(messager) == "7034272819" or str(messager) == "6219754372":
        x = db_user.get_users()
        await bot.reply_to(message,f"Total bot users: {len(x)}")
    else:
        await bot.reply_to(message, "admin command")



@bot.message_handler(commands=['start'])
async def start(message):
    bot_info = await bot_info_()
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
    btn2 = types.InlineKeyboardButton(f"{ton_bal(wallet_address)} Ton", callback_data='us')
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
            await track(message, ca)
            await bot.delete_message(owner, message.message_id)
        elif str(referrer).startswith('genpnl'):
            ca = extract_ca_pnl(referrer)
            await GenPnL(message, ca)
            await bot.delete_message(owner, message.message_id)    
        elif str(referrer).isdigit():
            if referrer == owner:
                await bot.send_message(owner, "You can't be your own referrer")
                db_userd.add_user(owner, wallet_address, 7034272819)
                db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                await bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
            else:
                if db_userd.get_referrer(referrer) == None:
                    await bot.send_message(owner, "Referrer not in database")
                    db_userd.add_user(owner, wallet_address, 7034272819)
                    db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                    await bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
                else:
                    if db_userd.get_referrer(owner) == None:
                        db_userd.add_user(owner, wallet_address, referrer=referrer)
                        ref = db_userd.get_referrals(referrer)
                        reff = ref + 1
                        db_userd.update_referrals(reff, referrer)
                        db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                        await bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
                    else:
                        db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
                        await bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
        else:
            pass
    else:
        db_userd.add_user(owner, wallet_address, 7034272819)
        db_user.add_user(username_= owner, mnemonics= new_nmemonics, wallet= wallet_address)
    
        await bot.send_message(message.chat.id, welcom, reply_markup=markup, parse_mode='Markdown')
 
 

    
@bot.message_handler(commands=['wallet'])
async def view_wallet(message):
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
    await bot.send_message(owner, msg, 'Markdown')
    
    
@bot.message_handler(commands=['support'])
async def support(message):
    await bot.reply_to(message, "For help or support join the official support community https://t.me/neuton_support\n You can read the docs for detailed example on bot usage https://neuton-bot.gitbook.io/neuton-trade-bot")

@bot.message_handler(commands=['referrals'])
async def ree(message):
    bot_info = await bot_info_()
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

*Rewards*: {round(db_userd.get_referrals_vol(owner), 5)}
"""

    await bot.send_message(owner, msg, 'Markdown',reply_markup=markup)
    
    
@bot.message_handler(commands=['positions'])
async def pos(message):
    bot_info = await bot_info_()
    owner = message.chat.id 
    wallet = db_user.get_wallet(owner)
    msg = "Open Positions\n\n"
    pos = await position.main(wallet)
    for i in pos:
            msg += f"[${i['jetton']['name']}](https://t.me/{bot_info.username}?start=track-{position.str_addr(i['jetton']['address'])}) *$ 0.0 Ton *\n"
    markup = types.InlineKeyboardMarkup()
    btn= types.InlineKeyboardButton('❌️ Close', callback_data="cancel")
    markup.add(btn)
    await bot.send_message(owner, msg, parse_mode='Markdown', reply_markup=markup)
    
    
    
@bot.message_handler(commands=['bridge'])
async def brid(message):
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
        
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
        
@bot.message_handler(commands=['airdrop'])
async def airdroped(message):
    owner = message.chat.id
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    msg = f"""

Easily transfer tokens to up to 256 TON addresses, each with a different amount.


⚠️ Ensure your TON Wallet has at least 2 TON to cover both Bot Fees (1 TON) and Network Fees.
Your airdrop wallet for this operation is:
`{await airdrop.get_wallet(mnemonics)}` (same mnemonics as your bot wallet).

⚠️ Make sure all tokens are sent to the designated wallet 
`{await airdrop.get_wallet(mnemonics)}` 

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
    await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
    
    
@bot.message_handler(commands=['withdraw'])
async def withdraw(message):
    await bot.reply_to(message, "Reply to this message with the wallet address to withdraw to and ton amount seperated by comma\nExample: WITHDRAW-WALLET, 10")
    await bot.set_state(message.from_user.id, WithdrawState.msg, message.chat.id)


@bot.message_handler(state=WithdrawState.msg)    
async def tonwithdraw(message):
    msg = message.text
    all = msg.split(",")
    owner = message.chat.id
    mn = db_user.get_mnemonics(owner)
    mnemonics = eval(decrypt(mn))
    wallet = all[0]
    amount = float(all[1])
    print(wallet)
    print(amount)
    wallet_ = db_user.get_wallet(owner)
    bal = ton_bal(wallet_)
    await bot.delete_state(message.from_user.id, message.chat.id)
    try:
        if bal >= amount:
            await send_ton(wallet, amount,mnemonics)
            asyncio.sleep(20)
            msg = f"""Sent {amount} Ton to {wallet} with [Tx Hash](https://tonscan.org/address/{wallet}#transactions)"""
            await bot.send_message(message.chat.id, msg, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            await bot.send_message(message.chat.id, "⚠️ Amount higher than Wallet Balance")
            
    except Exception as e:
        print(e)
        await bot.send_message(message.chat.id, "⚠️ Transaction could not be prossesed")
        
    
@bot.message_handler(state=OthersEthBridgeState.amount) 
async def toneth(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'eth', 'eth')
        if amt < min:
            await bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            await bot.set_state(owner, OthersEthBridgeState.amount, owner)
        else:
            db_bridge.update_amount(amt, owner)
            s = await bot.send_message(owner, "send Wallet to bridge to: ")
            await bot.set_state(owner, OthersEthBridgeState.wallet, owner)
    except Exception as e:
        await bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        await bot.set_state(owner, OthersEthBridgeState.amount, owner)  
        
@bot.message_handler(state=OthersEthBridgeState.wallet)      
async def toneth1y(message):
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
        
        await bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        await bot.send_message(owner, "Request could not be processed")
        
        
@bot.message_handler(state=OthersSolBridgeState.amount)       
async def solton(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'sol', 'sol')
        if amt < min:
            await bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            await bot.set_state(owner, OthersSolBridgeState.amount, owner)
        else:
            db_bridge.update_amount(amt, owner)
            s = await bot.send_message(owner, "send Wallet to bridge to: ")
            await bot.set_state(owner, OthersSolBridgeState.wallet, owner)
    except Exception as e:
        await bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        await bot.set_state(owner, OthersSolBridgeState.amount, owner)
        

@bot.message_handler(state=OthersSolBridgeState.wallet)       
async def tonsol1y(message):
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
        
        await bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        print(e)
        
  
@bot.message_handler(state=OthersBtcBridgeState.amount)      
async def tonbtc(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'btc', 'btc')
        if amt < min:
            await bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            await bot.set_state(owner, OthersBtcBridgeState.amount, owner)
        else:
            db_bridge.update_amount(amt, owner)
            s = await bot.send_message(owner, "send Wallet to bridge to: ")
            await bot.set_state(owner, OthersBtcBridgeState.wallet, owner)
    except Exception as e:
        await bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        await bot.set_state(owner, OthersBtcBridgeState.wallet, owner)
        
        
@bot.message_handler(state=OthersBtcBridgeState.wallet)
async def tonbtc1y(message):
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
        
        await bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        print(e)
        

@bot.message_handler(state=OthersUsdt1BridgeState.amount)       
async def tonerc(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'eth', 'usdt')
        if amt < min:
            await bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            await bot.set_state(owner, OthersUsdt1BridgeState.amount, owner)
        else:
            db_bridge.update_amount(amt, owner)
            s = await bot.send_message(owner, "send Wallet to bridge to: ")
            await bot.set_state(owner, OthersUsdt1BridgeState.wallet, owner)
    except Exception as e:
        await bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        await bot.set_state(owner, OthersUsdt1BridgeState.amount, owner)  
        
 
@bot.message_handler(state=OthersUsdt1BridgeState.wallet)       
async def tonerc1y(message):
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
        
        await bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        print(e)
        
@bot.message_handler(state=OthersUsdt2BridgeState.amount)       
async def tontrc(message):
    owner = message.chat.id
    try:
        amt = float(message.text)
        min = minimum('ton','ton', 'trx', 'usdt')
        if amt < min:
            await bot.send_message(owner, "Amount Lower than Minimum bridge amount {min}\nEnter amount: ")
            await bot.set_state(owner, OthersUsdt2BridgeState.amount,owner) 
        else:
            db_bridge.update_amount(amt, owner)
            s = await bot.send_message(owner, "send Wallet to bridge to: ")
            await bot.set_state(owner, OthersUsdt2BridgeState.wallet,owner) 
    except Exception as e:
        await bot.send_message(owner, "Invalid number\nPlease Enter a valid number: ")
        await bot.set_state(owner, OthersUsdt2BridgeState.amount,owner) 
        
@bot.message_handler(state=OthersUsdt2BridgeState.wallet)      
async def tontrc1y(message):
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
        
        await bot.send_message(owner, msg, reply_markup=markup, parse_mode="Markdown")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        print(e)
        
@bot.message_handler(state=BuySXState.amount)        
async def buy_sx(message):
    owner = message.chat.id
    token = db_trades.get_last_ca(owner)
    try:
        amount = float(message.text)
        
        await sbuy(message, token, amount)
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        print(e)
        await bot.send_message(owner, "⚠️ Invalid amount!")
        
@bot.message_handler(state=TonBridgeEthState.amount)       
async def etht1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('eth','eth','ton','ton')
    if initial < min:
        s = await bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        await bot.set_state(owner, TonBridgeEthState.amount, owner)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm')
        out = output('eth','eth','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} ETH* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        await bot.delete_state(message.from_user.id, message.chat.id)
        
        
@bot.message_handler(state = TonBridgeSolState.amount)    
async def sol1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('sol','sol','ton','ton')
    if initial < min:
        s = await bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        await bot.set_state(owner, TonBridgeSolState.amount, owner)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm1')
        out = output('sol','sol','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} SOL* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        await bot.delete_state(message.from_user.id, message.chat.id)
        
        
@bot.message_handler(state=TonBridgeBaseState.amount)     
async def base1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('eth','base','ton','ton')
    if initial < min:
        s = await bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        await bot.set_state(owner, TonBridgeBaseState.amount, owner)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm2')
        out = output('eth','base','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} Base* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        await bot.delete_state(message.from_user.id, message.chat.id)
        
        
@bot.message_handler(state=TonBridgeBtcState.amount)       
async def btc1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('btc','btc','ton','ton')
    if initial < min:
        s = await bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        await bot.set_state(owner, TonBridgeBtcState.amount, owner)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm3')
        out = output('btc','btc','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} BTC* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        

@bot.message_handler(state=TonBridgeBnbState.amount)        
async def bnb1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('bnb','bsc','ton','ton')
    if initial < min:
        s = await bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        await bot.set_state(owner, TonBridgeBnbState.amount, owner)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm4')
        out = output('bnb','bsc','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} BNB* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        await bot.delete_state(message.from_user.id, message.chat.id)
        
@bot.message_handler(state=TonBridgeUsdt1State.amount)
async def erc1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('usdt','eth','ton','ton')
    if initial < min:
        s = await bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        await bot.set_state(owner, TonBridgeUsdt1State.amount, owner)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm5')
        out = output('usdt','eth','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} USDT(ERC20)* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        await bot.delete_state(message.from_user.id, message.chat.id)
        

@bot.message_handler(state=TonBridgeUsdt2State.amount)
async def trc1(message):
    owner = message.chat.id
    wallet = db_user.get_wallet(owner)
    try:
        initial = float(message.text)
        db_bridge.update_amount(initial, owner)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        
    min = minimum('usdt','trx','ton','ton')
    if initial < min:
        s = await bot.send_message(owner, "bridge amount lower than minimum bridge amount\nPlease enter amount: ")
        await bot.set_state(owner, TonBridgeUsdt2State.amount, owner)
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Confirm Bridge ', callback_data='confirm6')
        out = output('usdt','trx','ton', 'ton', initial)
        msg = f"""You're about to swap *{initial} USDT(TRC20)* to *{out} Ton* to your wallet address `{wallet}`
        
Click on the button below to confirm swap 
        """
        markup.add(btn)
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        await bot.delete_state(message.from_user.id, message.chat.id)
        
        
@bot.message_handler(state=SellXState.amount)
async def sellix(message):
    owner = message.chat.id
    try:
        initial = float(message.text)
    except Exception as e:
        await bot.send_message(message.chat.id, "⚠️ Message should be a number ")
    owner = message.chat.id
    token = db_trades.get_last_ca(owner)
    wallet = db_user.get_wallet(owner)
    bal = await jetton_bal(token,wallet)
    #print(call.data)
    if bal > initial:
        await sell(message, token, initial)
        await asyncio.sleep(20)
        await bot.delete_state(message.from_user.id, message.chat.id)
        
        
@bot.message_handler(state = BuyXState.amount, )        
async def buy_x(message):
    print(message.text)
    try:
        initial = float(message.text)
    except Exception as e:
        await bot.send_message(message.chat.id, "Message should be a number ")
        await bot.delete_state(message.from_user.id, message.chat.id)
        pass
    owner = message.chat.id
    bot_info = await bot_info_()
    token = db_trades.get_last_ca(owner)
    name = get_name(token)
    mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
    
    wallet= db_user.get_wallet(owner)
    bal = ton_bal(wallet)
    #print(call.data)
    slip = db_user.get_slippage(owner)
    if bal > initial:
        await deploy(mnemonics)
        amount = await bot_fees(initial, owner)
        limit = await calculate_slipage(owner, token,amount)
        x = await bot.send_message(owner, f"Sent a buy transaction at ${abbreviate(get_mc(token))} MCap")
        buy = await jetton_swap(token, mnemonics, amount, limit)
        await asyncio.sleep(20)
        if buy == 1:
            ref = db_userd.get_referrer(owner)
            am = sell_fees(amount)
            ref_fee = ref_fees(am)
            get_ref_vol = db_userd.get_referrals_vol(ref)
            add_ref_vol = get_ref_vol + ref_fee
            db_userd.update_referrals_vol(add_ref_vol, ref)
            get_trad = db_userd.get_trading_vol(owner)
            add_trad = amount + get_trad
            db_userd.update_trading_vol(add_trad, owner)
            await bot.delete_message(owner, x.message_id)
            await bot.send_message(owner, f"Bought {await jetton_bal(token,wallet)} of [{get_name(token)}](https://tonviewer.com/transaction/{await tx_hash.main(wallet)})", parse_mode='Markdown')
            buy_mc = get_mc(token)
            pnl = (get_mc(token)-buy_mc)/buy_mc*100
            amt = initial
            db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
            x = get_url(token)
            chart = x['pairs'][0]['url']
            print(token)
            pool = get_pool(token)
            print(pool)
            mintable = await metadata.mint(token)
            renounce = await metadata.owner(token)
            name = get_name(token)
            symbol = get_symbol(token)
            pair = get_pair(token)
            lp = get_lp(token)
            msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*initial, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
            await bot.send_message(message.chat.id, msg, parse_mode='Markdown', reply_markup=markup, disable_web_page_preview=True)
            
            await bot.delete_state(message.from_user.id, message.chat.id)
            
        else:
                await bot.send_message(owner, "Swap Failed")
    else:
        await bot.send_message(owner, "Not Enough Balance.")
        
        
@bot.message_handler(state=SlippageState.slippage)     
async def setslip(message):
    owner = message.chat.id
    try:
        new_sli = float(message.text)
        new_slip = new_sli / 100
    except Exception as e:
        await bot.send_message(owner, "Invalid Number")
        
    db_user.update_slippage(new_slip, owner)
    await bot.send_message(owner, "Slippage updated")
    await bot.delete_state(message.from_user.id, message.chat.id)
    
    
@bot.message_handler(state=AirdropState.jetton)
async def air(message):
    jetton = message.text
    owner = message.chat.id
    send = await bot.send_message(message.chat.id,"Send Wallet and amount list seperated by comma: ")
    await bot.set_state(message.from_user.id, AirdropState.wallet, owner)
    db_airdrop.add_user(owner, jetton)
    #bot.delete_message(message.chat.id, message.message_id)
   
    
@bot.message_handler(state=AirdropState.wallet)   
async def drop(message):
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
        await bot.send_message(owner, "An error occurred\n Check your wallet list and try again")
        
    try:
        mn = db_user.get_mnemonics(owner)
        mnemonics = eval(decrypt(mn))
        address = db_airdrop.get_address(owner)
        await airdrop.main(mnemonics, address, destinations)
        await bot.send_message(owner, "Done")
        db_airdrop.delete_user(owner)
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        await bot.send_message(owner, "Failed To Send Tokens")
        print(e)
        
        

"""
This part of the code deals with Token Buy or Sell
"""
@bot.message_handler(func=lambda message: True)
async def trade(message):
    try:
        bot_info = await bot_info_()
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
        mintable = await metadata.mint(token)
        renounce = await metadata.owner(token)
        print(renounce)
        
        msg = f""" 
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
 
Ton: {ton_bal(wallet)}
 
💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}`
 
📈 *M Cap*: ${abbreviate(get_mc(token))} |💵 ${get_price(token)} 
 
♻️ *Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}

Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 
 
        """
       
        await bot.send_message(message.chat.id, msg, 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
        #db_trades.add(owner, name, token)
        db_trades.add(owner, name, token)
        
    except Exception as e:
        await bot.send_message(message.chat.id, "Invalid Token")
        print(e)
        



@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    bot_info = await bot_info_()
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
    mintable = await metadata.mint(token)
    renounce = await metadata.owner(token)
    
    if call.data == 'wallett':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss: `{db_user.get_wallet(owner)}`
        
Balance: *{ton_bal(wallet)} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🏦 Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('🏦 Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('🔎 Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('🔃 Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('🔙 Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
    elif call.data == 'track':
        await bot.pin_chat_message(owner, call.message.message_id)
        
    
    elif call.data =='wwithdraw':
        await withdraw(call.message)
        
    elif call.data == 'deposit':
        print(call.data)
        msg = f"""Deposit Ton into your address
        
        
`{db_user.get_wallet(owner)}` (tap to copy)

Manually Send ton to the address above 

*Do not send Ton Space to this Account!!!*

        """
        
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Back', callback_data='back')
        markup.add(btn)
        
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup, parse_mode='Markdown')
        
        
    elif call.data == 'view':
        await view_wallet(call.message)
        
        
    elif call.data == 'airdrop':
        await airdroped(call.message)
        
    elif call.data == 'startmass':
        send = await bot.send_message(owner, "send Jetton Address")
        await bot.set_state(call.from_user.id, AirdropState.jetton, owner)
        
        
    elif call.data == 'wrefresh':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss : `{db_user.get_wallet(owner)}`
        
Balance : *{ton_bal(wallet)} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🏦 Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('🏦 Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('🔎 Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('🔃 Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('🔙 Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
    elif call.data == 'home':
        await bot.delete_message(owner, call.message.message_id)
        await start(call.message)
    
    
    elif call.data == 'back':
        print("yessssssssss")
        mnemonics = eval(decrypt(db_user.get_mnemonics(owner)))
        msg = f"""Wallet Adresss : `{db_user.get_wallet(owner)}`
        
Balance : *{ton_bal(wallet)} Ton*
        """
        new_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🏦 Withdraw', callback_data='wwithdraw')
        btn2 = types.InlineKeyboardButton('🏦 Deposit', callback_data='deposit')
        btn3 = types.InlineKeyboardButton('🔎 Show Seed phrase', callback_data='view')
        btn4 = types.InlineKeyboardButton('🔃 Refresh', callback_data='wrefresh')
        btn5 = types.InlineKeyboardButton('🔙 Back', callback_data='home')
        
        new_markup.add(btn1,btn2,btn3,btn4,btn5)
        
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=new_markup, parse_mode='Markdown')
    
    
    elif call.data == 'position':
        msg = "Open Positions\n\n"
        pos = await position.main(wallet)
        for i in pos:
            msg += f"[${i['jetton']['name']}](https://t.me/{bot_info.username}?start=track-{position.str_addr(i['jetton']['address'])}) *$ 0.0 Ton *\n"
        markup = types.InlineKeyboardMarkup()
        btn= types.InlineKeyboardButton('❌️ Close', callback_data="cancel")
        markup.add(btn)
        await bot.send_message(owner, msg, parse_mode='Markdown', reply_markup=markup)
        
        
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

*Rewards*: {round(db_userd.get_referrals_vol(owner), 5)}
"""

        await bot.send_message(owner, msg, 'Markdown',reply_markup=markup)
        
        
    elif call.data == 'cancel':
        await bot.delete_message(owner, call.message.message_id)
        
        
    elif call.data == 'buy1':
        bal = ton_bal(wallet)
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 1:
            await deploy(mnemonics)
            amount = await bot_fees(1, owner)
            limit = await calculate_slipage(owner, token, 1)
            x = await bot.send_message(owner, f"Sent a buy transaction at ${abbreviate(get_mc(token))} MCap")
            buy = await jetton_swap(token, mnemonics, amount, limit)
            await asyncio.sleep(20)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                am = sell_fees(1)
                ref_fee = ref_fees(am)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                await bot.delete_message(owner, x.message_id)
                await bot.send_message(owner, f"Bought {await jetton_bal(token,wallet)} of [{get_name(token)}](https://tonviewer.com/transaction/{await tx_hash.main(wallet)})", parse_mode='Markdown')
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 1
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
                await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview= True,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                await bot.send_message(owner, "⚠️ Swap Failed")
        else:
            await bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == 'buy5':
        bal = ton_bal(wallet)
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 5:
            await deploy(mnemonics)
            amount = await bot_fees(5, owner)
            limit = await calculate_slipage(owner, token, 5)
            x = await bot.send_message(owner, f"Sent a buy transaction at ${abbreviate(get_mc(token))} MCap")
            buy = await jetton_swap(token, mnemonics, amount, limit)
            await asyncio.sleep(20)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                am = sell_fees(5)
                ref_fee = ref_fees(am)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                await bot.delete_message(owner, x.message_id)
                await bot.send_message(owner, f"Bought {await jetton_bal(token,wallet)} of [{get_name(token)}](https://tonviewer.com/transaction/{await tx_hash.main(wallet)})", parse_mode='Markdown')
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 5
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
                await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview= True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                await bot.send_message(owner, "⚠️ Swap Failed")
        else:
            await bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == "buy10":
        bal = ton_bal(wallet)
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 10:
            await deploy(mnemonics)
            amount = await bot_fees(10, owner)
            limit = await calculate_slipage(owner, token, 10)
            x = await bot.send_message(owner, f"Sent a buy transaction at ${abbreviate(get_mc(token))} MCap")
            buy = await jetton_swap(token, mnemonics, amount, limit)
            await asyncio.sleep(20)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                am = sell_fees(10)
                ref_fee = ref_fees(am)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                await bot.delete_message(owner, x.message_id)
                await bot.send_message(owner, f"Bought {await jetton_bal(token,wallet)} of [{get_name(token)}](https://tonviewer.com/transaction/{await tx_hash.main(wallet)})", parse_mode='Markdown')
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 10
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
                await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                await bot.send_message(owner, "⚠️ Swap Failed")
        else:
            await bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == "buy15":
        bal = ton_bal(wallet)
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 15:
            await deploy(mnemonics)
            amount = await bot_fees(15, owner)
            limit = await calculate_slipage(owner, token, 15)
            x = await bot.send_message(owner, f"Sent a buy transaction at ${abbreviate(get_mc(token))} MCap")
            buy = await jetton_swap(token, mnemonics, amount, limit)
            await asyncio.sleep(20)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                am = sell_fees(15)
                ref_fee = ref_fees(am)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                await bot.delete_message(owner, x.message_id)
                await bot.send_message(owner, f"Bought {await jetton_bal(token,wallet)} of [{get_name(token)}](https://tonviewer.com/transaction/{await tx_hash.main(wallet)})", parse_mode='Markdown')
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 15
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
                await bot.edit_message_text(chat_id=call.message.chat.id,disable_web_page_preview= True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                await bot.send_message(owner, "⚠️ Swap Failed")
        else:
            await bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == "buy20":
        bal = ton_bal(wallet)
        slip = db_user.get_slippage(owner)
        #print(call.data)
        if bal > 20:
            await deploy(mnemonics)
            amount = await bot_fees(20, owner)
            limit = await calculate_slipage(owner, token, 20)
            x = await bot.send_message(owner, f"Sent a buy  transaction at ${abbreviate(get_mc(token))} MCap")
            buy = await jetton_swap(token, mnemonics, amount, limit)
            await asyncio.sleep(20)
            if buy == 1:
                ref = db_userd.get_referrer(owner)
                am = sell_fees(20)
                ref_fee = ref_fees(am)
                get_ref_vol = db_userd.get_referrals_vol(ref)
                add_ref_vol = get_ref_vol + ref_fee
                db_userd.update_referrals_vol(add_ref_vol, ref)
                get_trad = db_userd.get_trading_vol(owner)
                add_trad = amount + get_trad
                db_userd.update_trading_vol(add_trad, owner)
                await bot.delete_message(owner, x.message_id)
                await bot.send_message(owner, f"Bought {await jetton_bal(token,wallet)} of [{get_name(token)}](https://tonviewer.com/transaction/{await tx_hash.main(wallet)})", parse_mode='Markdown')
                buy_mc = get_mc(token)
                pnl = (get_mc(token)-buy_mc)/buy_mc*100
                amt = 20
                db_trades.update(owner,token,name, buy_mc=buy_mc, buy_amount=amt)
                x = get_url(token)
                chart = x['pairs'][0]['url']
                msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
                await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
                
            else:
                await bot.send_message(owner, "⚠️ Swap Failed")
        else:
            await bot.send_message(owner, "⚠️ Not Enough Balance.")
            
            
    elif call.data == "buyx":
        send = await bot.send_message(owner, "Enter buy amount: ")
        #print(call)
        await bot.set_state(call.from_user.id, BuyXState.amount, call.message.chat.id)
        print("mmmm")
    
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
 
Ton: {ton_bal(wallet)}
 
💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *M Cap*: ${abbreviate(get_mc(token))} |💵 ${get_price(token)} 
 
♻️ *Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 
 
        """
       
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text= msg, parse_mode = 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
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
 
Ton: {ton_bal(wallet)}
 
💎 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *M Cap*: ${abbreviate(get_mc(token))} |💵 ${get_price(token)} 
 
♻️ *Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
💡 *(24h) B {get_url(token)['pairs'][0]['txns']['h24']['buys']} | S {get_url(token)['pairs'][0]['txns']['h24']['sells']} | {get_url(token)['pairs'][0]['priceChange']['h24']}% | Vol: $ {abbreviate(get_url(token)['pairs'][0]['volume']['h24'])}* 
 
        """
       
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text= msg, parse_mode = 'Markdown', reply_markup=markup, disable_web_page_preview=True) 
        db_trades.add(owner, name, token)
        
        
    elif call.data == "sellrefresh":
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
        await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == "sellrefresh1":
        print("sell11111111111111111111111111")
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
        await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == 'sell25':
        token_bal = await jetton_bal(token, wallet)
        
        amount = token_bal * 0.25
        await sell(call.message, token, amount)
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
        await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == 'sell50':
        token_bal = await jetton_bal(token, wallet)
        
        amount = token_bal * 0.5
        await sell(call.message, token, amount)
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}
Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
        await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == 'sell75':
        token_bal = await jetton_bal(token, wallet)
        
        amount = token_bal * 0.75
        await sell(call.message, token, amount)
        buy_mc = 1 if db_trades.get_buy_mc(owner, token) == None else db_trades.get_buy_mc(owner,token)
        pnl = (get_mc(token)-buy_mc)/buy_mc*100
        amt = 0 if db_trades.get_buy_amt(owner, token) == None else db_trades.get_buy_amt(owner, token)
        x = get_url(token)
        chart = x['pairs'][0]['url']
        msg = f"""
💠 *{name}* (${symbol}): 🌐 {pool} 

*Balance*:  
{name}: {await jetton_bal(token, wallet)} 
Ton: {ton_bal(wallet)} 
                 
{'🟩' if round(pnl, 2) > 0.0 else '🟥'} *profit*: {1 if round(pnl, 2) > 10000 else round(pnl, 2)} % [PnL 🖼️](https://t.me/{bot_info.username}?start=genpnl-{token}) | 💎 {round((get_mc(token)/buy_mc)*amt, 2)} Ton 
 
🏠 *CA*: `{token}` [🅲](https://tonscan.org/address/{token}) 
 
💹 *LP*: `{pair}` 
 
📈 *MCap*: ${abbreviate(get_mc(token))} *USD* |💵 ${get_price(token)} 
 
♻️ * Liquidity*: {lp} TON 
 
mintable: {"⚠️" if mintable == True else "✅️"}

Renounced: {"✅️" if renounce == "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c" else "❌️"}

*Quick Insight*
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
        await bot.edit_message_text(chat_id=call.message.chat.id, disable_web_page_preview=True ,message_id=call.message.message_id, text= msg, parse_mode='Markdown', reply_markup=markup)
        
        
    elif call.data == 'sell100':
        token_bal = await jetton_bal(token, wallet)
        
        amount = token_bal * 1
        await sell(call.message, token, amount)
        await asyncio.sleep(20)
        await bot.delete_message(owner, call.message.message_id)
        
    elif call.data == 'sellx':
        send = await bot.send_message(owner, "send Number of tokens you want to sell: ")
        await bot.set_state(call.from_user.id, SellXState.amount, owner)
        
        
        
    elif call.data == 'set_slip':
        send = await bot.send_message(owner, "Enter slippage:")
        await bot.set_state(call.from_user.id, SlippageState.slippage, owner)
        
    
    elif call.data == "buysx":
        s = await bot.send_message(owner, "Enter buy amount: ")
        await bot.set_state(call.from_user.id, BuySXState.amount, owner)
        
        
    elif call.data == "buys5":
        await sbuy(call.message, token, 5)
        
        
    elif call.data == 'buys10':
        await sbuy(call.message, token, 10)
        
        
    elif call.data == 'bridge':
        await bot.delete_message(owner, call.message.message_id)
        await brid(call.message)
        
    
    elif call.data == 'ethton':
        min = minimum('eth','eth','ton','ton')
        msg = f"You're Swaping from ETH to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, TonBridgeEthState.amount, owner)
        
        
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)  
        
        
    elif call.data == 'solton':
        min = minimum('sol','sol','ton','ton')
        msg = f"You're Swaping from SOL to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, TonBridgeSolState.amount, owner)
        
        
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'baseton':
        min = minimum('eth','base','ton','ton')
        msg = f"You're Swaping from BASE to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, TonBridgeBaseState.amount, owner)
        
        
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'btcton':
        min = minimum('btc','btc','ton','ton')
        msg = f"You're Swaping from BTC to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, TonBridgeBtcState.amount, owner)
        
        
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'bnbton':
        min = minimum('bnb','bsc','ton','ton')
        msg = f"You're Swaping from BNB to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, TonBridgeBnbState.amount, owner)
        
        
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'ercton':
        min = minimum('usdt','eth','ton','ton')
        msg = f"You're Swaping from USDT(ERC20) to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, TonBridgeUsdt1State.amount, owner)
        
        
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'trcton':
        min = minimum('usdt','trx','ton','ton')
        msg = f"You're Swaping from USDT(TRC20) to TON\n Minimum amount to swap is {min}\n Enter swap amount below:"
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, TonBridgeUsdt2State.amount, owner)
        
        
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'tonbridge':
        await bot.delete_message(owner, call.message.message_id)
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
        
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        
    elif call.data == 'toneth':
        min = minimum('ton', 'ton', 'eth', 'eth')
        msg = f"Minimum bridge amount for TON to ETH is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, OthersEthBridgeState.amount, owner)
    elif call.data == 'tonsol':
        min = minimum('ton', 'ton', 'sol', 'sol')
        msg = f"Minimum bridge amount for TON to SOL is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, OthersSolBridgeState.amount, owner)
        
    elif call.data == 'tonerc':
        min = minimum('ton', 'ton', 'eth', 'usdt')
        msg = f"Minimum bridge amount for TON to USDT(ERC20) is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, OthersUsdt1BridgeState.amount)
    elif call.data == 'tonbtc':
        min = minimum('ton', 'ton', 'btc', 'btc')
        msg = f"Minimum bridge amount for TON to BTC is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, OthersBtcBridgeState.amount, owner)
    elif call.data == 'tontrc':
        min = minimum('ton', 'ton', 'trx', 'usdt')
        msg = f"Minimum bridge amount for TON to USDT(TRC20) is {min}\n Please enter bridge amount: "
        db_bridge.add_user(owner)
        s = await bot.send_message(owner, msg)
        await bot.set_state(owner, OthersUsdt2BridgeState.amount, owner)
        
        
    elif call.data == 'tonethc':
        await bot.delete_message(owner, call.message.message_id)
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
        
    elif call.data == 'tonbtcc':
        await bot.delete_message(owner, call.message.message_id)
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'tonsolc':
        await bot.delete_message(owner, call.message.message_id)
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
        
    elif call.data == 'tonercc':
        await bot.delete_message(owner, call.message.message_id)
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)
        
    
    elif call.data == 'tontrcc':
        await bot.delete_message(owner, call.message.message_id)
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
        await bot.send_message(owner, msg, 'Markdown', reply_markup=markup)
        db_bridge.del_user(owner)

       
        
bot.add_custom_filter(asyncio_filters.StateFilter(bot))

        
asyncio.run(bot.polling())