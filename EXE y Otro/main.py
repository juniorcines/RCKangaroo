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


# Importar private_key_to_public_key, pubkey_to_bitcoin_address, de bitcoin.py
from bitcoinx import private_key_to_public_key, pubkey_to_bitcoin_address, obtener_valor_hex_porcentaje, rangoInicialFinalHexEncontradoPorcentaje, get_hex_range_from_page_number

console = Console()
console.clear()

# Definir la zona horaria de La Paz (-4 GMT)
la_paz_tz = pytz.timezone("America/La_Paz")

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


def Home(porcentajeSearch=5):

     # Obtener el tiempo actual en La Paz
    current_time = datetime.now(la_paz_tz)
    
    # Formatear la hora en el formato deseado
    formatted_time = current_time.strftime("%d-%m-%Y %I:%M%p")

    binary_dir = os.path.join("./")
    miner_binary = os.path.join("RCKangaroo.exe")
    
    puzzleNumero = 135
    vanityAddressSearch = "13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so"
    pubKeySearch = "024ee2be2d4e9f92d2f5a4a03058617dc45befe22938feed5b7a6b7282dd74cbdd"
    hexStartSearch = obtener_valor_hex_porcentaje('4000000000000000000000000000000000', '7fffffffffffffffffffffffffffffffff', porcentajeSearch)

    console.print(f"[white]Starting miner >> {hexStartSearch.upper()} %{porcentajeSearch}] [{formatted_time}][/white]")

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


    # Incrementar porcentajeSearch en 5% y reiniciar si llega a 100%
    porcentajeSearch += 5
    if porcentajeSearch > 100:
        porcentajeSearch = 5

    # Llamar a Home nuevamente con el nuevo porcentaje
    Home(porcentajeSearch)



Home()