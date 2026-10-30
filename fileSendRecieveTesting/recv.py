import os
import socket


# IP = "192.168.1.101" #"localhost"
IP = "localhost"
PORT = 1738
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def main():

    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    f = open("./recv/test.txt", "wb")
    f.write(client.recv(SIZE))



    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
