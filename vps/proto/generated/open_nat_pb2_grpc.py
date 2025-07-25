# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import vps.proto.generated.open_nat_pb2 as open__nat__pb2

GRPC_GENERATED_VERSION = '1.71.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in open_nat_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class OpenNatServerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SendWeChatText = channel.unary_unary(
                '/open_nat.OpenNatServer/SendWeChatText',
                request_serializer=open__nat__pb2.WeChatTextRequest.SerializeToString,
                response_deserializer=open__nat__pb2.CommonResponse.FromString,
                _registered_method=True)
        self.NatHttpSend = channel.unary_unary(
                '/open_nat.OpenNatServer/NatHttpSend',
                request_serializer=open__nat__pb2.NatHttpRequest.SerializeToString,
                response_deserializer=open__nat__pb2.CommonResponse.FromString,
                _registered_method=True)


class OpenNatServerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SendWeChatText(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def NatHttpSend(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_OpenNatServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SendWeChatText': grpc.unary_unary_rpc_method_handler(
                    servicer.SendWeChatText,
                    request_deserializer=open__nat__pb2.WeChatTextRequest.FromString,
                    response_serializer=open__nat__pb2.CommonResponse.SerializeToString,
            ),
            'NatHttpSend': grpc.unary_unary_rpc_method_handler(
                    servicer.NatHttpSend,
                    request_deserializer=open__nat__pb2.NatHttpRequest.FromString,
                    response_serializer=open__nat__pb2.CommonResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'open_nat.OpenNatServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('open_nat.OpenNatServer', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class OpenNatServer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SendWeChatText(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/open_nat.OpenNatServer/SendWeChatText',
            open__nat__pb2.WeChatTextRequest.SerializeToString,
            open__nat__pb2.CommonResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def NatHttpSend(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/open_nat.OpenNatServer/NatHttpSend',
            open__nat__pb2.NatHttpRequest.SerializeToString,
            open__nat__pb2.CommonResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
