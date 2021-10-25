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

from concurrent import futures
import logging

import grpc
import jcoin_pb2
import jcoin_pb2_grpc
from collections import OrderedDict
import socket


class Registrar(jcoin_pb2_grpc.RegistrarServicer):

    reg_dict = OrderedDict()

    def Register(self, request, context):
        try:
            last_joined_ip = list(self.reg_dict)[-1]
            self.reg_dict[request.addrMe] = {'nTime': request.nTime, 'nVersion': request.nVersion}
            print(self.reg_dict)
            return jcoin_pb2.LastNode(lastNodeIp=last_joined_ip)
        except IndexError:
            self.reg_dict[request.addrMe] = {'nTime': request.nTime, 'nVersion': request.nVersion}
            print(self.reg_dict)
            return jcoin_pb2.LastNode(lastNodeIp="NULL")


def serve():
    node_ip = socket.gethostbyname(socket.gethostname())
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    jcoin_pb2_grpc.add_RegistrarServicer_to_server(Registrar(), server)
    server.add_insecure_port('172.17.0.2:50051')
    server.start()
    print('Registrar Server is live on ' + node_ip + ':50051')
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
