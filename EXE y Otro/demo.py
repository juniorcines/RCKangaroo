import hashlib

# Importar private_key_to_public_key, pubkey_to_bitcoin_address, de bitcoin.py
from bitcoinx import private_key_to_public_key, pubkey_to_bitcoin_address, obtener_valor_hex_porcentaje, rangoInicialFinalHexEncontradoPorcentaje, get_hex_range_from_page_number, pkWifToAddress, btcPrivatekeyHextoWIF

# Cadena a hashear
input_string = "bc1qnr27kuxdju6yqfqjnayvn0f7eej3yyj5ylvzlz"

# Calcular SHA-256 (hex private key)
hash_result = hashlib.sha256(input_string.encode()).hexdigest()

#Convertir Hex a WIF
pkWifComprimida = btcPrivatekeyHextoWIF(hash_result)[1] # Comprimida
pkWIFSinComprimir = btcPrivatekeyHextoWIF(hash_result)[0] # Sin Comprimir

# PrivateKey HEX to Pubkey
hexToPubkeySinComprimir, hextoPubKeyComprida = private_key_to_public_key(hash_result)

# PubKey to Address
address = pubkey_to_bitcoin_address(hexToPubkeySinComprimir)

# Mostrar el resultado
print(f"{address} :: PrivateKey HEX: {hash_result} :: PrivateKey WIF Comprimida: {pkWifComprimida} :: PrivateKey WIF Sin Comprimir: {pkWIFSinComprimir}")