```
pip install grpcio grpcio-tools pycryptodome

python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/open_nat.proto

python -m vps.server.app
```