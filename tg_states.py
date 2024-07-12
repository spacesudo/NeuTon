from telebot import asyncio_filters
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup

class BroadcastState(StatesGroup):
    msg = State()
    
    
class AirdropState(StatesGroup):
    jetton = State()
    wallet = State()
    
    
class BuyXState(StatesGroup):
    amount = State()
    
    
class BuySXState(StatesGroup):
    amount = State()
    
    
class SellXState(StatesGroup):
    amount = State()
    
    
class SlippageState(StatesGroup):
    slippage = State()
    
       
class WithdrawState(StatesGroup):
    msg = State()
    
    
class TonBridgeEthState(StatesGroup):
    amount = State()
    
    
class TonBridgeSolState(StatesGroup):
    amount = State()
    
    
class TonBridgeBaseState(StatesGroup):
    amount = State()
    
    
class TonBridgeBtcState(StatesGroup):
    amount = State()
    

class TonBridgeUsdt1State(StatesGroup):
    amount = State()
    
    
class TonBridgeUsdt2State(StatesGroup):
    amount = State()
    
    
class TonBridgeBnbState(StatesGroup):
    amount = State()
    
    
class OthersEthBridgeState(StatesGroup):
    amount = State()
    wallet = State()
    
    
class OthersSolBridgeState(StatesGroup):
    amount = State()
    wallet = State()
    
    
class OthersBtcBridgeState(StatesGroup):
    amount = State()
    wallet = State()
    

class OthersUsdt1BridgeState(StatesGroup):
    amount = State()
    wallet = State()
    
    
class OthersUsdt2BridgeState(StatesGroup):
    amount = State()
    wallet = State()