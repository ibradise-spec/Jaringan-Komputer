import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 5001  # Port beda dari multicast
BUFFER_SIZE = 4096
SAVE_DIR = 'received_files'

def terima_pesan(conn):
    """Thread untuk menerima pesan/file dari server"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    while True:
        try:
            header = b""
            while not header.endswith(b"\n"):
                byte = conn.recv(1)
                if not byte:
                    return
                header += byte

            header = header.decode().strip()
            if not header:
                continue

            parts = header.split('|')
            tipe = parts[0]

            if tipe == 'TEKS':
                pengirim = parts[1]
                pesan = parts[2]
                print(f"\n[BROADCAST MASUK] Dari {pengirim}: {pesan}")
                print(">> ", end='', flush=True)

            elif tipe == 'FILE':
                pengirim = parts[1]
                nama_file = parts[2]
                ukuran = int(parts[3])

                print(f"\n[FILE BROADCAST] Dari {pengirim}: {nama_file} ({ukuran} bytes)")

                save_path = os.path.join(SAVE_DIR, f"dari_{pengirim}_{nama_file}")
                diterima = 0
                with open(save_path, 'wb') as f:
                    while diterima < ukuran:
                        sisa = ukuran - diterima
                        chunk = conn.recv(min(BUFFER_SIZE, sisa))
                        if not chunk:
                            break
                        f.write(chunk)
                        diterima += len(chunk)

                print(f"[FILE] Disimpan di: {save_path}")
                print(">> ", end='', flush=True)

        except Exception as e:
            print(f"\n[CLIENT] Koneksi terputus: {e}")
            break

def kirim_file(conn, nama_saya, path_file):
    """Kirim file ke server untuk di-broadcast ke semua"""
    if not os.path.exists(path_file):
        print(f"[ERROR] File tidak ditemukan: {path_file}")
        return

    nama_file = os.path.basename(path_file)
    ukuran = os.path.getsize(path_file)

    # Kirim header
    header = f"FILE|{nama_saya}|{nama_file}|{ukuran}\n"
    conn.sendall(header.encode())

    # Tunggu server siap
    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    resp = resp.decode().strip()

    if resp != "SIAP":
        print(f"[ERROR] Server tidak siap: {resp}")
        return

    # Kirim file
    print(f"[CLIENT] Mengirim '{nama_file}' ({ukuran} bytes) ke semua...")
    with open(path_file, 'rb') as f:
        terkirim = 0
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            conn.sendall(chunk)
            terkirim += len(chunk)
            persen = (terkirim / ukuran) * 100
            print(f"\r[CLIENT] Progress: {persen:.1f}%", end='', flush=True)

    # Tunggu OK
    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    print(f"\n[CLIENT] File berhasil di-broadcast!")

def kirim_teks(conn, nama_saya, pesan):
    """Kirim teks ke server untuk di-broadcast ke semua"""
    msg = f"TEKS|{nama_saya}|{pesan}\n"
    conn.sendall(msg.encode())

    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    print("[CLIENT] Pesan berhasil di-broadcast!")

def menu_pengirim(conn, nama_saya):
    """Menu untuk pengirim broadcast"""
    print(f"\n[MODE BROADCAST] Kamu: {nama_saya} | Tujuan: SEMUA")

    while True:
        print("\n===== MENU BROADCAST =====")
        print("1. Kirim 1-5 kata")
        print("2. Kirim 1 kalimat panjang")
        print("3. Kirim 1 paragraf")
        print("4. Kirim dokumen (txt, docx, pdf)")
        print("5. Kirim gambar (jpg, png)")
        print("6. Kirim suara (mp3)")
        print("7. Kirim video (mp4)")
        print("8. Keluar")
        pilihan = input(">> Pilih: ").strip()

        if pilihan == '1':
            pesan = input("Masukkan 1-5 kata: ").strip()
            kata = pesan.split()
            if len(kata) < 1 or len(kata) > 5:
                print("[ERROR] Harus 1-5 kata!")
                continue
            kirim_teks(conn, nama_saya, pesan)

        elif pilihan == '2':
            pesan = input("Masukkan 1 kalimat panjang: ").strip()
            kirim_teks(conn, nama_saya, pesan)

        elif pilihan == '3':
            print("Masukkan paragraf (ketik END di baris baru untuk selesai):")
            baris = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                baris.append(line)
            pesan = ' '.join(baris)
            kirim_teks(conn, nama_saya, pesan)

        elif pilihan == '4':
            path = input("Masukkan path file dokumen (txt/docx/pdf): ").strip().strip('"').strip("'")
            kirim_file(conn, nama_saya, path)

        elif pilihan == '5':
            path = input("Masukkan path file gambar (jpg/png): ").strip().strip('"').strip("'")
            kirim_file(conn, nama_saya, path)

        elif pilihan == '6':
            path = input("Masukkan path file audio (mp3): ").strip().strip('"').strip("'")
            kirim_file(conn, nama_saya, path)

        elif pilihan == '7':
            path = input("Masukkan path file video (mp4): ").strip().strip('"').strip("'")
            kirim_file(conn, nama_saya, path)

        elif pilihan == '8':
            print("[CLIENT] Keluar...")
            break

        else:
            print("[ERROR] Pilihan tidak valid!")

def main():
    print("===== CLIENT BROADCAST =====")
    nama_saya = input("Masukkan nama kamu: ").strip()

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((HOST, PORT))

    # Kirim nama ke server
    conn.sendall((nama_saya + '\n').encode())

    # Tunggu konfirmasi
    resp = b""
    while not resp.endswith(b"\n"):
        resp += conn.recv(1)
    print(f"[CLIENT] {resp.decode().strip()}")

    # Pilih mode
    print("\nPilih mode:")
    print("1. Pengirim (A) - broadcast ke semua")
    print("2. Penerima - tunggu broadcast")
    mode = input(">> Pilih: ").strip()

    if mode == '1':
        menu_pengirim(conn, nama_saya)

    elif mode == '2':
        print(f"[CLIENT] Mode penerima aktif. Menunggu broadcast...")
        terima_thread = threading.Thread(target=terima_pesan, args=(conn,))
        terima_thread.daemon = True
        terima_thread.start()
        terima_thread.join()

    conn.close()

if __name__ == '__main__':
    main()