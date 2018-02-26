#!/usr/bin/env python
import socket
import hashlib
import md5
import sys
import struct

filename = str(sys.argv[2])
servername = str(sys.argv[1])

HOST = servername
PORT = 6969
SIZE = 516
MAXRETRY = 256

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.1)

rec_opcode = ''
mode = 'octet'
block_nr = '' #number of block we just recived
exp_block_nr = 1 #number of block we should have received
ret_counter = 0 #counts how many times we try to receive sth
rec_flag = 1 #for checking if it's last
blocks = 16 #how many dg in one window
err = 0
normal = 1 #windowsize or not
rrq = str(struct.pack("!H", 1) + filename + struct.pack("!H", 0) + mode + struct.pack("!H", 0) + 'windowsize' + struct.pack("!H", 0) + str(blocks) + struct.pack("!H", 0))
m = md5.new()

#Prepare file
file = open("message.txt", "a")


#Sending request to server till oack or first dg
while rec_opcode != 6 and (rec_opcode != 3 or block_nr != exp_block_nr):
    try:
        sock.sendto(rrq, (HOST, PORT))
        (msg, (HOST,PORT)) = sock.recvfrom(SIZE)
        temp = struct.unpack("!H", msg[:2])
        rec_opcode = temp[0]
        if rec_opcode == 6:
            blocks = int(msg[14:-2])
            normal = 0
        elif rec_opcode == 3:
            temp = struct.unpack("!H", msg[2:4])
            block_nr = temp[0]
            normal = 1
    except Exception:
        if ret_counter < MAXRETRY:
            ret_counter = ret_counter + 1
            continue

#Checking if it's last package
if normal == 1 and len(msg) < SIZE:
    rec_flag = 0

#If we recived dg it means we don't use windowsize
if normal == 1:
    m.update(msg[4:])
    file.write(msg[4:])
    ack = str(struct.pack("!HH", 4, 1))
    #Receiving message
    while rec_flag == 1:
        try:
            sock.sendto(ack, (HOST, PORT))
            (msg, (HOST,PORT)) = sock.recvfrom(SIZE)
            temp = struct.unpack("!H", msg[:2])
            rec_opcode = temp[0]
            temp = struct.unpack("!H", msg[2:4])
            block_nr = temp[0]
            if rec_opcode != 3 or block_nr != ((exp_block_nr+1)%65536):
                continue
            exp_block_nr = (exp_block_nr + 1)%65536
            ack = str(struct.pack("!HH", 4, exp_block_nr))
            ret_counter = 0
            m.update(msg[4:])
            file.write(msg[4:])
            if len(msg) < SIZE:
                sock.sendto(ack, (HOST, PORT))
                rec_flag = 0
        except Exception:
            if ret_counter < MAXRETRY:
                ret_counter = ret_counter + 1
                continue
else:
    #Receiving message
    blocks_counter = 0 #count recived dg 0-blocks (to send ack after blocks dg)
    dg_counter = 0 #how many dg's we have
    exp_block_nr = 0
    ack = str(struct.pack("!HH", 4, 0))
    while rec_flag == 1:
        try:
            #We send ack 1.error, 2.if windowsize=1, 3.after windowsize
            if (err == 1) or (blocks == 1 or blocks_counter%blocks == 0 ):
                blocks_counter = 1
                sock.sendto(ack, (HOST, PORT))
            err = 0
            (msg, (HOST,PORT)) = sock.recvfrom(SIZE)
            temp = struct.unpack("!H", msg[:2])
            rec_opcode = temp[0]
            temp = struct.unpack("!H", msg[2:4])
            block_nr = temp[0]
            #Check if it's good number, if not send ack again and again start counting recived dg
            if rec_opcode != 3 or block_nr != ((exp_block_nr+1)%65536):
                err = 1
                blocks_counter = 1
                ack = str(struct.pack("!HH", 4, dg_counter))
                continue
            #if we are here it means that we recived one more good dg
            blocks_counter = blocks_counter + 1
            dg_counter = dg_counter + 1
            exp_block_nr = (exp_block_nr + 1)%65536
            ack = str(struct.pack("!HH", 4, exp_block_nr))
            ret_counter = 0
            m.update(msg[4:])
            file.write(msg[4:])
            if len(msg) < SIZE:
                sock.sendto(ack, (HOST, PORT))
                rec_flag = 0
        except Exception:
            if ret_counter < MAXRETRY:
                ret_counter = ret_counter + 1
                blocks_counter = 1
                err = 1
                continue
            else:
                rec_flag = 0

print m.hexdigest()
file.close()
