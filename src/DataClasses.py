from abc import ABC
from enum import Enum
from operator import xor
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ipaddress import IPv4Address


class RmtCmd(bytes, Enum):
    StartTest = bytes.fromhex('00')
    StopTest = bytes.fromhex('01')
    Working = bytes.fromhex('02')
    NotWorking = bytes.fromhex('03')


class ProtocolType(bytes, Enum):
    TCP = bytes.fromhex('06')
    IPv4 = bytes.fromhex('08 00')
    ARP = bytes.fromhex('08 06')


class EthernetFrame:
    def __init__(self, dstAddr, srcAddr, ethType: bytes):
        self._dstEthAddr = dstAddr
        self._srcEthAddr = srcAddr
        self._ethType = ethType

    def Pack(self) -> bytes:
        return self._dstEthAddr + self._srcEthAddr + self._ethType


class IpFrame(EthernetFrame):
    def __init__(self, dstEthAddr: bytes, srcEthAddr: bytes, dstIpAddr: 'IPv4Address', srcIpAddr: 'IPv4Address',
                 protType: 'ProtocolType', ipId: int = 0):
        EthernetFrame.__init__(self, dstEthAddr, srcEthAddr, ProtocolType.IPv4)

        self._header = bytes.fromhex('45')                    # IPv4, mit 20 byte Länge
        self._services = bytes.fromhex('00')
        self._length = bytes.fromhex('00 00')                 # Gesetzt während Pack()
        self._id = ipId.to_bytes(2, 'big')
        self._flags = bytes.fromhex('40 00')                  # steht für 'don't Fragment'
        self._ttl = bytes.fromhex('40')                       # ist immer 64
        self._protocol = protType
        self._checksum = bytes.fromhex('00 00')               # Gesetzt während Pack()
        self._srcIpAddr = srcIpAddr
        self._dstIpAddr = dstIpAddr

    def Pack(self) -> bytes:
        ethFrame = EthernetFrame.Pack(self)
        payloadLength = self._GetPayloadLength()
        length = (((int.from_bytes(self._header, 'big') & 0x0f) * 4) + payloadLength).to_bytes(2, 'big')

        ipFrame = (self._header + self._services + length + self._id + self._flags + self._ttl + self._protocol +
                   self._checksum + self._srcIpAddr.packed + self._dstIpAddr.packed)
        checksum = self.IpChecksum(ipFrame)
        ipFrame = ipFrame[:10] + checksum + ipFrame[12:]

        return ethFrame + ipFrame

    def _GetPayloadLength(self) -> int:
        raise NotImplemented

    @staticmethod
    def IpChecksum(ipHeader: bytes) -> bytes:
        checksum = 0

        for i in range(2, ((ipHeader[0] & 0x0f) + 1) * 4, 2):
            checksum = AddCarry(checksum, int.from_bytes(ipHeader[i - 2:i], 'big'))

        checksum = xor(checksum, 0xffff)
        return checksum.to_bytes(2, 'big')


class TcpFrame(ABC, IpFrame):
    def __init__(self, dstEthAddr: bytes, srcEthAddr: bytes, dstIpAddr: 'IPv4Address', srcIpAddr: 'IPv4Address',
                 ipId: int, srcPort: bytes, dstPort: bytes, seqNo: bytes, ackNo: bytes):
        IpFrame.__init__(self, dstEthAddr, srcEthAddr, dstIpAddr, srcIpAddr, ProtocolType.TCP, ipId)

        self._srcPort = srcPort
        self._dstPort = dstPort
        self._seqNo = seqNo
        self._ackNo = ackNo

        self._window = bytes.fromhex('01 fd')               # immer 509
        self._checksum = bytes.fromhex('00 00')
        self._pointer = bytes.fromhex('00 00')

        self._lengthAndFlags = None

    def _GetPayloadLength(self) -> int:
        return ((int.from_bytes(self._lengthAndFlags, 'big') & 0xf000) >> 12) * 4

    def Pack(self) -> bytes:
        pseudoIpHeader = (self._srcIpAddr.packed + self._dstIpAddr.packed + bytes.fromhex('00 06') +
                          self._GetPayloadLength().to_bytes(2, 'big'))
        tcpFrame = (self._srcPort + self._dstPort + self._seqNo + self._ackNo + self._lengthAndFlags + self._window +
                    self._checksum + self._pointer)
        checksum = self.TcpChecksum(pseudoIpHeader + tcpFrame)
        tcpFrame = tcpFrame[:16] + checksum + tcpFrame[18:]

        return IpFrame.Pack(self) + tcpFrame

    @staticmethod
    def TcpChecksum(tcpHeader: bytes) -> bytes:
        checksum = 0
        if len(tcpHeader) % 2 != 0:
            tcpHeader += bytes.fromhex('00')

        for i in range(2, len(tcpHeader) + 2, 2):
            checksum = AddCarry(checksum, int.from_bytes(tcpHeader[i - 2:i], 'big'))

        checksum = xor(checksum, 0xffff)
        return checksum.to_bytes(2, 'big')


class TcpFinFrame(TcpFrame):
    def __init__(self, dstEthAddr: bytes, srcEthAddr: bytes, dstIpAddr: 'IPv4Address', srcIpAddr: 'IPv4Address',
                 ipId: int, srcPort: bytes, dstPort: bytes, seqNo: bytes, ackNo: bytes):
        TcpFrame.__init__(self, dstEthAddr, srcEthAddr, dstIpAddr, srcIpAddr, ipId, srcPort, dstPort, seqNo, ackNo)

        self._lengthAndFlags = bytes.fromhex('50 11')  # Länge -> 20 bytes, flags -> FIN, ACK


class TcpAckFrame(TcpFrame):
    def __init__(self, dstEthAddr: bytes, srcEthAddr: bytes, dstIpAddr: 'IPv4Address', srcIpAddr: 'IPv4Address',
                 ipId: int, srcPort: bytes, dstPort: bytes, seqNo: bytes, ackNo: bytes):
        TcpFrame.__init__(self, dstEthAddr, srcEthAddr, dstIpAddr, srcIpAddr, ipId, srcPort, dstPort, seqNo, ackNo)

        self._lengthAndFlags = bytes.fromhex('50 10')  # Länge -> 20 bytes, flags -> ACK


def AddCarry(a: int, b: int) -> int:
    result = a + b
    while len(bin(result)) - 2 > 16:
        result = (result % 0x10000) + 1
    return result
