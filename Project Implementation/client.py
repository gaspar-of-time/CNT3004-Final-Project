#!/usr/bin/python
import os
import sys
import socket

IP = "localhost"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"


def main():
    while True:
        command = input("Input Command (type help for help): ")
        commandSubstrings = command.split()
        match commandSubstrings[0].lower():
            case "help":
                print("Commands:\n  connect [ip]:[port]\n       Connects to server\n  upload [local filepath] [server filepath]\n     Uploads file to connected server\n    download [server filepath] [local filepath]\n       Downloads file from connected server\n  delete [server filepath]\n      Delete file from connected server\n  dir [server filepath]\n        List files in specified directory\n subfolder [create|delete] [server path]")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break

        data = input("> ")
        data = data.split(" ")
        cmd = data[0]
        client.send(cmd.encode(FORMAT))
        if cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

    print("Disconnected from the server.")
    client.close()  # close the connection


if __name__ == "__main__":
    main()
