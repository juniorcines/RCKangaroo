import os
import hashlib
import requests
import json
from requests.auth import HTTPBasicAuth

import time
from bitcoinx import (
    private_key_to_public_key,
    pubkey_to_bitcoin_address,
    btcPrivatekeyHextoWIF,
)

from getz_input import (
    parseTx,
    getSignableTxn
)

from bit import Key
from bit.network import NetworkAPI

# RPC BTC
btcHost = '127.0.0.1'
auth = HTTPBasicAuth('anigametv', 'gotech2020')


# Obtener todas las direcciones del tx que son direcciones que estan recibiendo fondos
def get_transaction_addresses(txid=None, mode="vout"):
    """
    Obtiene las direcciones de una transacción en función del modo: entradas (vin) o salidas (vout).

    :param txid: ID de la transacción (txid)
    :param mode: "vin" para direcciones que envían, "vout" para direcciones que reciben
    :return: Lista de direcciones en función del modo seleccionado
    """
    if not txid:
        return {"error": "Debe proporcionar un txid válido."}

    data = {
        "method": "getrawtransaction",
        "params": [txid, True],  # Solicitar transacción decodificada
        "id": 1
    }

    try:
        # Realizar la solicitud al servidor Bitcoin (puedes cambiar 'btcHost' y 'auth' según corresponda)
        response = requests.post(f'http://{btcHost}:8332/', json=data, auth=auth, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        transaction_info = response.json().get('result')

        # Si no se encuentra la información de la transacción, devolver una lista vacía
        if not transaction_info:
            return []

        if mode == "vin":
            # Procesar direcciones de entrada (vin) - aunque no se tiene acceso directo a las direcciones de entrada
            vin_addresses = []
            for vin in transaction_info.get('vin', []):
                # Las entradas generalmente no contienen direcciones directas, pero se puede obtener el txid y vout.
                # Es necesario obtener más información de la transacción anterior si es necesario.
                vin_addresses.append(vin.get('txid'))  # Aquí sólo guardamos el txid de las entradas
            return vin_addresses

        elif mode == "vout":
            # Procesar direcciones de salida (vout)
            vout_addresses = []
            for vout in transaction_info.get('vout', []):
                address = vout.get('scriptPubKey', {}).get('address')  # Extraemos la dirección directamente de 'address'
                if address:
                    vout_addresses.append(address)

            return vout_addresses

        else:
            return []

    except requests.exceptions.RequestException as e:
        return []


# Obtener las transacciones pendiente que aun no esta en los bloque
def get_mempool_transactions():
    data = {
        "method": "getrawmempool",
        "params": [],  # Sin parámetros adicionales
        "id": 1
    }

    try:
        response = requests.post(f'http://{btcHost}:8332/', json=data, auth=auth, headers={'Content-Type': 'application/json'})
        response.raise_for_status()  # Verifica si la solicitud tuvo éxito
        result = response.json().get('result')
        return result  # Esto será una lista de IDs de transacciones pendientes
    
    except requests.exceptions.RequestException as e:

        return []


# Obtener todos los Txid de Transacciones Pendientes
getTransaccionesPendientesMempool = get_mempool_transactions()

print(getTransaccionesPendientesMempool)

'''
for i, tx_hash in enumerate(getTransaccionesPendientesMempool):

    # del Txid sacamos las direcciones
    tx_direcciones = get_transaction_addresses(tx_hash)
    for addr in tx_direcciones:

        # Verificamos que no este vacio, esto devuelve la direccion que tiene los tx y que la direccion comienze con 1
        if addr and addr.startswith('1'): 

            print(f"{addr} :: Txid: {tx_hash}")
'''