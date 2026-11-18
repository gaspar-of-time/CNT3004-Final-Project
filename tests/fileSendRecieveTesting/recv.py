import os
import socket


# IP = "192.168.1.101" #"localhost"
IP = "localhost"
PORT = 1738
ADDR = (IP, PORT)
SIZE = 1024   # byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"


def main():

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    getFile(client, "./recv/test.txt")

    print("Disconnected from the server.")
    client.close()  # close the connection


def getFile(socket, path):
    if (os.path.exists(path)):
        response = input("File exists, do you want to overwrite? Y/N:")
        if (response == "Y" or "y" or "yes" or "YES" or "Yes"):

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
    else:

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


if __name__ == "__main__":
    main()
