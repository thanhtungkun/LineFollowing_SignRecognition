import cv2
import socket
import pickle
import struct
import threading
import serial  # Import thư viện Serial
import time

previous_data = "straight"
# Kết nối với Arduino qua cổng UART
arduino = serial.Serial("/dev/serial0", 9600, timeout=1)  # Raspberry Pi UART

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", 8090))
server_socket.listen(5)

print("📡 Đang chờ kết nối từ Laptop...")
conn, addr = server_socket.accept()
print(f"✅ Đã kết nối với {addr}")

cap = cv2.VideoCapture(1)
if not cap.isOpened():  # Nếu camera 1 không hoạt động, thử camera 0
    print("Camera 1 không hoạt động, thử camera 0...")
    cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

def receive_from_arduino():
    global previous_data
    while True:
        try:
            dataFromArduino = arduino.readline().decode("utf-8", errors="ignore").strip()
            if dataFromArduino:
                print(f"📩 Nhận từ Arduino: {dataFromArduino}")

                # Nếu Arduino yêu cầu "setUp", gửi lại dữ liệu cũ
                if dataFromArduino == "setUp":
                    print(f"🔁 Gửi lại dữ liệu: {previous_data}")
                    arduino.write((previous_data + "\n").encode())

        except Exception as e:
            print(f"❌ Lỗi nhận từ Arduino: {e}")
            break

# 🔥 Nhận dữ liệu từ Laptop và gửi đến Arduino
def receive_from_laptop():
    global previous_data
    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            print(f"📩 Nhận từ Laptop: {data}")
            previous_data = data  # Lưu lại dữ liệu cũ
            arduino.write((data + "\n").encode())  # Gửi đến Arduino
            print(f"📤 Gửi đến Arduino: {data}")

        except Exception as e:
            print(f"❌ Lỗi nhận từ Laptop: {e}")
            break


# Chạy 2 thread song song
thread_arduino = threading.Thread(target=receive_from_arduino, daemon=True)
thread_laptop = threading.Thread(target=receive_from_laptop, daemon=True)


thread_arduino.start()
thread_laptop.start()


# Gửi video đến laptop
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    _, frame_encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    data = pickle.dumps(frame_encoded)
    msg_size = struct.pack("L", len(data))
    conn.sendall(msg_size + data)


thread_arduino.join()
thread_laptop.join()
cap.release()
conn.close()
server_socket.close()
arduino.close()  # Đóng kết nối Serial
