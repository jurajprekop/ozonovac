import socket
import os
import ujson as json

# MIME typy
def mime(path):
    if path.endswith(".html"): return "text/html"
    if path.endswith(".css"): return "text/css"
    if path.endswith(".js"): return "application/javascript"
    if path.endswith(".png"): return "image/png"
    if path.endswith(".jpg") or path.endswith(".jpeg"): return "image/jpeg"
    if path.endswith(".svg"): return "image/svg+xml"
    if path.endswith(".ico"): return "image/x-icon"
    return "text/plain"

# Anti-cache headers
def anti_cache_headers(mime_type):
    return (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: {}\r\n"
        "Cache-Control: no-cache, no-store, must-revalidate\r\n"
        "Pragma: no-cache\r\n"
        "Expires: 0\r\n"
        "Connection: close\r\n\r\n"
    ).format(mime_type)

# Nastavenia
settings = {"rtc":"", "onTime":"", "offTime":"", "power":"50"}

# Odoslanie súboru
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

# Spracovanie POST /save
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

# Spustenie webservera
def start_web(ip):
    global IP
    IP = ip
    s = socket.socket()
    s.bind(("0.0.0.0", 80))
    s.listen(5)
    print("🌐 Webserver beží (full captive portal) na IP:", ip)

    while True:
        conn, addr = s.accept()
        req = conn.recv(2048).decode()
        print("\n📨 Požiadavka od:", addr)
        print(req.split("\r\n")[0])

        # POST /save
        if req.startswith("POST /save"):
            handle_save(conn, req)
            conn.close()
            continue

        # Každý request GET (alebo neznámy) → presmerovanie / odoslanie súboru
        try:
            path = req.split(" ")[1]
        except:
            path = "/"
        send_file(conn, path)
        conn.close()
