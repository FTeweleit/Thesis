import socket

from Config import DUT_IP, DUT_PORT


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcpSocket:
        tcpSocket.bind((str(DUT_IP), DUT_PORT))
        tcpSocket.listen()

        while True:
            print('Listening...')
            rmtSocket, rmtAddr = tcpSocket.accept()
            print(f'Connected to: {rmtAddr}')

            while True:
                try:
                    data = rmtSocket.recv(1024)
                except socket.error:
                    break
                if not data:
                    rmtSocket.shutdown(socket.SHUT_RDWR)
                    break
                data = int.from_bytes(data, 'big')
                print(f'Received request: {data}\nSend response: {data + 1}')
                rmtSocket.sendall((data + 1).to_bytes(8, 'big'))


if __name__ == '__main__':
    main()
