#!/usr/bin/python
import os
import socket
import threading
import datetime
import time

IP = "0.0.0.0"
PORT = 4451
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"


def handle_client(conn, addr, starttime):

    print(f"[NEW CONNECTION] {addr} connected.")
    while True:
        # expected response is [current upload data speed]@[current download data speed]@[time spent on last file]@[last file name]
        data = conn.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        if (data[0] == ""):
            break
        with open("./Logs/"+starttime, 'a') as log:
            log.write("Current Time:"+str(datetime.datetime.now())+", IP Address:"+str(addr)+", Transfer Speed (MB/s):"+data[0]+", Time spent on file (s):"+data[1]+", File Name:"+data[2]+"\n")
            log.close()


def main():
    print("Starting the server")
    if (not os.path.isdir("./Logs")):
        try:
            os.mkdir("./Logs")
        except:
            print("Unable to create logs directory.\nTerminating server.")
            quit()
    server = socket.socket(socket.AF_INET,
                           socket.SOCK_STREAM)  # used IPV4 and TCP connection
    server.bind(ADDR)  # bind the address
    server.listen()  # start listening
    print(f"server is listening on {IP}: {PORT}")
    starttime = str(datetime.datetime.now())
    while True:
        conn, addr = server.accept()  # accept a connection from a client
        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr, starttime))  # assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
