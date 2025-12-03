import network
import socket
import _thread
import ujson as json
import os

# -----------------------------
# 1️⃣ Nastavenie AP
# -----------------------------
SSID = "ozonik"
PASSWORD = "12345678"
IP = "192.168.4.1"

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)
ap.ifconfig((IP, "255.255.255.0", IP, IP))
print("📶 AP beží:", SSID, "IP:", IP)

# -----------------------------
# 2️⃣ DNS server
# -----------------------------
def start_dns():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 53))
    print("🟢 DNS server beží...")
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
            response += bytes(map(int, IP.split('.')))
            s.sendto(response, addr)
        except:
            pass

# Spusti DNS v samostatnom vlákne
_thread.start_new_thread(start_dns, ())

# -----------------------------
# 3️⃣ Webserver (Captive portal)
# -----------------------------
settings = {"rtc":"", "onTime":"", "offTime":"", "power":"50"}

def mime(path):
    if path.endswith(".html"): return "text/html"
    if path.endswith(".css"): return "text/css"
    if path.endswith(".js"): return "application/javascript"
    if path.endswith(".png"): return "image/png"
    if path.endswith(".jpg") or path.endswith(".jpeg"): return "image/jpeg"
    if path.endswith(".svg"): return "image/svg+xml"
    if path.endswith(".ico"): return "image/x-icon"
    return "text/plain"

def anti_cache_headers(mime_type):
    return (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: {}\r\n"
        "Cache-Control: no-cache, no-store, must-revalidate\r\n"
        "Pragma: no-cache\r\n"
        "Expires: 0\r\n"
        "Connection: close\r\n\r\n"
    ).format(mime_type)

def send_file(conn, fname):
    fname = fname.lstrip("/")
    if fname == "":
        fname = "index.html"

    # favicon.ico ignorujeme
    if fname == "favicon.ico":
        conn.send(b"HTTP/1.1 204 No Content\r\n\r\n")
        return

    # ak súbor existuje, odošli ho
    if fname in os.listdir():
        try:
            with open(fname, "rb") as f:
                content = f.read()
            conn.send(anti_cache_headers(mime(fname)).encode())
            conn.send(content)
            print("✔ Súbor odoslaný:", fname)
        except Exception as e:
            print("🔥 Chyba pri čítaní súboru:", e)
            conn.send(b"HTTP/1.1 500 Internal Server Error\r\nConnection: close\r\n\r\nError")
    else:
        # súbor neexistuje → presmerovanie na root (captive portal)
        print("➡ Presmerovanie na root pre:", fname)
        r = "HTTP/1.1 302 Found\r\nLocation: http://{}/\r\n\r\n".format(IP)
        conn.send(r.encode())

def handle_save(conn, request):
    try:
        body = request.split("\r\n\r\n",1)[1]
        data = json.loads(body)
        settings["rtc"] = data.get("rtc","")
        settings["onTime"] = data.get("onTime","")
        settings["offTime"] = data.get("offTime","")
        settings["power"] = data.get("power","50")
        print("💾 Nastavenia uložené:", settings)
        conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nNastavenia ulozene!")
    except Exception as e:
        print("🔥 Chyba pri uklade:", e)
        conn.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\nChyba pri uklade")

def start_web():
    s = socket.socket()
    s.bind(("0.0.0.0", 80))
    s.listen(5)
    print("🌐 Webserver beží na IP:", IP)

    while True:
        conn, addr = s.accept()
        try:
            req = conn.recv(2048).decode()
        except:
            conn.close()
            continue

        print("\n📨 Požiadavka od:", addr)
        print(req.split("\r\n")[0])

        # POST /save
        if req.startswith("POST /save"):
            handle_save(conn, req)
            conn.close()
            continue

        # Každý GET request → odoslanie súboru / presmerovanie
        try:
            path = req.split(" ")[1]
        except:
            path = "/"
        send_file(conn, path)
        conn.close()

# Spusti webserver
start_web()
