import socket
import time

from Config import CLIENT_IP, CTRL_IP, CTRL_PORT, DUT_IP, DUT_PORT
from DataClasses import RmtCmd
from HelpFunctions import EMPTY_MSG_ERR_NO, RecvTimeout


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ctrlSocket:
        # Verbinde mit Controller
        try:
            ctrlSocket.bind((str(CLIENT_IP), CTRL_PORT))
            ctrlSocket.connect((str(CTRL_IP), CTRL_PORT))
            print('Connected to controller!')
        except socket.error as e:
            print(f'Unable to connect to controller: {e}')
            return

        # Warte auf Testfallstart
        if not ctrlSocket.recv(1024) == RmtCmd.StartTest:
            print('Received abort from controller!')
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dutSocket:
            # Abtestung Sollverhalten | Verbinde mit DuT
            try:
                dutSocket.bind((str(CLIENT_IP), DUT_PORT))
                dutSocket.connect((str(DUT_IP), DUT_PORT))
                print('Connected to DuT')
            except socket.error as e:
                print(f'Unable to connect to DuT: {e}')
                ReportToController(ctrlSocket, False)
                return

            # Abtestung Sollverhalten | Sende Daten an DuT
            reqData = 42
            print(f'Send request: {reqData}')
            dutSocket.sendall(reqData.to_bytes(8, 'big'))
            respData = int.from_bytes(dutSocket.recv(1024), 'big')
            print(f'Received response {respData}')

            if respData != reqData + 1:
                ReportToController(ctrlSocket, False)
                return
            ReportToController(ctrlSocket, True)

            # Nebenläufige Abtestung des Sollverhaltens
            while True:

                # TCP-FIN erhalten?
                try:
                    data = dutSocket.recv(1024, socket.MSG_DONTWAIT)
                    if not data:
                        ReportToController(ctrlSocket, False)
                        break
                except socket.error as e:
                    if e.errno not in EMPTY_MSG_ERR_NO:
                        print(f'Error on DuT socket: {e} Errno: {e.errno}')

                # Testfallende?
                if RecvTimeout(ctrlSocket, 0) == RmtCmd.StopTest:
                    print(f'Received message from controller: {data}\nTerminate testcase!')
                    break

                # Sende Daten an DUT
                reqData += 2
                print(f'Send request: {reqData}')
                try:
                    dutSocket.sendall(reqData.to_bytes(8, 'big'))
                    data = RecvTimeout(dutSocket, 2)
                    data = int.from_bytes(data, 'big') if data else None
                except socket.error as e:
                    print(f'Error on DUT Socket: {e}')
                    ReportToController(ctrlSocket, False)
                    break
                print(f'Received response: {data}')

                if data != reqData + 1:
                    ReportToController(ctrlSocket, False)
                    return

                time.sleep(1)


def ReportToController(ctrlSocket: socket.socket, connStatus: bool):
    print(f'Send connection status to controller. Status: {connStatus}')
    if connStatus:
        ctrlSocket.sendall(RmtCmd.Working)
    else:
        ctrlSocket.sendall(RmtCmd.NotWorking)
        ctrlSocket.shutdown(socket.SHUT_RDWR)


if __name__ == '__main__':
    main()
