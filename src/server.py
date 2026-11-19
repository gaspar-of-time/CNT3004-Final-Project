#!/usr/bin/python
import os
import socket
import threading
import shutil
import time

IP = "0.0.0.0"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
# password is "thisisapassword" and "thisisanotherpassword" respectively
sha256keys = ["a8d20c7aa37322429826e1f3cfabb08bb02d2b2bc13c12b2272cc23ff4389692", "000614845099a5f44c51c8614f3f7a7ab01b2f766edf759bc055b41a347dba7e"]


def getFile(socket, path):
    # overwriting file at path
    f = open(path, "wb")
    f.write(b'')

    # opening file with append
    f = open(path, "ab")
    test = True

    # append data to file until done
    print("Writing File")
    while (test != b''):
        test = socket.recv(SIZE)
        f.write(test)
    f.close()
    print("Done Writing File")


# to handle the clients
def handle_client(conn, addr):

    print(f"[NEW CONNECTION] {addr} connected.")

    data = conn.recv(SIZE).decode(FORMAT)
    data = data.split("@")
    if (data[0] not in sha256keys):
        send_data = "AUTHFAIL@"
        conn.send(send_data.encode(FORMAT))
    else:
        send_data = "AUTHSUCCESS@"
        conn.send(send_data.encode(FORMAT))
        while True:
            data = conn.recv(SIZE).decode(FORMAT)
            data = data.split("@")
            print(data)
            cmd = data[0]
            if cmd == "":
                break
            else:
                path = data[1]
            match cmd:
                case "UPLOAD":
                    # expected msg from client is UPLOAD@ [server filepath]

                    if (os.path.isfile(path)):
                        # if the file exists send that it exists
                        print("File exists")
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
                    elif (os.path.isdir(path)):
                        print("Directory exists at path")
                        send_data = "FAIL@"
                        conn.send(send_data.encode(FORMAT))
                    else:
                        print("rsy")
                        send_data = "RDYRECV@"
                        conn.send(send_data.encode(FORMAT))
                        getFile(conn, path)
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))

                case "DELETE":
                    # expected msg from client is DELETE@ [server filepath]

                    if (os.path.isfile(path)):
                        os.remove(path)
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))
                    elif (os.path.isdir(path)):
                        shutil.rmtree(path, ignore_errors=True)
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))
                    else:
                        send_data = "DNE@"
                        conn.send(send_data.encode(FORMAT))

                case "DOWNLOAD":
                    # expected msg from client is DOWNLOAD@ [server filepath]

                    # data = conn.recv(SIZE).decode(FORMAT)
                    # data = data.split("@")
                    if not os.path.exists(path):
                        Response = "DNE@"
                        conn.send(Response.encode(FORMAT))
                        break
                    FileSize = os.path.getsize(path)
                    Response = f"SIZE@{FileSize}"
                    conn.send(Response.encode(FORMAT))
                    StartPos = int(data[2])
                    # StartTime for upload speed.
                    StartTime = time.time_ns()
                    with open(path, "rb") as File:
                        File.seek(StartPos)
                        Text = File.read(1024)
                        while Text != b"":
                            conn.send(Text)
                            Text = File.read(1024)
                    EndTime = time.time_ns()
                    module = socket.socket(socket.AF_INET,
                                           socket.SOCK_STREAM)
                    module.connect(("localhost", PORT+1))
                    MBps = (FileSize/1000000)/((EndTime-StartTime)/1000000000)
                    filename = path.split("/")[-1]
                    module.send(("DOWNLOAD@"+str(MBps)+"@"+str((EndTime-StartTime)/1000000000)+"@"+filename).encode(FORMAT))
                    module.close()
                    break
                    # send_data = "DONE@"
                    # conn.send(send_data.encode(FORMAT))

                case "DIRECTORY":
                    # expected msg from client is DIRECTORY@ [path]

                    directory = os.scandir(path)
                    send_data = ""  # + path + ":\n"
                    for entry in directory:
                        if entry.is_dir():
                            send_data += "[Directory] " + entry.name + "\n"
                        elif entry.is_file():
                            send_data += "[File] " + entry.name + "\n"
                    if send_data == "":
                        send_data = "EMPTY."
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

    print(f"{addr} disconnected")
    conn.close()


def main():
    print("Starting the server")
    if (not os.path.isdir("./Files")):
        try:
            os.mkdir("./Files")
        except:
            print("Unable to create files directory.\nTerminating server.")
            quit()
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
