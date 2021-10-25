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

import logging

import grpc
import jcoin_pb2
import jcoin_pb2_grpc
import datetime
import socket
from collections import OrderedDict


# confirm node has registered with DNS_SEED
# then launch blockchain software and start listening...
# listen for handshakes from new peers, add to list of known peers, return list of all known peers to calling Node
# also listen for new transactions!?

##########
# Launch a new node and register with registrar server
##########

def launch_node():
    launch_time = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    node_ip = socket.gethostbyname(socket.gethostname())
    channel = grpc.insecure_channel('172.17.0.2:50051')
    stub = jcoin_pb2_grpc.RegistrarStub(channel)
    response = stub.Register(jcoin_pb2.NewNode(nVersion='1', nTime=launch_time, addrMe=node_ip))
    print("JCoin registrar server says last node added = " + response.lastNodeIp)
    return response.lastNodeIp


##########
# Handshake server
##########

class Handshake(jcoin_pb2_grpc.HandshakeServicer):

    known_peers = OrderedDict()
    node_ip = socket.gethostbyname(socket.gethostname())

    def Shake(self, request, context):
        # use extend to add multiple known peer IPs to handshake response
        if request.addrMe not in self.known_peers:
            self.known_peers[request.addrMe] = {'nTime': request.nTime,
                                                'nVersion': request.nVersion,
                                                'bestHeight': request.bestHeight}
        else:
            print('node ' + request.addrMe + ' is already known!')
        print('Known Peers = ' + str(self.known_peers))
        r_shake_peers = jcoin_pb2.ReceiverShake().knownPeers
        r_shake_peers.extend(list(self.known_peers))
        print('Known Peers EXTENDED for RPC response = ' + str(r_shake_peers))
        return jcoin_pb2.ReceiverShake(knownPeers=r_shake_peers)


def serve_handshake(lastIp):
    # add dynamic bestHeight???
    if lastIp != "NULL" and lastIp not in Handshake.known_peers:
        Handshake.known_peers[lastIp] = {'nTime': str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")),
                                         'nVersion': '1',
                                         'bestHeight': 0}
    node_ip = socket.gethostbyname(socket.gethostname())
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    jcoin_pb2_grpc.add_HandshakeServicer_to_server(Handshake(), server)
    server.add_insecure_port(socket.gethostbyname(socket.gethostname()) + ':58333')
    server.start()
    print('Handshake Server is live on ' + node_ip + ':58333')
    server.wait_for_termination()


##########
# Handshake call
##########

def shake_hands(lastIp):
    current_time = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    node_ip = socket.gethostbyname(socket.gethostname())
    channel = grpc.insecure_channel(lastIp + ':58333')
    stub = jcoin_pb2_grpc.HandshakeStub(channel)
    # add dynamic bestHeight
    # shake hands with any nodes not yet shaken with
    # add flag to track handshakes
    response = stub.Shake(jcoin_pb2.CallerShake(nVersion='1', nTime=current_time, addrMe=node_ip, bestHeight=0))
    peers_list = []
    for peer in response.knownPeers:
        peers_list.append(peer)
        # add dynamic bestHeight???
        if peer not in Handshake.known_peers and peer != node_ip:
            Handshake.known_peers[peer] = {'nTime': str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")),
                                           'nVersion': '1',
                                           'bestHeight': 0}
    print("JCoin server says known peers from called Node = " + str(peers_list))


##########
# Run program
##########

if __name__ == '__main__':
    logging.basicConfig()
    lastNodeIp = launch_node()
    if lastNodeIp != "NULL":
        print('lastNodeIp not NULL')
        shake_hands(lastNodeIp)
    else:
        print('lastNodeIp IS NULL')
    serve_handshake(lastNodeIp)


###
