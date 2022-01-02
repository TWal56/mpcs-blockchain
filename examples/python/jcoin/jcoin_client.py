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
import socket
import threading


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
        Handshake.known_peers[response.lastNodeIp] = {'nTime': cur_time,
                                                      'nVersion': '1',
                                                      'bestHeight': 0}
    return response.lastNodeIp


##########
# HANDSHAKE OPERATIONS
##########
# Handshake server to process inbound shakes

class Handshake(jcoin_pb2_grpc.HandshakeServicer):

    known_peers = OrderedDict()
    node_ip = socket.gethostbyname(socket.gethostname())

    def Shake(self, request, context):
        # use extend to add known peer IPs to handshake response
        if request.addrMe not in self.known_peers:
            self.known_peers[request.addrMe] = {'nTime': request.nTime,
                                                'nVersion': request.nVersion,
                                                'bestHeight': request.bestHeight}
        else:
            print('node ' + request.addrMe + ' is already known!')
        print('\nNew Inbound Shake from ' + request.addrMe + ' ...')
        print('\nKnown Peers now = ' + str(self.known_peers))
        return jcoin_pb2.ReceiverShake(knownPeers=self.known_peers)


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
    # for now just pass simple strings...
    txn_mempool = {}
  
    def CastTrans(self, request, context):
        if request.txn not in self.txn_mempool:
            txn_count = str(len(self.txn_mempool) + 1)
            self.txn_mempool[txn_count] = {'txn': request.txn, 'from': request.addrMe}
        else:
            print('txn ' + request.txn + ' is already known!')
        print('\nNew Inbound Txn from ' + request.addrMe + ' ...')
        print('\nTxn MemPool now = ' + str(self.txn_mempool))
        return jcoin_pb2.TxnReceived(txnConfirm='Txn Confirmed!')


# Txn call outbound
# adding hardcoded ip
def cast_trans(ip_add):
    current_time = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    node_ip = socket.gethostbyname(socket.gethostname())
    channel = grpc.insecure_channel(ip_add + ':58333')
    stub = jcoin_pb2_grpc.TxnCastStub(channel)
    response = stub.CastTrans(jcoin_pb2.NewTxn(txn='test txn 1', addrMe=node_ip))
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
    if lastIp != "NULL" and lastIp not in Handshake.known_peers:
        Handshake.known_peers[lastIp] = {'nTime': str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")),
                                         'nVersion': '1',
                                         'bestHeight': 0}
    node_ip = socket.gethostbyname(socket.gethostname())
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    jcoin_pb2_grpc.add_HandshakeServicer_to_server(Handshake(), server)
    jcoin_pb2_grpc.add_TxnCastServicer_to_server(TxnCast(), server)
    server.add_insecure_port(socket.gethostbyname(socket.gethostname()) + ':58333')
    server.start()
    print('\nJCOIN CLIENT SERVER IS LIVE ON ' + node_ip + ':58333')
    if node_ip == '172.17.0.4':
        txnConfirm = cast_trans('172.17.0.3')
        print('txn test cast response = ' + txnConfirm)
    server.wait_for_termination()


##########
# RUN PROGRAM
##########

if __name__ == '__main__':
    logging.basicConfig()
    node_ip = socket.gethostbyname(socket.gethostname())
    lastNodeIp = launch_node()
    if lastNodeIp != "NULL":
        print('\nlastNodeIp not NULL')
        peers = shake_hands(lastNodeIp)
        for peer in peers:
            # peers_list.append(peer)
            # add dynamic bestHeight???
            if peer not in Handshake.known_peers and peer != node_ip:
                print('\nAdding new peer to this node: ' + str(peer))
                Handshake.known_peers[peer] = {'nTime': str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")),
                                               'nVersion': '1',
                                               'bestHeight': 0}
                print('\nFor Loop--All known peers currently on this node = ' + str(list(Handshake.known_peers)))
                shake_hands(peer)
        print('\nAll known peers currently on this node = ' + str(list(Handshake.known_peers)))
    else:
        print('\nlastNodeIp IS NULL')
    serve_jcoin_node(lastNodeIp)


###
