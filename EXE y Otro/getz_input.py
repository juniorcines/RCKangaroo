# -*- coding: utf-8 -*-
"""

@author: iceland
"""
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import sys
import hashlib
import argparse
import json
from cloudscraper import create_scraper  # Importa create_scraper desde cloudscraper

#==============================================================================

def get_rs(sig):
    rlen = int(sig[2:4], 16)
    r = sig[4:4+rlen*2]
#    slen = int(sig[6+rlen*2:8+rlen*2], 16)
    s = sig[8+rlen*2:]
    return r, s
    
def split_sig_pieces(script):
    sigLen = int(script[2:4], 16)
    sig = script[2+2:2+sigLen*2]
    r, s = get_rs(sig[4:])
    pubLen = int(script[4+sigLen*2:4+sigLen*2+2], 16)
    pub = script[4+sigLen*2+2:]
    assert(len(pub) == pubLen*2)
    return r, s, pub


# Returns list of this list [first, sig, pub, rest] for each input
def parseTx(txn):
    if len(txn) <130:
        return {"error": "[WARNING] rawtx most likely incorrect. Please check.."}
        
    inp_list = []
    ver = txn[:8]
    if txn[8:12] == '0001':
        return {"error": "UnSupported Tx Input. Presence of Witness Data"}

    inp_nu = int(txn[8:10], 16)
    
    first = txn[0:10]
    cur = 10
    for m in range(inp_nu):
        prv_out = txn[cur:cur+64]
        var0 = txn[cur+64:cur+64+8]
        cur = cur+64+8
        scriptLen = int(txn[cur:cur+2], 16)
        script = txn[cur:2+cur+2*scriptLen] #8b included
        r, s, pub = split_sig_pieces(script)
        seq = txn[2+cur+2*scriptLen:10+cur+2*scriptLen]
        inp_list.append([prv_out, var0, r, s, pub, seq])
        cur = 10+cur+2*scriptLen
    rest = txn[cur:]
    return [first, inp_list, rest]


# =============================================================================

def getSignableTxn(parsed):
    res = []
    first, inp_list, rest = parsed
    tot = len(inp_list)
    for one in range(tot):
        e = first
        for i in range(tot):
            e += inp_list[i][0] # prev_txid
            e += inp_list[i][1] # var0
            if one == i: 
                e += '1976a914' + HASH160(inp_list[one][4]) + '88ac'
            else:
                e += '00'
            e += inp_list[i][5] # seq
        e += rest + "01000000"
        z = hashlib.sha256(hashlib.sha256(bytes.fromhex(e)).digest()).hexdigest()
        res.append([inp_list[one][2], inp_list[one][3], z, inp_list[one][4], e])
    return res
#==============================================================================
def HASH160(pubk_hex):
    return hashlib.new('ripemd160', hashlib.sha256(bytes.fromhex(pubk_hex)).digest() ).hexdigest()
#==============================================================================

#==============================================================================

# Nueva función para obtener el raw transaction desde Bitcoin Core RPC
def get_rawtx_from_rpc(txid):
    try:
        # Configura la conexión con el cliente de Bitcoin Core a través de RPC
        rpc_user = "anigametv"       # Reemplaza con tu usuario RPC
        rpc_password = "gotech2020"   # Reemplaza con tu contraseña RPC
        rpc_host = "127.0.0.1"  # Cambia esto si tu cliente de Bitcoin Core está en un host remoto
        rpc_port = 8332        # Cambia esto si has configurado un puerto diferente para RPC

        # Crea una instancia de AuthServiceProxy para interactuar con Bitcoin Core a través de RPC
        rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")

        # Llama al método getrawtransaction de Bitcoin Core a través de RPC
        raw_tx = rpc_connection.getrawtransaction(txid)
        return raw_tx

    except JSONRPCException as e:
        print(json.dumps({"error": f"Error al obtener la transacción cruda (raw tx) para txid: {txid}"}))
