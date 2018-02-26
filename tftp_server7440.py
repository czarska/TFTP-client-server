#!/usr/bin/env python
import socket
import struct
import os
import sys

PATH = str(sys.argv[2])
PORT = int(sys.argv[1])
HOST = ''
SIZE = 516

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.settimeout(0.1)

rec_opcode = ''
message = ''
filename = ''
blocks = ''

#Waiting for request
while rec_opcode != 1:
    try:
        (msg, (HOST, PORT)) = sock.recvfrom(SIZE)
        temp = struct.unpack("!H", msg[:2])
        rec_opcode = temp[0]
        filename = msg.split('\x00\x01')[1].split('\0')[0]
        blocks = msg.split('\x00\x01')[1].split('\0')[6]
    except Exception:
        continue

#Prepare file to send
fn = os.path.join(PATH, filename)
file = open(fn, "rb")

#Creating first datagram
data = file.read(SIZE - 4)
datagram = str(struct.pack("!H", 3) + struct.pack("!H", 1) + data)

#Check if it's last datagram
if len(data) < SIZE - 4:
    lastpack = 1
else:
    lastpack = 0

#Creating AOCK
aock = str(struct.pack("!H", 6) + 'windowsize' + struct.pack("!H", 0) + blocks + struct.pack("!H", 0))

#Sending AOCK till OCK0
while rec_opcode != 4 or block_nr != 0:
    try:
        sock.sendto(aock, (HOST, PORT))
        (msg, (HOST, PORT)) = sock.recvfrom(SIZE)
        temp = struct.unpack("!H", msg[:2])
        rec_opcode = temp[0]
        temp = struct.unpack("!H", msg[2:4])
        block_nr = temp[0]
    except Exception:
        continue

#Sending file
sended_counter = 0 #0-blocks count how many we sended
last_ack = 1
block_counter = 1
while True:
    try:
        if sended_counter == blocks:
            (msg, (HOST, PORT)) = sock.recvfrom(SIZE)
            temp = struct.unpack("!H", msg[:2])
            rec_opcode = temp[0]
            temp = struct.unpack("!H", msg[2:4])
            block_nr = temp[0]
            sended_counter = 0
            last_ack = block_nr
            if rec_opcode != 4 or block_nr != block_counter:
                data = file.seek(512*block_nr)
                data = file.read(SIZE - 4)
                lastpack = 0
                datagram = str(struct.pack("!H", 3) + struct.pack("!H", block_nr+1) + data)
                continue
        sock.sendto(datagram, (HOST, PORT))
        if lastpack == 1:
            break;
        block_counter = block_counter + 1
        sended_counter = sended_counter + 1
        data = file.read(SIZE - 4)
        datagram = str(struct.pack("!H", 3) + struct.pack("!H", block_counter) + data)
        if len(data) < SIZE - 4:
            lastpack = 1
    except Exception:
        data = file.seek(512*last_ack)
        data = file.read(SIZE - 4)
        lastpack = 0
        datagram = str(struct.pack("!H", 3) + struct.pack("!H", last_ack) + data)
        sended_counter = 0
        continue

file.close()
