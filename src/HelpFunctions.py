import socket
import time

from Config import CLIENT_IP, CLIENT_MAC, DUT_IP, DUT_MAC, DUT_PORT
from DataClasses import TcpFinFrame
from typing import Optional


EMPTY_MSG_ERR_NO = [socket.EAGAIN, socket.EWOULDBLOCK]


def RecvTimeout(rmtSocket: socket.socket, timeout: int) -> Optional[bytes]:
    rmtSocket.setblocking(False)
    data = None
    startTime = time.time()
    while True:
        try:
            data = rmtSocket.recv(1024)
            break
        except socket.error as e:
            if e.errno not in EMPTY_MSG_ERR_NO:
                raise e
        if time.time() > startTime + timeout:
            break
        time.sleep(0.1)
    rmtSocket.setblocking(True)
    return data


def BuildSpoofedTcpPackets(ipId: int, sequNo: bytes, ackNo: bytes) -> TcpFinFrame:
    finFrame = TcpFinFrame(dstEthAddr=DUT_MAC,
                           srcEthAddr=CLIENT_MAC,
                           dstIpAddr=DUT_IP,
                           srcIpAddr=CLIENT_IP,
                           ipId=ipId+1,
                           srcPort=DUT_PORT.to_bytes(2, 'big'),
                           dstPort=DUT_PORT.to_bytes(2, 'big'),
                           seqNo=sequNo,
                           ackNo=ackNo)
    return finFrame
