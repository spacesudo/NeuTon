import requests

def get_url(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return "failed to connect try again later"
    
def get_mc(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['pairs'][0]["fdv"]
        
        return mc
    else:
        return "failed to connect try again later"
    

def get_name(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['pairs'][0]['baseToken']['name']
        
        return mc
    else:
        return "failed to connect try again later"


def get_price(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['pairs'][0]['priceUsd']
        
        return mc
    else:
        return "failed to connect try again later"



def get_symbol(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['pairs'][0]['baseToken']['symbol']
        
        return mc
    else:
        return "failed to connect try again later"
    
    
def get_pool(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['pairs'][0]['dexId']
        return mc.capitalize()
    else:
        return "failed to connect try again later"
    
 
def get_decimal(addr: str):
    url = f"https://api.geckoterminal.com/api/v2/networks/ton/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['data']['attributes']['decimals']
        return mc
    else:
        return "failed to connect try again later"   
    
    
def get_lp(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['pairs'][0]['liquidity']['quote']
        return mc
    else:
        return "failed to connect try again later"
    
    
def get_pair(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()['pairs'][0]['pairAddress']
        return mc
    else:
        return "failed to connect try again later"
    
    
def get_pairp(addr: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
    response = requests.get(url)
    if response.status_code == 200:
        mc = response.json()
        return mc
    else:
        return "failed to connect try again later"
    
    
#print(get_lp('0x8b1869f79b9abF52001314A2E6990A96F039058D'))

#print(get_url("EQBlqsm144Dq6SjbPI4jjZvA1hqTIP3CvHovbIfW_t-SCALE")['pairs'][0]['txns']['h24']['buys'])