from utils.grpc.open_nat.open_nat_client import OpenNatClient


class OpenNatService:

    @staticmethod
    def init_vps_config_qy():
        return OpenNatClient.init_config_qy()


