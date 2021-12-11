import socket
import struct
import time
import cv2 as cv

address = ("192.168.47.1", 8080)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(address)
s.listen(1)

transfered_data = 0

while True:
    print("waiting...")
    client, addr = s.accept()

    if client:
        print('got connected from', addr)
        buf = b''
        while len(buf)<4:
            buf += client.recv(4-len(buf))
        size = struct.unpack('!i', buf)
        print("receiving %s bytes" % size)

        with open('picture.jpg', 'wb') as img:
            temp = 0
            while int(temp) < int(size[0]):
                data = client.recv(1024)
                img.write(data)
                temp = temp + len(data)
        print('received')

        from yolo import load_image

        danger = load_image('picture.jpg')

        with open('picture.jpg', 'rb') as f:
            try:
                data = f.read(1024)
                while data:
                    transfered_data += client.send(data)
                    data = f.read(1024)
                    print("전송완료 %s, 전송량 %d" % ('picture.jpg', transfered_data))
            except Exception as ex:
                print(ex)
    client.close()






