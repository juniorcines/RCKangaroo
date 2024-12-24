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

import threading

console = Console()
console.clear()

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



def Home():

    binary_dir = os.path.join("./")
    miner_binary = os.path.join("RCKangaroo.exe")
    
    # 13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so

    # Puzzle 67 Buscar >> Buscar Por la PubKey, si se descubrio la Pubkey ejecutamos para obtener la clave y luego retiramos los fondos
    puzzleNumero = 66
    vanityAddressSearch = "13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so" # Direccion
    pubKeySearch = "024ee2be2d4e9f92d2f5a4a03058617dc45befe22938feed5b7a6b7282dd74cbdd"
    hexStartSearch = '10000000000000000' #Puzzle 66 Inicia desde: 10000000000000000

    console.print(f"[white]Starting miner >> {hexStartSearch.upper()}][/white]")

    process = subprocess.Popen(f"{miner_binary} -dp 14 -range {puzzleNumero} -start {hexStartSearch} -pubkey {pubKeySearch}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=binary_dir)

    buffer = b""
    accountPrivateHEX = None

    totalWalletFound = 0

    while True:

        # Verificar si el archivo RESULTS.txt existe
        if os.path.exists("RESULTS.txt"):
            with open("RESULTS.txt", "r") as file:
                # Tomar la primera línea del archivo y asignarla a accountPrivateHEX
                accountPrivateHEX = file.readline().strip()


        # Esperar 5 segundos antes de volver a verificar el archivo
        time.sleep(5)

        if accountPrivateHEX:

            totalWalletFound += 1

            balance = get_btc_balance(vanityAddressSearch)

            # Imprimir el panel con el texto y estilos especificados, incluyendo el color gris para el panel
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

            # Salir del While Ya que se encontro Wallet
            break


Home()