# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: jcoin.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='jcoin.proto',
  package='jcoin',
  syntax='proto3',
  serialized_options=b'\n\026io.grpc.examples.jcoinB\nJCoinProtoP\001\242\002\003JCN',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0bjcoin.proto\x12\x05jcoin\":\n\x07NewNode\x12\x10\n\x08nVersion\x18\x01 \x01(\t\x12\r\n\x05nTime\x18\x02 \x01(\t\x12\x0e\n\x06\x61\x64\x64rMe\x18\x03 \x01(\t\"\x1e\n\x08LastNode\x12\x12\n\nlastNodeIp\x18\x01 \x01(\t2:\n\tRegistrar\x12-\n\x08Register\x12\x0e.jcoin.NewNode\x1a\x0f.jcoin.LastNode\"\x00\x42,\n\x16io.grpc.examples.jcoinB\nJCoinProtoP\x01\xa2\x02\x03JCNb\x06proto3'
)




_NEWNODE = _descriptor.Descriptor(
  name='NewNode',
  full_name='jcoin.NewNode',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='nVersion', full_name='jcoin.NewNode.nVersion', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='nTime', full_name='jcoin.NewNode.nTime', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='addrMe', full_name='jcoin.NewNode.addrMe', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=22,
  serialized_end=80,
)


_LASTNODE = _descriptor.Descriptor(
  name='LastNode',
  full_name='jcoin.LastNode',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='lastNodeIp', full_name='jcoin.LastNode.lastNodeIp', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=82,
  serialized_end=112,
)

DESCRIPTOR.message_types_by_name['NewNode'] = _NEWNODE
DESCRIPTOR.message_types_by_name['LastNode'] = _LASTNODE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

NewNode = _reflection.GeneratedProtocolMessageType('NewNode', (_message.Message,), {
  'DESCRIPTOR' : _NEWNODE,
  '__module__' : 'jcoin_pb2'
  # @@protoc_insertion_point(class_scope:jcoin.NewNode)
  })
_sym_db.RegisterMessage(NewNode)

LastNode = _reflection.GeneratedProtocolMessageType('LastNode', (_message.Message,), {
  'DESCRIPTOR' : _LASTNODE,
  '__module__' : 'jcoin_pb2'
  # @@protoc_insertion_point(class_scope:jcoin.LastNode)
  })
_sym_db.RegisterMessage(LastNode)


DESCRIPTOR._options = None

_REGISTRAR = _descriptor.ServiceDescriptor(
  name='Registrar',
  full_name='jcoin.Registrar',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=114,
  serialized_end=172,
  methods=[
  _descriptor.MethodDescriptor(
    name='Register',
    full_name='jcoin.Registrar.Register',
    index=0,
    containing_service=None,
    input_type=_NEWNODE,
    output_type=_LASTNODE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_REGISTRAR)

DESCRIPTOR.services_by_name['Registrar'] = _REGISTRAR

# @@protoc_insertion_point(module_scope)
