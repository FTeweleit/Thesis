from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ipaddress import IPv4Address


class ProtocolType(bytes, Enum):
    TCP = bytes.fromhex('06')
    IPv4 = bytes.fromhex('08 00')
    ARP = bytes.fromhex('08 06')


class ArpHardwareType(bytes, Enum):
    Ethernet = bytes.fromhex('00 01')


class ArpOpCode(bytes, Enum):
    Request = bytes.fromhex('00 01')
    Reply = bytes.fromhex('00 02')


class ArpFrame(EthernetFrame):
    def __init__(self, dstEthAddr: bytes, srcEthAddr: bytes, opCode: ArpOpCode, srcHwAddr: bytes,
                 srcIpAddr: 'IPv4Address', dstHwAddr: bytes, dstIpAddr: 'IPv4Address',
                 hwType: bytes = ArpHardwareType.Ethernet, protType: bytes = ProtocolType.IPv4,
                 hwSize: bytes = bytes.fromhex('06'), protSize: bytes = bytes.fromhex('04')):
        EthernetFrame.__init__(self, dstEthAddr, srcEthAddr, ProtocolType.ARP)

        self._hwType = hwType
        self._protType = protType
        self._hwSize = hwSize
        self._protSize = protSize
        self._opCode = opCode

        self._dstIpAddr = dstIpAddr
        self._dstHwAddr = dstHwAddr
        self._srcIpAddr = srcIpAddr
        self._srcHwAddr = srcHwAddr

    def Pack(self) -> bytes:
        ethHeader = EthernetFrame.Pack(self)
        arpPacket = (self._hwType + self._protType + self._hwSize + self._protSize + self._opCode + self._srcHwAddr +
                     self._srcIpAddr.packed + self._dstHwAddr + self._dstIpAddr.packed)

        return ethHeader + arpPacket

    @staticmethod
    def Unpack(rawData: bytes) -> 'ArpFrame':
        raise NotImplemented






