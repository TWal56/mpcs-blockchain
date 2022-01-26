# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from concurrent import futures
from collections import OrderedDict
import logging
import grpc
import jcoin_pb2
import jcoin_pb2_grpc
import datetime
import time
import hashlib
import json
import ast
import random
import threading
import socket


block_reward = 50000
KnownPeers = OrderedDict()
Blockchain = OrderedDict()
TxnMemoryPool = OrderedDict()

##########
# BLOCKCHAIN CLASSES
##########
# The Block's Blockhash is a hash of the current block's header.
# A block holds a hash of it's own Header information, and it's header
# holds a hash of the previous block's hash, and so on.


class Block:
    MagicNumber = 0xD9B4BEF9
    # max txns is 9 + coinbase = 10
    max_txns = 9
    
    def __init__(self, header, transx, height):
        self.height = height
        self.Blocksize = 0
        self.BlockHeader = header
        # You may wish to implement the Block's Transactions list
        # as a map or dictionary, where each key is the actual Transaction's TransactionHash
        self.Transactions = transx
        self.Transactions_forPrint = list(transx)
        self.TransactionCounter = len(self.Transactions)
        # Blockhash = TimeStamp + hashMerkleRoot + Bits + Nonce + previousHash (hash of the header)
        Blockhash_prep = str(self.BlockHeader.Timestamp) + str(self.BlockHeader.hashMerkleRoot) + \
                         str(self.BlockHeader.Bits) + str(self.BlockHeader.Nonce) + \
                         str(self.BlockHeader.hashPrevBlock)
        self.Blockhash = double_hash(Blockhash_prep)
        # create these on new Block addition to the chain:
        self.previousblockhash = None
        self.nextblockhash = None
        self.from_node = ''
    
    def reset_blockhash(self):
        Blockhash_prep = str(self.BlockHeader.Timestamp) + str(self.BlockHeader.hashMerkleRoot) + \
                         str(self.BlockHeader.Bits) + str(self.BlockHeader.Nonce) + \
                         str(self.BlockHeader.hashPrevBlock)
        self.Blockhash = double_hash(Blockhash_prep)
    
    def printBlock(self):
        block_toprint = {
            "hash": self.Blockhash,
            "confirmations": 0,
            "strippedsize": None,
            "size": self.Blocksize,
            "weight": None,
            "height": self.height,
            "version": 0,
            "versionHex": None,
            "merkleroot": self.BlockHeader.hashMerkleRoot,
            "tx": self.Transactions_forPrint,
            "time": None,
            "mediantime": None,
            "nonce": self.BlockHeader.Nonce,
            "bits": self.BlockHeader.Bits,
            "difficulty": None,
            "chainwork": None,
            "nTx": self.TransactionCounter,
            "previousblockhash": self.previousblockhash,
            "nextblockhash": self.nextblockhash,
            "from_node": self.from_node
        }
        
        print(json.dumps(block_toprint, indent=4))


class Header:
    
    def __init__(self, hashPrevBlock, txns):
        self.Version = 0
        self.hashPrevBlock = hashPrevBlock
        # need to access block's t-list!
        # first make simple list object of transaction hashes
        txns_for_merkle = list(txns.keys())
        print('pre-merkle txns=' + str(txns_for_merkle))
        self.hashMerkleRoot = merkle(txns_for_merkle)
        print('merkle_root=' + self.hashMerkleRoot)
        self.Timestamp = datetime.datetime.now()
        self.Bits = 0x207fffff
        self.Nonce = 0
    
    def gen_header_hash(self):
        to_hash = self.Timestamp.__str__() + self.hashMerkleRoot + str(self.Bits) + \
                  str(self.Nonce) + self.hashPrevBlock
        return double_hash(to_hash)


