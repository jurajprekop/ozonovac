import socket

def start_dns(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 53))
    print("DNS bezi...")

    while True:
        try:
            data, addr = s.recvfrom(256)

            # DNS odpoveda na všetko rovnakou IP
            response = data[:2] + b'\x81\x80' + data[4:6] + data[4:6] + b'\x00\x00\x00\x00'
            response += data[12:]  # otázka
            response += b'\xc0\x0c'  # pointer
            response += b'\x00\x01'  # type A
            response += b'\x00\x01'  # class IN
            response += b'\x00\x00\x00\x3c'  # TTL 60s
            response += b'\x00\x04'  # dlzka
            response += bytes(map(int, ip.split('.')))

            s.sendto(response, addr)
        except:
            pass
