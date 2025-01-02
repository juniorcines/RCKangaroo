import hashlib
import requests
from bitcoinx import (
    private_key_to_public_key,
    pubkey_to_bitcoin_address,
    btcPrivatekeyHextoWIF,
)

# Función para obtener el balance de una dirección usando la API de Blockchain.info
def obtener_balance_direccion(direcciones):
    """
    Obtiene el balance de varias direcciones usando la API de Blockchain.info.

    :param direcciones: Lista de direcciones Bitcoin.
    :return: Diccionario con los balances de las direcciones.
    """
    url = f"https://blockchain.info/balance?active={'|'.join(direcciones)}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()  # Devuelve el JSON con los balances
    else:
        return {"error": "No se pudo obtener el balance"}

# PD: solo usar hash256 solo si es una direccion, y sin hash256 seria txid y hash del bloque
def generar_direcciones_y_wif(texto, isAddress=False):
    """
    Genera las direcciones Bitcoin (comprimida y sin comprimir) y sus WIFs a partir de un texto.

    :param texto: Cadena de texto base para generar el hash SHA-256.
    :return: Diccionario con las direcciones, WIFs y balances de las direcciones.
    """

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
    
    # Obtener los balances de las direcciones usando la API
    balances = obtener_balance_direccion([address_sin_comprimir, address_comprimida])

    # Devolver los resultados en un diccionario
    return {
        "hash_hex": hex_generate,
        "wif_sin_comprimir": pk_wif_sin_comprimir,
        "wif_comprimida": pk_wif_comprimida,
        "direccion_sin_comprimir": address_sin_comprimir,
        "direccion_comprimida": address_comprimida,
        "balances": balances,
    }

# Ejemplo de uso
texto_base = "00000000000000000000de59e73bcb5cafd77042243ca610620d26241a0fb986"
resultado = generar_direcciones_y_wif(texto_base)

# Mostrar los resultados
print(f"Hex: {resultado['hash_hex']}")
print(f"Dirección sin comprimir: {resultado['direccion_sin_comprimir']} (WIF: {resultado['wif_sin_comprimir']}) [{resultado['balances'].get(resultado['direccion_sin_comprimir'], {}).get('final_balance', 0)} BTC]")
print(f"Dirección comprimida: {resultado['direccion_comprimida']} (WIF: {resultado['wif_comprimida']}) [{resultado['balances'].get(resultado['direccion_comprimida'], {}).get('final_balance', 0)} BTC]")