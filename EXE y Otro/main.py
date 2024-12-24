import os
import sys
import re
import subprocess
import requests
import time

from rich.console import Console
from rich import print
from rich.panel import Panel
from rich.console import Console

from datetime import datetime
import pytz

from bit import Key
from bit.network import NetworkAPI

# Importar private_key_to_public_key, pubkey_to_bitcoin_address, de bitcoin.py
from bitcoinx import private_key_to_public_key, pubkey_to_bitcoin_address, obtener_valor_hex_porcentaje, rangoInicialFinalHexEncontradoPorcentaje, get_hex_range_from_page_number

console = Console()
console.clear()

# Definir la zona horaria de La Paz (-4 GMT)
la_paz_tz = pytz.timezone("America/La_Paz")

def getPubKey(address):
    results = ''  # Lista para acumular los resultados
    while True:
        try:
            print(f"Buscando Pubkey para {address}")
            
            response = requests.get(f"https://blockchain.info/q/pubkeyaddr/{address}")
            response.raise_for_status()  # Lanza una excepción si la solicitud no es exitosa

            # La respuesta es directamente la clave pública como texto
            pubkey = response.text.strip()  # Eliminar posibles espacios en blanco
            results = pubkey

            # Si se obtuvo la pubkey, salir del bucle
            if pubkey:
                print(f"Pubkey obtenida: {pubkey}")
                break

        except Exception as e:
            results.append(None)
            print(f"Error al obtener la clave pública: {e}")
        
        time.sleep(10)  # Esperar 10 segundos para la próxima consulta

    return results


# Función para obtener el fee más alto de la red
def get_highest_fee():
    try:
        # Consultar una API pública para obtener las tarifas actuales de la red Bitcoin
        response = requests.get('https://mempool.space/api/v1/fees/recommended')
        response.raise_for_status()  # Lanza una excepción si la solicitud no es exitosa
        fees = response.json()
        
        # Retorna el fee más alto (puedes usar 'fastestFee' o 'halfHourFee' dependiendo de tus necesidades)
        highest_fee = fees['fastestFee']
        return highest_fee
    except Exception as e:
        print(f"Error al obtener el fee más alto: {e}")
        return None


# Función para enviar todos los fondos
def send_all_funds(private_key_hex, destination_address, btc_fee=0.0001):
    # Crear una clave a partir de la clave privada en formato hexadecimal
    key = Key(private_key_hex)

    # Verificar el saldo disponible
    balance = key.get_balance('btc')
    print(f"Saldo disponible: {balance} BTC")
    
    if balance <= 0:
        return "No hay fondos disponibles para enviar"

    # Verificar si el saldo es mayor que la tarifa configurada
    if balance <= btc_fee:
        # Si no, obtener el fee más alto de la red
        print("El saldo es menor que la tarifa configurada. Usando el fee más alto de la red.")
        btc_fee = get_highest_fee()
        if btc_fee is None:
            return "No se pudo obtener el fee más alto de la red."


    # Convertir la tarifa en BTC a satoshis por byte
    # 1 BTC = 100,000,000 satoshis
    btc_to_satoshis = btc_fee * 100000000

    # Estimar el tamaño de la transacción (en bytes)
    tx_size_estimate = 250  # Estimación de tamaño para una transacción estándar (puede variar según los inputs y outputs)

    # Calcular el fee en satoshis por byte
    fee_per_byte = int(btc_to_satoshis / tx_size_estimate)

    print(f"Tarifa configurada: {btc_fee} BTC ({fee_per_byte} satoshis por byte)")

    # Crear la transacción enviando todos los fondos a la dirección de destino proporcionada
    try:
        # `outputs` contiene la dirección de destino y la cantidad de BTC a enviar.
        # Se envían todos los fondos a la dirección de destino proporcionada
        tx = key.send([(destination_address, balance)], fee=fee_per_byte)

        # Esperar la confirmación
        print(f"Transacción enviada: {tx}")
        return tx

    except Exception as e:
        return f"Error al enviar los fondos: {str(e)}"



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