class Transaction:
    
    def __init__(self, ListOfInputs, ListOfOutputs):
        self.VersionNumber = 0
        self.ListOfInputs = ListOfInputs
        self.InCounter = len(self.ListOfInputs)
        self.ListOfOutputs = ListOfOutputs
        self.OutCounter = len(self.ListOfOutputs)
        # TransactionHash is a hash of the concatenated (serialized/stringified) fields of
        # VersionNumber, InCounter, ListOfInputs, OutCounter, and ListOfOutputs
        self.concat = str(self.VersionNumber) + str(self.InCounter) + str(self.ListOfInputs) + str(self.OutCounter) + \
                      str(self.ListOfOutputs)
        self.TransactionHash = double_hash(self.concat)
        self.is_coinbase = False
        self.from_node = ''
        # what is txid ? coinbase txid looks like same as hash value...
    
    def printTransaction(self):
        tx = {
            "txid": "",
            "hash": self.TransactionHash,
            "version": self.VersionNumber,
            "size": None,
            "vsize": None,
            "weight": None,
            "locktime": None,
            "vin": self.ListOfInputs,
            "vout": self.ListOfOutputs,
            "hex": None,
            "blockhash": "",
            "confirmations": 0,
            "time": None,
            "blocktime": None,
            "is_coinbase": self.is_coinbase,
            "from_node": self.from_node
        }
        
        print(json.dumps(tx, indent=4))
        return str(tx)


class TxInput:
    
    def __init__(self, prev_tx_id, prev_tx_vout_idx):
        # txid from previous tx:
        self.txid = prev_tx_id
        # index of output from previous tx:
        self.vout = prev_tx_vout_idx
        self.scriptSig = {}
        self.txinwitness = []
        self.sequence = None
        self.coinbase = None
    
    def vin_format(self):
        for_vin = {
            "txid": self.txid,
            "vout": self.vout,
            "scriptSig": self.scriptSig,
            "txinwitness": self.txinwitness,
            "sequence": self.sequence,
            "coinbase": str(self.coinbase)
        }
        return for_vin


class TxOutput:
    output_counter = 0
    
    def __init__(self, value):
        # value is denominated in 1/1000 Jennycoins
        self.value = value
        self.n = TxOutput.output_counter
        TxOutput.output_counter += 1
        self.scriptPubKey = {}
    
    def vout_format(self):
        for_vout = {
            "value": self.value,
            "n": self.n,
            "scriptPubKey": self.scriptPubKey,
        }
        return for_vout


##########
# BLOCKCHAIN FUNCTIONS
##########
# function to build a full transaction from selected inputs with specified outputs
def create_txn(inputs, outputs):
    # inputs should be list of tuples with (prev_tx_id, prev_vout_idx)
    List_Inputs = []
    for input_tuple in inputs:
        new_input = TxInput(input_tuple[0], input_tuple[1])
        List_Inputs.append(new_input.vin_format())
    
    # outputs should be list of values
    List_Outputs = []
    for output in outputs:
        new_output = TxOutput(output)
        List_Outputs.append(new_output.vout_format())
    
    # Reset output counter to 0 for each new transaction:
    TxOutput.output_counter = 0
    
    # validate that sum of inputs = sum of outputs?
    txn = Transaction(List_Inputs, List_Outputs)
    txn.from_node = socket.gethostbyname(socket.gethostname())
    return txn


# Function 1. There must be some means of asking your Blockchain for a given block by block height and
# by block hash.  It is up to you how to implement this.
def get_block_by_height(height):
    chain = list(Blockchain.items())
    block_toget = chain[height][1]
    block_toget.printBlock()
    return chain[height][1]


# Function 2. There must be some means of searching the Blockchain for a given Transaction by
# TransactionHash, which should return the Transaction being searched.
def get_txn_by_hash(trn_hash):
    for Block_obj in Blockchain.values():
        for txh in Block_obj.Transactions.keys():
            if txh==trn_hash:
                Block_obj.Transactions[txh].printTransaction()
                return Block_obj.Transactions[txh]


# Other helper functions:
def double_hash(to_hash):
    # encode string to bytes
    in_bytes = to_hash.encode('utf-8')
    
    # double hash the bytes
    hash1 = hashlib.sha256(in_bytes)
    hash2 = hashlib.sha256(hash1.digest())
    
    # hex it
    hash_out = hash2.hexdigest()
    
    # return hex string
    return hash_out


def hash_pair(txn1, txn2):
    # encode hex string to bytes
    txn1_bytes = bytearray.fromhex(txn1)
    txn2_bytes = bytearray.fromhex(txn2)
    
    # reverse bytes
    txn1_bytes.reverse()
    txn2_bytes.reverse()
    
    # concat the reversed bytestrings
    concat = txn1_bytes + txn2_bytes
    
    # double hash the concat
    concat_hash1 = hashlib.sha256(concat)
    concat_hash2 = hashlib.sha256(concat_hash1.digest())
    
    # double hashed concat to bytestring and reverse
    concat_hash_hex = concat_hash2.hexdigest()
    concat_hash_hex_bytes = bytearray.fromhex(concat_hash_hex)
    concat_hash_hex_bytes.reverse()
    
    # hex it
    hash_hex = concat_hash_hex_bytes.hex()
    
    # return hex string
    return hash_hex


