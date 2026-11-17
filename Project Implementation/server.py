#!/usr/bin/python
import os
import socket
import threading
import fstream
import shutil

IP = "0.0.0.0"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"


def getFile(socket, path):
    # overwriting file at path
    f = open(path, "wb")
    f.write(b'')

    # opening file with append
    f = open(path, "ab")
    test = True

    # append data to file until done
    while (test != b''):
        test = socket.recv(SIZE)
        print(f"{test}")
        f.write(test)


# to handle the clients
def handle_client(conn, addr):

    print(f"[NEW CONNECTION] {addr} connected.")

    while True:
        data = conn.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        cmd = data[0]
        path = data[1]
        match cmd:
            case "UPLOAD":
                # expected msg from client is UPLOAD@ [server filepath]

                if (os.path.exists(path)):
                    # if the file exists send that it exists
                    send_data = "EXISTS@"
                    conn.send(send_data.encode(FORMAT))

                    # recieve response either OVRW@ for overwrite or NO@ for no
                    data = conn.recv(SIZE).decode(FORMAT)
                    data = data.split("@")
                    if (data[0] == "OVRW"):

                        # after the client recieves RDYRECV it should start sending the file
                        send_data = "RDYRECV@"
                        conn.send(send_data.encode(FORMAT))
                        getFile(conn, path)

                        # sending DONE when done
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))
                    elif (data[0] == "NO"):
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))
                else:
                    send_data = "RDYRECV@"
                    conn.send(send_data.encode(FORMAT))
                    getFile(conn, path)
                    send_data = "DONE@"
                    conn.send(send_data.encode(FORMAT))

            case "DELETE":
                # expected msg from client is DELETE@ [server filepath]

                if (os.path.exists(path)):
                    os.remove(path)
                    send_data = "DONE@"
                    conn.send(send_data.encode(FORMAT))
                else:
                    send_data = "DNE@"
                    conn.send(send_data.encode(FORMAT))

            case "DOWNLOAD":
                # expected msg from client is DOWNLOAD@ [server filepath]

                data = conn.recv(SIZE).decode(FORMAT)
                data = data.split("@")
                if (data[0] == "RDYRECV"):
                    f = open(path, "rb", buffering=0)
                    conn.sendfile(f)
                    send_data = "DONE@"
                    conn.send(send_data.encode(FORMAT))

            case "DIRECTORY":
                # expected msg from client is DIRECTORY@ [path]
                if (os.path.exists(path)):
                    directory = os.scandir(path)
                    # send_data = "Files in directory " + path + ":\n"
                    for entry in directory:
                        if entry.is_dir():
                            send_data += "[Directory] " + entry.name + "\n"
                        elif entry.is_file():
                            send_data += "[File] " + entry.name + "\n"
                    conn.send(send_data.encode(FORMAT))
                else:
                    send_data = "FAIL@"
                    conn.send(send_data.encode(FORMAT))

            case "MKDIR":
                # expected msg from client is MKDIR@ [path]

                if (not os.path.exists(path)):
                    os.mkdir(path)
                    send_data = "DONE@"
                    conn.send(send_data.encode(FORMAT))
                else:
                    send_data = "FAIL@"
                    conn.send(send_data.encode(FORMAT))

            case "DELDIR":
                # expected msg from client is DELDIR@ [path]

                if (os.path.exists(path)):
                    shutil.rmtree(path, ignore_errors=True)
                    send_data = "DONE@"
                    conn.send(send_data.encode(FORMAT))
                else:
                    send_data = "FAIL@"
                    conn.send(send_data.encode(FORMAT))

    print(f"{addr} Connection Terminated")
    conn.close()


def main():
    print("Starting the server")
    server = socket.socket(socket.AF_INET,
                           socket.SOCK_STREAM)  # used IPV4 and TCP connection
    server.bind(ADDR)  # bind the address
    server.listen()  # start listening
    print(f"server is listening on {IP}: {PORT}")
    while True:
        conn, addr = server.accept()  # accept a connection from a client
        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr))  # assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
