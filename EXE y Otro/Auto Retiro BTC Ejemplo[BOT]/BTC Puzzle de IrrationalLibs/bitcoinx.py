import ecdsa
import hashlib
import base58
import numpy as np
from decimal import Decimal, getcontext
from bit import Key
from bitcoin import encode_privkey, privkey_to_address


#PrivateKeyWIF a Address
def pkWifToAddress(pkWIF):
    try:
        # Intenta convertir la clave privada WIF a una dirección de Bitcoin
        address = privkey_to_address(pkWIF)

        address_lower = address

        return address_lower
    except Exception as e:
        # Si ocurre un error, devuelve False
        return False



#Function para privatekey hex a PrivateKey WIF
def btcPrivatekeyHextoWIF(pkHex):  

    # Codifica la clave privada sin comprimir en formato WIF
    private_key_wif_uncompressed = encode_privkey(bytes.fromhex(pkHex), 'wif')

    # Codifica la clave privada comprimida en formato WIF
    private_key_wif_compressed = encode_privkey(bytes.fromhex(pkHex), 'wif_compressed')

    btcWIFData = [private_key_wif_uncompressed, private_key_wif_compressed]
    return btcWIFData


# Obtener Obtener HEX Por el numero de pagina
def get_hex_range_from_page_number(page_number, keys_per_page):
    base_page = int(page_number) - 1
    first_seed = base_page * keys_per_page

    start_hex = hex(first_seed)[2:]

    return start_hex


# Private Key HEX a Pubkey
def private_key_to_public_key(private_key_hex):
    try:
        # Decodificar la clave privada hexadecimal
        private_key = bytes.fromhex(private_key_hex)
        # Crear un objeto de clave privada utilizando la curva secp256k1
        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
        # Derivar la clave pública
        public_key = sk.get_verifying_key()
        # Obtener la clave pública en formato sin comprimir (04 + coordenada x + coordenada y)
        public_key_uncompressed = b'\x04' + public_key.to_string()
        # Obtener la clave pública en formato comprimido
        if public_key.pubkey.point.y() % 2 == 0:
            # Si la coordenada y es par, usar el prefijo 02
            public_key_compressed = b'\x02' + public_key.pubkey.point.x().to_bytes(32, byteorder="big")
        else:
            # Si la coordenada y es impar, usar el prefijo 03
            public_key_compressed = b'\x03' + public_key.pubkey.point.x().to_bytes(32, byteorder="big")
        # Obtener la clave pública en formato hexadecimal y en mayúsculas
        public_key_hex_uncompressed = public_key_uncompressed.hex().upper()
        public_key_hex_compressed = public_key_compressed.hex().upper()
        return public_key_hex_uncompressed, public_key_hex_compressed
        
    except Exception as e:
        print("Error al convertir la clave privada en clave pública:", e)
        return None, None


# Pubkey a Direccion Bitcoin
def pubkey_to_bitcoin_address(pubkey_hex):
    try:
        # Decodificar la clave pública hexadecimal
        public_key = bytes.fromhex(pubkey_hex)

        # Verificar si la clave pública es comprimida o sin comprimir
        if public_key[0] == 0x04:  # Sin comprimir
            # Calcular el hash SHA256 de la clave pública
            sha256_hash = hashlib.sha256(public_key).digest()
            # Calcular el hash RIPEMD160 del hash SHA256
            ripemd160_hash_uncompressed = hashlib.new('ripemd160', sha256_hash).digest()
            # Agregar el byte de versión (0x00 para direcciones sin comprimir)
            version_byte = b'\x00'
            # Calcular el hash doble SHA256 del hash RIPEMD160 junto con el byte de versión
            checksum_uncompressed = hashlib.sha256(hashlib.sha256(version_byte + ripemd160_hash_uncompressed).digest()).digest()[:4]
            # Agregar los bytes de versión y el hash RIPEMD160 al inicio para formar el payload final (sin comprimir)
            payload_uncompressed = version_byte + ripemd160_hash_uncompressed + checksum_uncompressed
            # Codificar el payload final en formato Base58 para obtener la dirección Bitcoin (sin comprimir)
            bitcoin_address_uncompressed = base58.b58encode(payload_uncompressed).decode()
            return bitcoin_address_uncompressed

        elif public_key[0] in (0x02, 0x03):  # Comprimida
            # Calcular el hash SHA256 de la clave pública
            sha256_hash = hashlib.sha256(public_key).digest()
            # Calcular el hash RIPEMD160 del hash SHA256
            ripemd160_hash_compressed = hashlib.new('ripemd160', sha256_hash).digest()
            # Agregar el byte de versión (0x00 para direcciones sin comprimir)
            version_byte = b'\x00'
            # Calcular el hash doble SHA256 del hash RIPEMD160 junto con el byte de versión
            checksum_compressed = hashlib.sha256(hashlib.sha256(version_byte + ripemd160_hash_compressed).digest()).digest()[:4]
            # Agregar los bytes de versión y el hash RIPEMD160 al inicio para formar el payload final (comprimido)
            payload_compressed = version_byte + ripemd160_hash_compressed + checksum_compressed
            # Codificar el payload final en formato Base58 para obtener la dirección Bitcoin (comprimida)
            bitcoin_address_compressed = base58.b58encode(payload_compressed).decode()
            return bitcoin_address_compressed  # No se proporciona dirección sin comprimir

        else:
            raise ValueError("Clave pública no válida")

    except Exception as e:
        print("Error al convertir la clave pública en direcciones Bitcoin:", e)
        return None



# Obtener el Valor HEX Al Indicar Porcentaje, Rango HEX Inicial, HEX Final
def obtener_valor_hex_porcentaje(hex_inicial, hex_final, porcentaje):
    # Convertir los valores hexadecimales iniciales y finales a enteros
    valor_inicial = int(hex_inicial, 16)
    valor_final = int(hex_final, 16)
    
    # Calcular la diferencia entre los valores iniciales y finales
    diferencia = valor_final - valor_inicial
    
    # Calcular el valor entero correspondiente al porcentaje
    valor_porcentaje = valor_inicial + int(diferencia * porcentaje / 100)
    
    # Convertir el valor entero generado a hexadecimal y llenar con ceros a la izquierda si es necesario
    valor_hex_porcentaje = hex(valor_porcentaje)[2:] #.zfill(64)
    
    return valor_hex_porcentaje  # Devolver el valor hexadecimal en mayúsculas



# Rango  HEX INICIAL: HEX FINAL, HEX Encontrado y obtener el Porcentaje en que se encontro
def rangoInicialFinalHexEncontradoPorcentaje(initial_hex, final_hex, found_hex, precision=35):
    from decimal import Decimal, getcontext
    
    getcontext().prec = precision  # Establecer la precisión
    
    # Convertir de hexadecimal a Decimal
    initial_value = Decimal(int(initial_hex, 16))
    final_value = Decimal(int(final_hex, 16))
    found_value = Decimal(int(found_hex, 16))
    
    # Calcular la diferencia
    range_difference = final_value - initial_value
    found_difference = found_value - initial_value
    
    # Calcular el porcentaje
    percentage = (found_difference / range_difference) * Decimal(100)
    
    # Formatear con muchos decimales (por ejemplo, 90 decimales)
    return f"{percentage:.90f}"