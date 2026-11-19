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
    # print the connection address
    print(f"[NEW CONNECTION] {addr} connected.")

    # get the command and authentication from the message
    # first message is AUTHKEY@
    data = conn.recv(SIZE).decode(FORMAT)
    data = data.split("@")
    # check if the key is in the list of keys
    if (data[0] not in sha256keys):
        # if the key isn't present send a fail and disconnect client
        send_data = "AUTHFAIL@"
        conn.send(send_data.encode(FORMAT))
    else:
        # if the key is present send a success and wait for further commands
        send_data = "AUTHSUCCESS@"
        conn.send(send_data.encode(FORMAT))
        while True:
            # get further commands
            data = conn.recv(SIZE).decode(FORMAT)
            data = data.split("@")

            # print the command and path
            print(data)
            cmd = data[0]

            # check if the command has anything
            if cmd == "":
                # if it is nothing then stop listening for commands and disconnect
                break
            else:
                # if it's something then the path should also be present
                path = data[1]

            # run the command choosing from the list of commands
            match cmd:
                case "UPLOAD":
                    # expected msg from client is UPLOAD@ [server filepath]

                    if (os.path.isfile(path)):
                        # if the file exists send that it exists
                        print("File exists")
                        send_data = "EXISTS@"
                        conn.send(send_data.encode(FORMAT))

                        # receive response either OVRW@ for overwrite or NO@ for no
                        data = conn.recv(SIZE).decode(FORMAT)
                        data = data.split("@")
                        if (data[0] == "OVRW"):

                            # after the client receives RDYRECV it should start sending the file
                            send_data = "RDYRECV@"
                            conn.send(send_data.encode(FORMAT))

                            # file reciving and writing function
                            getFile(conn, path)

                            # sending DONE when done
                            send_data = "DONE@"
                            conn.send(send_data.encode(FORMAT))

                        elif (data[0] == "NO"):
                            # if the file shouldn't be overwritten then send done for client to know there wasn't an error
                            send_data = "DONE@"
                            conn.send(send_data.encode(FORMAT))

                    # if there's a file where the directory should go
                    elif (os.path.isdir(path)):
                        # send a fail and print that a directory exists
                        print("Directory exists at path")
                        send_data = "FAIL@"
                        conn.send(send_data.encode(FORMAT))

                    # if there's nothing where the file should go
                    else:
                        # tell client that the server is ready
                        send_data = "RDYRECV@"
                        conn.send(send_data.encode(FORMAT))

                        # and call file writing and receiving function
                        getFile(conn, path)

                        # send a done when done
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))

                case "DELETE":
                    # expected msg from client is DELETE@ [server filepath]

                    # check if it's a file or directory or nothing
                    if (os.path.isfile(path)):
                        # remove the file if it's a file
                        os.remove(path)

                        # send done when done
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))
                    elif (os.path.isdir(path)):
                        # remove the directory tree if it's a directory
                        shutil.rmtree(path, ignore_errors=True)

                        # send done when done
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))
                    else:
                        # if it's nothing then send that it does not exist
                        send_data = "DNE@"
                        conn.send(send_data.encode(FORMAT))

                case "DOWNLOAD":
                    # expected msg from client is DOWNLOAD@[server filepath]@[file offset for partial downloads]

                    # if the file doesn't exist
                    if not os.path.exists(path):
                        # send that it doesn't exist and close connection
                        Response = "DNE@"
                        conn.send(Response.encode(FORMAT))
                        break

                    # otherwise send the filesize to the client
                    FileSize = os.path.getsize(path)
                    Response = f"SIZE@{FileSize}"
                    conn.send(Response.encode(FORMAT))

                    # wait for the client to send a ready message
                    # since the message itself isn't important it isn't saved
                    conn.recv(SIZE).decode(FORMAT)

                    # set the start pos to the download offset from client
                    StartPos = int(data[2])

                    # record start time for file send
                    StartTime = time.time_ns()

                    # open the requested file
                    with open(path, "rb") as File:
                        # skip to the offset of the file
                        File.seek(StartPos)

                        # read in 1024 byte chunks
                        Text = File.read(1024)

                        # send in 1024 byte chunks until it reaches the end
                        while Text != b"":
                            conn.send(Text)
                            Text = File.read(1024)

                    # record the ending time for the file send
                    EndTime = time.time_ns()

                    # create and connect a socket to the module
                    module = socket.socket(socket.AF_INET,
                                           socket.SOCK_STREAM)
                    module.connect(("localhost", PORT+1))

                    # calculate the transfer speed
                    MBps = (FileSize/1000000)/((EndTime-StartTime)/1000000000)
                    # get the file name
                    filename = path.split("/")[-1]

                    # send the type of transfer, transfer speed and time of transfer to the module
                    module.send(("DOWNLOAD@"+str(MBps)+"@"+str((EndTime-StartTime)/1000000000)+"@"+filename).encode(FORMAT))

                    # disconnect from the module
                    module.close()

                    # disconnect from the client
                    break

                case "DIRECTORY":
                    # expected msg from client is DIRECTORY@ [path]

                    # gets the contents of the path
                    directory = os.scandir(path)

                    # initialize the message variable
                    send_data = ""

                    # for each entry in the path
                    for entry in directory:
                        # if it's a directory
                        if entry.is_dir():
                            # add to the message the directory's name and that it's a directory
                            send_data += "[Directory] " + entry.name + "\n"
                        # otherwise if it's a file
                        elif entry.is_file():
                            # add to the message the filename and that it's a file
                            send_data += "[File] " + entry.name + "\n"
                        # if it's neither a file or directory it does nothing

                    # if there are no files or directories in the path
                    if send_data == "":
                        # add to the message that the file is empty
                        send_data = "EMPTY."

                    # send the message
                    conn.send(send_data.encode(FORMAT))

                case "MKDIR":
                    # expected msg from client is MKDIR@ [path]

                    # if there's nothing at the path
                    if (not os.path.exists(path)):
                        # make the directory
                        os.mkdir(path)

                        # send done
                        send_data = "DONE@"
                        conn.send(send_data.encode(FORMAT))
                    else:
                        # otherwise send a fail since the path is full
                        send_data = "FAIL@"
                        conn.send(send_data.encode(FORMAT))

    print(f"{addr} disconnected")
    conn.close()


def main():
    # start server
    print("Starting the server")
    # check if there isn't a ./Files directory
    if (not os.path.isdir("./Files")):
        # attempt to make the files and if it fails throw a error and quit
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
