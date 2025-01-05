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
    :return: Lista de direcciones y cantidades en función del modo seleccionado
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

        if mode == "vout":
            # Procesar direcciones de salida (vout) y valores
            vout_addresses = []
            for vout in transaction_info.get('vout', []):
                address = vout.get('scriptPubKey', {}).get('address')  # Extraemos la dirección directamente de 'address'
                value = vout.get('value')  # Extraemos el valor de la transacción
                vout_index = vout.get('n')  # Extraemos el vout_index
                if address and value and vout_index is not None:
                    # Convertimos el valor a flotante y lo redondeamos a 8 decimales
                    formatted_value = round(value, 8)
                    vout_addresses.append({"address": address, "value": formatted_value, "vout_index": vout_index})


            return vout_addresses

        else:
            return []

    except requests.exceptions.RequestException as e:
        return []


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
        print(f"Error fetching mempool transactions: {e}")
        return []


# Obtener todos los Txid de Transacciones Pendientes
getTransaccionesPendientesMempool = get_mempool_transactions()

for i, tx_hash in enumerate(getTransaccionesPendientesMempool):

    # del Txid sacamos las direcciones
    tx_direcciones = get_transaction_addresses(tx_hash)
    for addr_info in tx_direcciones:
        
        # Aseguramos que la información tenga ambos valores (dirección y valor)
        if addr_info and 'address' in addr_info and 'value' in addr_info:
            address = addr_info['address']
            btcRecibido = addr_info['value'] # Cantidad de Bitcoin Recibido
            getVoutIndex = addr_info['vout_index'] # Vout_index del deposito
            
            # Verificamos que la dirección no esté vacía y que comience con '1'
            if address.startswith('1'):
                print(f"{address} :: BTC Recibido: {btcRecibido} :: Vout index {getVoutIndex} :: Txid: {tx_hash}")