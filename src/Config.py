from ipaddress import IPv4Address

# Controller Einstellungen
CTRL_IP = IPv4Address('192.168.0.4')
IFACE_ID = 16


# Client Einstellungen
CLIENT_IP = IPv4Address('192.168.0.2')
CLIENT_MAC = bytes.fromhex('b8 27 eb b3 84 5e')


# DuT Einstellungen
DUT_IP = IPv4Address('192.168.0.3')
DUT_MAC = bytes.fromhex('b8 27 eb ab 85 3c')


# TCP Einstellungen
CTRL_PORT = 42000
DUT_PORT = 42069


# Testfalleinstellungen
TEST_TIMEOUT = 10
