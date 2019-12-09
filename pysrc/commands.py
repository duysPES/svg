from enum import Enum


class Commands(Enum):
    ACK = b"\x06"
    NACK = b"\x15"
    GoInactive = b"\x1e"
    SendStatus = b"\x05"

    @staticmethod
    def is_ack(msg):
        return Commands.ACK.value == msg

    @staticmethod
    def is_nack(msg):
        return Commands.NACK.value == msg