def merkle(txns_list):
    if len(txns_list)==1:
        print('\nFINAL MERKLE ROOT:\n')
        return txns_list[0]
    else:
        if len(txns_list) % 2!=0:
            last_tx = txns_list[-1]
            txns_list.append(last_tx)
        txns_new = []
        while txns_list:
            tx_1 = txns_list.pop(0)
            tx_2 = txns_list.pop(0)
            hash_hex = hash_pair(tx_1, tx_2)
            txns_new.append(hash_hex)
        return merkle(txns_new)


def get_last_tx_from_last_block():
    chain = list(Blockchain.keys())
    block_hash = chain[-1]
    block = Blockchain[block_hash]
    txn_list = list(block.Transactions)
    last_txn_hash = txn_list[-1]
    return last_txn_hash


def get_last_tx_off_chain():
    return list(tx_dict)[-1]


def add_new_tx_to_txdict(out_val):
    if len(tx_dict) > 0:
        last_tx = get_last_tx_off_chain()
    else:
        last_tx = get_last_tx_from_last_block()
    ListInputs = [(last_tx, 0)]
    ListOutputs = [out_val]
    tx = create_txn(ListInputs, ListOutputs)
    tx_dict[tx.TransactionHash] = tx


def create_coinbase():
    cb_tx_prep = create_txn([(None, None)], [block_reward])
    cb_tx_prep.is_coinbase = True
    cb_tx_prep.ListOfInputs[0]['coinbase'] = 'placeholder_value'
    return cb_tx_prep


def create_new_block(txd):
    chain_list = list(Blockchain.keys())
    last_hash = chain_list[-1]
    header = Header(last_hash, txd)
    new_block = Block(header, txd, len(Blockchain))
    return new_block


# Create genesis block:
def create_genesis():
    ListOfInputs = []
    ListOfOutputs = []
    in1 = TxInput(None, None)
    out1 = TxOutput(100)
    ListOfInputs.append(in1.vin_format())
    ListOfOutputs.append(out1.vout_format())
    txGen = Transaction(ListOfInputs, ListOfOutputs)
    txGen.from_node = socket.gethostbyname(socket.gethostname())
    print('\nGENESIS BLOCK CREATED:\n')
    txGen.printTransaction()
    tx_dict = OrderedDict()
    tx_dict[txGen.TransactionHash] = txGen
    hashPrevBlock_gen = '0' * 64
    headerGen = Header(hashPrevBlock_gen, tx_dict)
    blockGen = Block(headerGen, tx_dict, 0)
    blockGen.previousblockhash = hashPrevBlock_gen
    Blockchain[blockGen.Blockhash] = blockGen
    print('\nBlockchain height now = ' + str(len(Blockchain) - 1) + '\n')


##########
# SETUP TXN MEM POOL AND MINING OPERATION
##########
# cryptocurrency name = Jennycoin
# 1000 Jennyoshis = 1 Jennycoin
# inputs should be list of tuples with (prev_tx_id, prev_vout_idx)
def create_txns_for_mem_pool():
    while True:
        to_hash = str(datetime.datetime.now())
        prev_tx_id = hashlib.sha256(to_hash.encode('utf-8')).hexdigest()
        prev_vout_idx = 0
        tx_value = random.randint(1, 100000)
        print('\nNEW MEM POOL TRANSACTION BEING CREATED:\n')
        # new_txn as Transaction object:
        new_txn = create_txn([(prev_tx_id, prev_vout_idx)], [tx_value])
        txn_string = new_txn.printTransaction()
        # use TransactionHash as key in TxnMemoryPool Ordered Dict...
        # with the Transaction object as the value
        TxnMemoryPool[new_txn.TransactionHash] = txn_string
        # loop over known peers and cast new transaction to them
        for peer_ip in KnownPeers.keys():
            cast_trans(peer_ip, txn_string)
            print('Just casted a newly created transaction created on this node from ' +
                  socket.gethostbyname(socket.gethostname()) + ' to ' + peer_ip)
        time.sleep(random.randint(2, 6))


