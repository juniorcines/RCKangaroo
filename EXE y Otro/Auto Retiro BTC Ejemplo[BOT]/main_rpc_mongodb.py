import os
import time
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

from pymongo import MongoClient

# Configurar la conexión a MongoDB
client = MongoClient("mongodb://animeflv:Onyx01091995@onyx.i234.me:27017/")
db = client["admin"]  # Nombre de la base de datos
collection = db["vulnerable_wallet"]  # Nombre de la colección

# Crear un índice único en el campo address para evitar duplicados
collection.create_index("address", unique=True)

def guardar_datos_masivo(direcciones_wif):
    """
    Guarda múltiples direcciones y sus WIFs en MongoDB.
    Si una dirección ya existe, se ignora.
    """
    # Preparar documentos para insertar
    current_timestamp = time.time()
    timestamp_without_decimal = int(current_timestamp)
    documentos = [{"address": address, "wif": wif, "timestamp": timestamp_without_decimal } for address, wif in direcciones_wif.items()]

    if documentos:
        try:
            # Insertar documentos ignorando duplicados
            collection.insert_many(documentos, ordered=False)
            #print(f"Se han guardado {len(documentos)} direcciones en la base de datos.")
            
        except Exception as e:
            # Captura cualquier excepción
            #print(f"Error inesperado al insertar documentos: {e}")
            pass



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
        return None, [], None


# Obtener todas las direcciones del tx
def get_transaction_addresses(txid=None):

    if not txid:
        return []


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

        if not getRAWTX:
            return []
        
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
        print(f"Ocurrio Error al obtener address: {e}")
        return []



# Función para generar direcciones y WIF
def generar_direcciones_y_wif(texto=None, isAddress=False):
    """
    Genera las direcciones Bitcoin (comprimida y sin comprimir) y sus WIFs a partir de un texto.

    :param texto: Cadena de texto base para generar el hash SHA-256.
    :param isAddress: Si es True, se genera una dirección; si es False, se genera una clave privada.
    :return: Diccionario con las direcciones y WIFs.
    """

    if texto is None:
        return False  # Si texto es None, devolvemos False

    if isAddress:
        # Generar el hash SHA-256 del texto
        hex_generate = hashlib.sha256(texto.encode()).hexdigest()
    else:
        # Usar el texto tal cual si isAddress es False
        hex_generate = texto


    # Convertir Hex a WIF (comprimida y sin comprimir)
    pk_wif_sin_comprimir, pk_wif_comprimida = btcPrivatekeyHextoWIF(hex_generate)
    
    # PrivateKey HEX to Pubkey (comprimida y sin comprimir)
    pubkey_sin_comprimir, pubkey_comprimida = private_key_to_public_key(hex_generate)
    
    # PubKey to Address (comprimida y sin comprimir)
    address_sin_comprimir = pubkey_to_bitcoin_address(pubkey_sin_comprimir)
    address_comprimida = pubkey_to_bitcoin_address(pubkey_comprimida)
    
    # Devolver los resultados en un diccionario
    return {
        "hash_hex": hex_generate,
        "wif_sin_comprimir": pk_wif_sin_comprimir,
        "wif_comprimida": pk_wif_comprimida,
        "direccion_sin_comprimir": address_sin_comprimir,
        "direccion_comprimida": address_comprimida,
    }



