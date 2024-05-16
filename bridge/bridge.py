import requests
from dotenv import load_dotenv
import os

KEY = os.getenv('BRIDGE_API')

import requests
import json

def exchange(from_curr,from_net, to_net , to_curr, amount, address):
  url = "https://api.changenow.io/v2/exchange"

  payload = json.dumps({
    "fromCurrency": from_curr,
    "toCurrency": to_curr,
    "fromNetwork": from_net,
    "toNetwork": to_net,
    "fromAmount": amount,
    "toAmount": "",
    "address": address,
    "extraId": "",
    "refundAddress": "",
    "refundExtraId": "",
    "userId": "",
    "payload": "",
    "contactEmail": "",
    "source": "",
    "flow": "standard",
    "type": "direct",
    "rateId": ""
})
  headers = {
    'Content-Type': 'application/json',
    'x-changenow-api-key': KEY
  }

  response = requests.request("POST", url, headers=headers, data=payload)
  return response.json()



def minimum(from_curr, from_net, to_net , to_curr):

  url = f"https://api.changenow.io/v2/exchange/min-amount?fromCurrency={from_curr}&toCurrency={to_curr}&fromNetwork={from_net}&toNetwork={to_net}&flow=standard"

  payload={}
  headers = {
    'x-changenow-api-key': KEY
  }

  response = requests.request("GET", url, headers=headers, data=payload)
  return response.json()


def tx_id(tx_id):
  url = f"https://api.changenow.io/v2/exchange/by-id?id={tx_id}"

  payload={}
  headers = {
    'x-changenow-api-key': KEY
  }

  response = requests.request("GET", url, headers=headers, data=payload)
  return response.json()