# miner function
def mine_blocks():
    # collect txs:
    while True:
        j = 0
        tx_dict = OrderedDict()
        c_base = create_coinbase()
        print('\nNEW COINBASE TXN CREATED:\n')
        c_base.printTransaction()
        tx_dict[c_base.TransactionHash] = c_base
        while j < Block.max_txns:
            try:
                next_tx = TxnMemoryPool.popitem(last=False)
                print('next_tx result in mine_blocks():')
                print(str(next_tx))
            except IndexError:
                print('INDEX ERROR GETTING NEXT_TX DURING MINE BLOCKS OPERATION')
                time.sleep(4)
                continue
            except KeyError:
                print('KEY ERROR GETTING NEXT_TX DURING MINE BLOCKS OPERATION')
                time.sleep(4)
                continue
            print('\nNEW TXN GRABBED FROM MEM POOL:\n')
            # next_tx.printTransaction()
            tx_dict[next_tx[0]] = next_tx[1]
            j += 1
            time.sleep(4)
        
        # create new block, note max_txns limit; create header first
        new_block = create_new_block(tx_dict)
        # add hash of previous block
        prev_block_hash = list(Blockchain)[-1]
        new_block.previousblockhash = prev_block_hash
        
        # get actual coefficient and exponent from bits field...
        bits = hex(new_block.BlockHeader.Bits)
        coefficient = int(bits[4:], 16)
        exponent = int(bits[2:4], 16)
        target = coefficient * 2 ** (8 * (exponent - 3))
        
        # print target in hex:
        target_hex = hex(target)
        needed_zeroes = 64 - (len(target_hex) - 2)
        target_hex_fmt = target_hex[:2] + '0' * 8 + target_hex[2:]
        
        # start guessing...
        while int(new_block.Blockhash, 16) > target:
            new_block.BlockHeader.Nonce += 1
            new_block.reset_blockhash()
        
        # add new block to Blockchain, first add this block's hash to previous block
        last_block_hash = list(Blockchain)[-1]
        last_block = Blockchain[last_block_hash]
        last_block.nextblockhash = new_block.Blockhash
        new_block.from_node = socket.gethostbyname(socket.gethostname())
        Blockchain[new_block.Blockhash] = new_block
        print('\nNEW BLOCK CREATED:\n')
        new_block.printBlock()
        print('\nBlockchain height now = ' + str(len(Blockchain) - 1) + '\n')


# confirm node has registered with DNS_SEED
# then launch blockchain software and start listening...
# listen for handshakes from new peers, add to list of known peers, return list of all known peers to calling Node
# also listen for new transactions...and blocks...

##########
# LAUNCH A NEW NODE AND REGISTER WITH REGISTRAR SERVER
##########
def launch_node():
    launch_time = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    node_ip = socket.gethostbyname(socket.gethostname())
    channel = grpc.insecure_channel('172.17.0.2:50051')
    stub = jcoin_pb2_grpc.RegistrarStub(channel)
    response = stub.Register(jcoin_pb2.NewNode(nVersion='1', nTime=launch_time, addrMe=node_ip))
    print('\nJCoin registrar server says last node added = ' + response.lastNodeIp)
    if not response.lastNodeIp == 'NULL':
        cur_time = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        KnownPeers[response.lastNodeIp] = {'nTime': cur_time,
                                                      'nVersion': '1',
                                                      'bestHeight': 0}
    return response.lastNodeIp


##########
# HANDSHAKE OPERATIONS
##########
# Handshake server to process inbound shakes
class Handshake(jcoin_pb2_grpc.HandshakeServicer):

    # known_peers = OrderedDict()
    node_ip = socket.gethostbyname(socket.gethostname())

    def Shake(self, request, context):
        # use extend to add known peer IPs to handshake response
        if request.addrMe not in KnownPeers:
            KnownPeers[request.addrMe] = {'nTime': request.nTime,
                                                'nVersion': request.nVersion,
                                                'bestHeight': request.bestHeight}
        else:
            print('node ' + request.addrMe + ' is already known!')
        print('\nNew Inbound Shake from ' + request.addrMe + ' ...')
        print('\nKnown Peers now = ' + str(KnownPeers))
        return jcoin_pb2.ReceiverShake(knownPeers=KnownPeers)


# Handshake call outbound
def shake_hands(ip_add):
    current_time = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    node_ip = socket.gethostbyname(socket.gethostname())
    channel = grpc.insecure_channel(ip_add + ':58333')
    stub = jcoin_pb2_grpc.HandshakeStub(channel)
    # shake hands with any nodes not yet shaken with
    # add flag to track handshakes
    response = stub.Shake(jcoin_pb2.CallerShake(nVersion='1', nTime=current_time, addrMe=node_ip, bestHeight=0))
    return response.knownPeers