# Función para procesar un bloque y sus transacciones
def procesar_bloque_y_transacciones(bloque_id):
    """
    Procesa un bloque, extrae las direcciones de las transacciones y obtiene sus balances.

    :param bloque_id: ID del bloque (número de bloque).
    :return: None
    """
    # Obtener información del bloque
    block_hash, tx_hashes, getmerkleroot = obtener_info_bloque(bloque_id)
    if block_hash is None:
        return

    # Inicializamos un diccionario para almacenar las direcciones y sus WIFs
    direcciones_wif = {}

    # Convertir merkleroot en direccion
    resultadoBMerklerootToAddress = generar_direcciones_y_wif(getmerkleroot, isAddress=False)

    if resultadoBMerklerootToAddress:
        # Asignamos solo el WIF correspondiente para cada dirección
        direcciones_wif[resultadoBMerklerootToAddress['direccion_sin_comprimir']] = resultadoBMerklerootToAddress['wif_sin_comprimir']
        direcciones_wif[resultadoBMerklerootToAddress['direccion_comprimida']] = resultadoBMerklerootToAddress['wif_comprimida']


    # Convertir el hash del bloque en direcciones y agregar los WIFs al diccionario
    resultadoBlockhashToAddress = generar_direcciones_y_wif(block_hash, isAddress=False)

    # Verificar si la respuesta no es False antes de agregar las direcciones
    if resultadoBlockhashToAddress:
        # Verificar que las direcciones comiencen con '1' antes de agregarlas
        if resultadoBlockhashToAddress['direccion_sin_comprimir'].startswith('1'):
            direcciones_wif[resultadoBlockhashToAddress['direccion_sin_comprimir']] = resultadoBlockhashToAddress['wif_sin_comprimir']
        if resultadoBlockhashToAddress['direccion_comprimida'].startswith('1'):
            direcciones_wif[resultadoBlockhashToAddress['direccion_comprimida']] = resultadoBlockhashToAddress['wif_comprimida']


    # Convertimos los hashes de las transacciones en direcciones y asignamos los WIFs
    for tx_hash in tx_hashes:
        resultadoTxToAddress = generar_direcciones_y_wif(tx_hash, isAddress=False)

        # Verificar si la respuesta no es False antes de agregar las direcciones
        if resultadoTxToAddress:
            # Verificar que las direcciones comiencen con '1' antes de agregarlas
            if resultadoTxToAddress['direccion_sin_comprimir'].startswith('1'):
                direcciones_wif[resultadoTxToAddress['direccion_sin_comprimir']] = resultadoTxToAddress['wif_sin_comprimir']
            if resultadoTxToAddress['direccion_comprimida'].startswith('1'):
                direcciones_wif[resultadoTxToAddress['direccion_comprimida']] = resultadoTxToAddress['wif_comprimida']


    # Obtenemos las direcciones de las transacciones y les asignamos los WIFs
    for i, tx_hash in enumerate(tx_hashes):
        # Mostrar el número de transacciones restantes por procesar
        #print(f"Procesando transacción {tx_hash}... ({i+1} de {len(tx_hashes)}) restantes.")

        tx_direcciones = get_transaction_addresses(tx_hash)
        for addr in tx_direcciones:

            # Solamente Convertir Direcciones que comienze con 1
            if addr and addr.startswith('1'):

                # Convertir la dirección y asignar solo el WIF correspondiente
                resultado = generar_direcciones_y_wif(addr, isAddress=True)

                if resultado:  # Verificamos que resultado no sea False
                    # Verificar que las direcciones comiencen con '1' antes de agregarlas
                    if resultado['direccion_sin_comprimir'].startswith('1'):
                        direcciones_wif[resultado['direccion_sin_comprimir']] = resultado['wif_sin_comprimir']

                        #print(f"[Sin Comprimir] Address: {resultado['direccion_sin_comprimir']} :: WIF: {resultado['wif_sin_comprimir']} ")

                    if resultado['direccion_comprimida'].startswith('1'):
                        direcciones_wif[resultado['direccion_comprimida']] = resultado['wif_comprimida']



    # Guardar todas las direcciones y WIFs en MongoDB de una vez
    guardar_datos_masivo(direcciones_wif)

    #time.sleep(1)


# Obtener el número del último bloque
latest_block_number = None  # Inicializamos con None para forzar la ejecución al inicio
new_block_number = None

while True:

    # Obtener el número más reciente del bloque
    new_block_number = get_latest_block_number()

    # Verificamos si el número del bloque ha cambiado o si es la primera vez
    if new_block_number != latest_block_number:
        latest_block_number = new_block_number  # Actualizamos el bloque procesado
        print(f"Nuevo bloque detectado: {new_block_number} | Procesando...")
        procesar_bloque_y_transacciones(new_block_number)


    # Esperar un tiempo antes de verificar el siguiente bloque (ajustar según sea necesario)
    time.sleep(15)  # Ajusta el tiempo de espera según lo necesites