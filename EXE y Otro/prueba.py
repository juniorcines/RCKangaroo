import os
import requests
from requests.auth import HTTPBasicAuth
import json

from getz_input import (
    parseTx,
    getSignableTxn
)

from bitcoinx import (
    pubkey_to_bitcoin_address
)

# RPC BTC
btcHost = '127.0.0.1'
auth = HTTPBasicAuth('anigametv', 'gotech2020')

# Obtener Numero del Bloque
def get_latest_block_number():
    data = {
        "method": "getblockcount",
        "params": [],
        "id": 1
    }

    try:
        response = requests.post(f'http://{btcHost}:8332/', json=data, auth=auth, headers={'Content-Type': 'application/json'})
        response.raise_for_status()  # Raises an error for 4xx/5xx status codes
        result = response.json().get('result')
        return result
    except requests.exceptions.RequestException as e:
        return False


# Obtener Informacion del Bloque por el hash pasando el numero
def obtener_info_bloque(block_number):
    
    # Obtener el hash del bloque usando el número del bloque
    data = {
        "method": "getblockhash",
        "params": [block_number],
        "id": 1
    }

    try:
        response = requests.post(f'http://{btcHost}:8332/', json=data, auth=auth, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        block_hash = response.json().get('result')
        
        # Obtener la información del bloque usando el hash del bloque
        data = {
            "method": "getblock",
            "params": [block_hash],
            "id": 1
        }
        response = requests.post(f'http://{btcHost}:8332/', json=data, auth=auth, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        block_info = response.json().get('result')

        # Extraer hash del bloque y array de transacciones
        block_hash = block_info.get('hash')
        tx_array = block_info.get('tx')
        getmerkleroot = block_info.get('merkleroot')
        
        return block_hash, tx_array, getmerkleroot

    except requests.exceptions.RequestException as e:
        print(f'Error fetching block info: {e}')
        return None, []



# Obtener todas las direcciones del tx
def get_transaction_addresses(txid):
    data = {
        "method": "getrawtransaction",
        "params": [txid, True],
        "id": 1
    }

    try:
        response = requests.post(f'http://{btcHost}:8332/', json=data, auth=auth, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        transaction_info = response.json().get('result')

        getRAWTX = transaction_info['hex']
        
        m = parseTx(getRAWTX)

        if isinstance(m, dict) and "error" in m:
            return []

        e = getSignableTxn(m)

        # Extraer direcciones de salida 
        addresses = set()

        for i in range(len(e)):
            pubKey = e[i][3]
            # Convertir PubKey a Address
            getAddress = pubkey_to_bitcoin_address(pubKey)
            addresses.add(getAddress)


        return addresses

    except requests.exceptions.RequestException as e:
        return []


# Obtener el número del último bloque
#latest_block_number = get_latest_block_number()
getHashBlock, getTxList, getmerkleroot = obtener_info_bloque(1)
#getAddressWithTx = get_transaction_addresses('14ab355e571762bd4d0ee8c6542728b5163678a2f58742635e9d3968f3d50c76')

print(getmerkleroot)