##########
# TXN OPERATIONS
##########
# Txn server to process inbound shakes
class TxnCast(jcoin_pb2_grpc.TxnCastServicer):
  
    def CastTrans(self, request, context):
        # need to make sure we are matching on TransactionHash !
        # turn Transaction string we get into Transaction object
        print('visualize inbound casted transaction:')
        print(request.txn)
        # TURN STRING request.txn into JSON object...
        txn_json = ast.literal_eval(request.txn)
        if txn_json['hash'] not in TxnMemoryPool:
            # add new transaction to this node's memory pool
            # PROBLEM IS THIS IS ORDERED DICT...
            TxnMemoryPool.update({txn_json['hash']: request.txn})
            print('\nNew Not Yet Seen Inbound Txn from ' + request.addrMe + ' ...')
            print('\nTxn MemPool now = ' + str(TxnMemoryPool))
            # then broadcast this new transaction to all this node's known peers
            for peer_ip in KnownPeers.keys():
                print('CHECK PEER_IP: THIS ITERATION PEER IP IS:')
                print(peer_ip)
                cast_trans(peer_ip, request.txn)
                print('Just casted a newly received transaction from ' +
                      socket.gethostbyname(socket.gethostname()) + ' to ' + peer_ip)
        else:
            print('txn ' + request.txn + ' is already known!')
        return jcoin_pb2.TxnReceived(txnConfirm='Txn Confirmed!')


# Txn call outbound
# adding hardcoded ip


def cast_trans(ip_add, txn_to_cast):
    current_time = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    node_ip = socket.gethostbyname(socket.gethostname())
    channel = grpc.insecure_channel(ip_add + ':58333')
    stub = jcoin_pb2_grpc.TxnCastStub(channel)
    response = stub.CastTrans(jcoin_pb2.NewTxn(txn=txn_to_cast, addrMe=node_ip))
    return response.txnConfirm


##########
# BLOCK OPERATIONS
##########
# Block server to process inbound shakes


# Block call outbound


##########
# GRPC SERVE FUNCTION
##########

def serve_jcoin_node(lastIp):
    # add dynamic bestHeight???
    if lastIp != "NULL" and lastIp not in KnownPeers:
        KnownPeers[lastIp] = {'nTime': str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")),
                                         'nVersion': '1',
                                         'bestHeight': 0}
    node_ip = socket.gethostbyname(socket.gethostname())
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    jcoin_pb2_grpc.add_HandshakeServicer_to_server(Handshake(), server)
    jcoin_pb2_grpc.add_TxnCastServicer_to_server(TxnCast(), server)
    server.add_insecure_port(socket.gethostbyname(socket.gethostname()) + ':58333')
    server.start()
    print('\nJCOIN CLIENT SERVER IS LIVE ON ' + node_ip + ':58333')
        
    # for now just pass simple strings...

    while len(KnownPeers) < 2:
        print(str(len(KnownPeers)))
        print('still has known peers < 2')
        time.sleep(5)
        continue
    
    tx_thread = threading.Thread(target=create_txns_for_mem_pool)
    mining_thread = threading.Thread(target=mine_blocks)
    tx_thread.start()
    mining_thread.start()
    
    server.wait_for_termination()


##########
# RUN MINING OPERATION
##########
# how do we deal with genesis block on the chain?
# create_genesis()


##########
# RUN GRPC SERVER NODE
##########

if __name__ == '__main__':
    logging.basicConfig()
    node_ip = socket.gethostbyname(socket.gethostname())
    lastNodeIp = launch_node()
    if lastNodeIp != "NULL":
        print('\nlastNodeIp not NULL')
        peers = shake_hands(lastNodeIp)
        for peer in peers:
            # add dynamic bestHeight???
            if peer not in KnownPeers and peer != node_ip:
                print('\nAdding new peer to this node: ' + str(peer))
                KnownPeers[peer] = {'nTime': str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")),
                                               'nVersion': '1',
                                               'bestHeight': 0}
                print('\nFor Loop--All known peers currently on this node = ' + str(list(KnownPeers)))
                shake_hands(peer)
        print('\nAll known peers currently on this node = ' + str(list(KnownPeers)))
    else:
        print('\nlastNodeIp IS NULL')
    serve_jcoin_node(lastNodeIp)


###
