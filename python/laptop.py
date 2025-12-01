import cv2
import socket
import pickle
import struct
import threading
import torch
from ultralytics import YOLO
import numpy as np
import time
# Load YOLOv8n model
model = YOLO("best.pt")
# model = YOLO("best_medium.pt")


server_ip = "192.168.137.26"  
server_port = 8090

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_ip, server_port))

print("✅ Đã kết nối tới Raspberry Pi")

data = b""
payload_size = struct.calcsize("L")
last_label_sent = ""
no_label_start_time = None  
delay_threshold = 0.3  # 300ms 
# Gửi dữ liệu đến Raspberry Pi
def send_data():
    while True:
        msg = input("Nhập dữ liệu gửi đến Raspberry Pi: ")
        client_socket.sendall(msg.encode())

threading.Thread(target=send_data, daemon=True).start()

while True:
    while len(data) < payload_size:
        data += client_socket.recv(4096)
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4096)

    frame_data = data[:msg_size]
    data = data[msg_size:]

    frame_encoded = pickle.loads(frame_data)
    frame = cv2.imdecode(frame_encoded, cv2.IMREAD_COLOR)
    
    # Run YOLOv8 detection
    results = model(frame)
    best_label = ""
    best_area = 0
    best_conf = 0
    
    for result in results:

        for box in result.boxes:
            cls = int(box.cls[0])  # Get class index
            label = model.names[cls]   # Get label name
            conf = float(box.conf[0])  # Get confidence
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            
            # Select the label with the largest area and highest confidence
            if ( area >= best_area):
                best_label = best_label = "straight" if label == "back" else label
                best_area = area
                best_conf = conf
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label+" "+str(round(conf,2))+" "+str(area), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
    current_time = time.time()
    # Xác định lệnh gửi đến Raspberry Pi
    if (best_label is None or best_label == "" or best_label == "no detections") and last_label_sent == "stop":
        if no_label_start_time is None:
            no_label_start_time = current_time

        # Kiểm tra nếu đã qua 500ms mà vẫn không nhận diện được gì
        if (current_time - no_label_start_time) >= delay_threshold:
            command = "straight"
        else:
            command = last_label_sent  # Giữ nguyên "stop" trong khoảng thời gian chờ

    # Nếu phát hiện nhãn khác (VD: "right", "left"), cập nhật ngay
    else:
        command = best_label
        no_label_start_time = None  # Reset thời gian mất nhãn
    
    # Send detected label to Raspberry Pi
    if command and command != last_label_sent :
        client_socket.sendall((command + "\n").encode())
        last_label_sent = command
    
    cv2.imshow("📡 Stream từ Raspberry Pi", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
client_socket.close()