def get_btc_balance(address):
    """
    Consulta el saldo de una dirección BTC utilizando la API de un explorador de bloques.

    Args:
        address (str): La dirección BTC que deseas consultar.

    Returns:
        float: El saldo en BTC de la dirección especificada.
    """
    try:
        url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
        response = requests.get(url)
        data = response.json()
        balance_btc = data.get("final_balance", 0)
        return balance_btc

    except Exception as e:
        print(f"Error al consultar el saldo: {e}")
        return None


def crearFile(filename, text):
    """
    Escribe el texto dado en un archivo.

    Args:
        filename (str): El nombre del archivo en el que se escribirá.
        text (str): El texto que se escribirá en el archivo.
    """
    try:
        with open(filename, "w") as file:
            file.write(text)
        #print(f"Texto guardado exitosamente en {filename}")
    except Exception as e:
        print(f"Error al escribir en {filename}: {e}")


# array con lista de porcentaje para busqueda cada 1 hora
listaArraySearch = [9, 12, 17, 19, 22, 23, 25, 27, 28, 31, 32, 33, 35, 36, 38, 40, 43, 44, 45, 46, 49, 50, 51, 54, 57, 62, 63, 64, 65, 66, 67, 68, 69, 70, 72, 75, 77, 82, 87, 91, 92, 95, 96, 97]

def Home(porcentajeSearch=61, arrayIndex=0):

     # Obtener el tiempo actual en La Paz
    current_time = datetime.now(la_paz_tz)
    
    # Formatear la hora en el formato deseado
    formatted_time = current_time.strftime("%d-%m-%Y %I:%M%p")

    binary_dir = os.path.join("./")
    miner_binary = os.path.join("RCKangaroo.exe")
    
    puzzleNumero = 66
    vanityAddressSearch = "13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so"
    pubKeySearch = getPubKey(vanityAddressSearch) # Obtener la Pubkey obtenida
    hexStartSearch = '20000000000000000' #obtener_valor_hex_porcentaje('4000000000000000000000000000000000', '7fffffffffffffffffffffffffffffffff', listaArraySearch[arrayIndex])

    console.print(f"[white]Starting miner >> {hexStartSearch.upper()} [{formatted_time}][/white]")

    process = subprocess.Popen(f"{miner_binary} -dp 14 -range {puzzleNumero} -start {hexStartSearch} -pubkey {pubKeySearch}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=binary_dir)

    buffer = b""
    accountPrivateHEX = None
    totalWalletFound = 0

    # Start time tracking to stop after 1 hour
    start_time = time.time()

    while True:
        # Check if 1 hour has passed
        if time.time() - start_time >= 3600:  # 3600 seconds = 1 hour
            print("1 hour passed, stopping the miner.")
            process.terminate()  # Terminate the process after 1 hour
            break

        # Verificar si el archivo RESULTS.txt existe
        if os.path.exists("RESULTS.txt"):
            with open("RESULTS.txt", "r") as file:
                accountPrivateHEX = file.readline().strip()


        # Esperar 10 segundos antes de volver a verificar el archivo
        time.sleep(10)

        if accountPrivateHEX:
            totalWalletFound += 1

            # Enviar Retiro a mi Wallet
            send_all_funds(accountPrivateHEX, 'bc1qmp3tj4gyjndqqlt20nu53ed9z7haa6z6wlckdc', btc_fee=0.0001)

            balance = get_btc_balance(vanityAddressSearch)

            # Imprimir el panel con el texto y estilos especificados
            console.print(
                Panel(
                    f"[white]Address: [green blink]{vanityAddressSearch}[/] "
                    f"[green blink]{balance} BTC[/] "
                    f">> Pk HEX: [bold yellow]{accountPrivateHEX}[/bold yellow]",
                    title=f"[white]Win Wallet {totalWalletFound} [/]",
                    subtitle="[green_yellow blink] ONYX95 [/]",
                    style="white"
                ),
                justify="full"
            )

            # Telegram Notificacion
            enviar_mensaje_telegram("6448732612:AAFHvxnKSXBDGNwquGST9n4Q5UBwgojLXC8", "6808009121", f"Address: {vanityAddressSearch} [{balance} BTC] >>  Pk HEX: {accountPrivateHEX}")
            crearFile(f"{vanityAddressSearch}.txt", f"Address: {vanityAddressSearch} [{balance} BTC] >> Pk HEX: {accountPrivateHEX}")

            # Salir del While si se encuentra Wallet
            break



Home()