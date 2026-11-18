import sys
from PySide6 import QtCore, QtWidgets, QtGui
import socket
import os
import hashlib
import time

# Get the hostname and IP of the device running the server.
HostName = socket.gethostname();
IP = socket.gethostbyname(HostName)
print(HostName, IP);

# Code to make a section for QT that's a horizontal box. 
def MakeSection(*Args):
    Section = QtWidgets.QWidget();
    Section.Layout = QtWidgets.QHBoxLayout(Section);
    for Arg in Args:
        Section.Layout.addWidget(Arg);
    Section.setProperty("class", "Section");
    Section.Layout.setContentsMargins(0, 0, 0, 0);
    return Section;

# Simple conversion.
def GetRateMBps(Bytes, TimeNS):
    MegaBytes = Bytes/1000000;
    Seconds = TimeNS/1000000000;
    if Seconds == 0:
        return "Too fast to measure lowkey.";
    return MegaBytes/Seconds;

# The main class with everything in it pretty much.
class MainWidget(QtWidgets.QWidget):
    def __init__(Self):
        super().__init__();
        # Let the user edit the IP to send the message to.
        Self.IP = QtWidgets.QLineEdit();
        
        Self.Socket = None;
        
        # Create a bunch of buttons and text lines and stuff and such and things.
        Self.QuitButton = QtWidgets.QPushButton("Quit.");
        Self.PrintButton = QtWidgets.QPushButton("Print.");
        Self.SendButton = QtWidgets.QPushButton("Send.");
        Self.YourIP = QtWidgets.QLabel("Your IP : " + str(IP),
                                       alignment = QtCore.Qt.AlignCenter);
        Self.FileSelect = QtWidgets.QPushButton("Select File?");
        Self.FileDialog = QtWidgets.QFileDialog();
        Self.File = None;
        Self.IPText = QtWidgets.QLabel("Server IP : ");
        Self.FileText = QtWidgets.QLabel("Selected File : ");
        Self.ServerFileText = QtWidgets.QLabel("File Path on Server : ")
        Self.ServerFileName = QtWidgets.QLineEdit();
        Self.PortText = QtWidgets.QLabel("Server Port : ");
        Self.Port = QtWidgets.QLineEdit();
        Self.KillButton = QtWidgets.QPushButton("Delete File at Path");
        Self.DownloadButton = QtWidgets.QPushButton("Download File at Path");
        Self.ServerContentButton = QtWidgets.QPushButton("View Content.");
        Self.PasswordPrompt = QtWidgets.QLabel("Password : ");
        Self.PasswordInput = QtWidgets.QLineEdit();

        # Let the buttons do what they're supposed to.
        Self.PrintButton.clicked.connect(Self.Print)
        Self.QuitButton.clicked.connect(Self.Quit);
        Self.SendButton.clicked.connect(Self.Send);
        Self.FileSelect.clicked.connect(Self.ShowFileDialog);
        Self.KillButton.clicked.connect(Self.Kill);
        Self.DownloadButton.clicked.connect(Self.Download);
        Self.ServerContentButton.clicked.connect(Self.SelectServerFile);

        # Layout.
        Self.Layout = QtWidgets.QVBoxLayout(Self);

        Container = QtWidgets.QWidget();
        Container.Layout = QtWidgets.QVBoxLayout(Container);
        Container.Layout.addWidget(Self.QuitButton);
        Container.Layout.addWidget(Self.YourIP);

        Container.Layout.addWidget(Self.FileSelect);
        Container.Layout.addWidget(Self.FileText);
        
        ServerFileSection = MakeSection(Self.ServerFileText, Self.ServerFileName, Self.ServerContentButton);
        Container.Layout.addWidget(ServerFileSection);

        #IPSection = QtWidgets.QWidget();
        #IPSection.IPLayout = QtWidgets.QHBoxLayout(IPSection);
        #IPSection.IPLayout.addWidget(Self.IPText);
        #IPSection.IPLayout.addWidget(Self.IP);
        IPSection = MakeSection(Self.IPText, Self.IP);
        Container.Layout.addWidget(IPSection);
        
        PortSection = MakeSection(Self.PortText, Self.Port);
        Container.Layout.addWidget(PortSection);

        PortSection = QtWidgets
        
        PasswordSection = MakeSection(Self.PasswordPrompt, Self.PasswordInput);
        Container.Layout.addWidget(PasswordSection);

        Buttons = MakeSection(Self.SendButton, Self.DownloadButton, Self.KillButton);
        Container.Layout.addWidget(Buttons);
        Self.Layout.addWidget(Container);
        Container.setContentsMargins(20, 20, 20, 20)

    # Unused function that I used to test stuff.
    def Print(Self):
        print("IP :", Self.IP.text());
    
    # Connect to the IP and port. Since it's pretty much used for every feature, it's a function here. Also handles authentication.
    def Connect(Self):
        IP = Self.IP.text();
        Port = Self.Port.text();
        Self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        Self.Socket.settimeout(5);
        Self.Socket.connect((IP, int(Port)));
        Self.Socket.send(hashlib.sha256(Self.PasswordInput.text().encode()).hexdigest().encode());
        Msg = Self.GetMessage();
        if Msg == "AUTHFAIL":
            raise(Exception("Authentication Failed."));
    
    # Send function that's pretty much a wrapper.
    def Send(Self):
        #IP = Self.IP.text();
        #Port = Self.Port.text();
        #print("Sending to", Self.IP.text() + ":" + Self.Port.text());
        try:
            Self.DoSend();
        except Exception as E:
            Self.OopsError(E);
    
    # Create a popup on screen.
    def Popup(Self, Text):
        Dialog = QtWidgets.QDialog(Self);
        Dialog.Layout = QtWidgets.QVBoxLayout(Dialog);
        Dialog.Layout.addWidget(QtWidgets.QLabel(Text, alignment = QtCore.Qt.AlignCenter));
        Dialog.exec();
    
    # Error handling.
    def OopsError(Self, E):
        if Self.Socket:
            Self.Socket.close();
            Self.Socket = None;
        Err = str(E);
        Self.Popup("Error! Check all fields!\n\n" + Err);
    
    # This converts a response from the server into a list of items and what they are.
    def ReadDir(Self, Response):
        Out = [];
        Responses = Response.split("\n");
        if "EMPTY" in Response[0:5]:
            return Out;
        for i in range(len(Responses)-1):
            X = Responses[i];
            #print(X);
            Things = X.split(" ", 1);
            Out.append((Things[0], Things[1]));
        #print(Out);
        return Out;

    # Gets a message from the server and returns the important part (Portion).
    def GetMessage(Self, Portion=[0]):
        #print("Here.");
        Msg = Self.Socket.recv(1024).decode().split("@");
        if len(Portion) == 1:
            return Msg[Portion[0]];
        else:
            Out = [Msg[X] for X in Portion]
            return Out;
    
    # Send helper function.
    def DoSend(Self):
        if not Self.File:
            raise(Exception("No file selected."));
        Self.Connect();
        # Size of file for MB/s later.
        SizeBytes = os.path.getsize(Self.File);
        
        # FileName here is the name of the file on the server, not the file on the host.
        # As in, where the file will be sent.
        FileName = Self.ServerFileName.text();
        
        # If no filename set, just set it to be the name of the file on the host.
        if FileName == "":
            NewFileName = Self.File.split("/")[-1];
        else: 
            NewFileName = FileName.split("/")[-1];
        #print("New : ", NewFileName, "Oth : ", Self.File);
        
        # This section pretty much just makes sure that the desired path exists, and if it doesn't, makes it.
        Paths = FileName.split("/");
        EndOfPaths = len(Paths);
        FullPath = "./Files/";
        Self.Socket.send(f"DIRECTORY@{FullPath}".encode());
        Dirs = Self.GetMessage();
        Read = Self.ReadDir(Dirs);
        for i in range(EndOfPaths-1):
            #print(i);
            Path = Paths[i]
            DirExists = 0;
            for Var in Read:
                if Var[1] == Path:
                    if Var[0] != "[Directory]":
                        raise(Exception("One of the directories in the path is actually a file."));
                    else:
                        DirExists = 1;
                        break;
            FullPath = (FullPath + Path + "/").strip();
            if not DirExists:
                    Self.Socket.send(f"MKDIR@{FullPath}".encode());
                    Response = Self.GetMessage();
                    #print(Response);
                    if Response == "FAIL":
                        raise(Exception("Failed to create directory."));
            Self.Socket.send(f"DIRECTORY@{FullPath}".encode());
            Dirs = Self.GetMessage();
            #print(Dirs);
            Read = Self.ReadDir(Dirs);
            #print(Read);
            #print(FullPath);
        print(FullPath + NewFileName);
        # Say, ayo Server bro let me upload this.
        Self.Socket.send(f"UPLOAD@{FullPath + NewFileName}".encode());
        Response = Self.GetMessage();
        #print(Response);
        # Check if the Server is chill or not.
        if Response == "EXISTS":
            # If file already exists (and isn't a directory) ask user to overwrite or not.
            Overwrite = Self.CheckOverwrite()
            if Overwrite:
                Self.Socket.send("OVRW".encode());
                Response = Self.GetMessage();
            else:
                Self.Socket.send("NO".encode());
                print("Not overwriting.");
                Self.Socket.close();
                return;
        elif Response == "FAIL":
            # This means that it's a directory so the server says no :(.
            raise(Exception("Selected server location is directory."))
        #print(Response);
        # StartTime for upload speed.
        StartTime = time.time_ns();
        # Check if server is ready.
        if Response == "RDYRECV":
            print("Sending.");
            with open(Self.File, "rb") as File:
                FileText = File.read(1024);
                while FileText != b"":    
                    Self.Socket.send(FileText)
                    FileText = File.read(1024);
        print("File sent.");
        # EndTime for upload speed.
        EndTime = time.time_ns();
        # Print speed to console.
        print("MB/s :", GetRateMBps(SizeBytes, EndTime-StartTime));
        # Close socket.
        Self.Socket.close();
        return;
    
    # This is pretty much just complicated because of the UI, but it checks if the user wants to overwrite the file or not.
    def CheckOverwrite(Self):
        class Overwrite():
            def __init__(Self):
                Self.Overwrite = False;
                Self.Curr = QtWidgets.QWidget();
                Self.Curr.Text = QtWidgets.QLabel("File Exists. Overwrite?");
                Self.Curr.Layout = QtWidgets.QVBoxLayout(Self.Curr);
                Self.Curr.Yes = QtWidgets.QPushButton("Yes.");
                Self.Curr.No = QtWidgets.QPushButton("No.");
            
                Self.Curr.Layout.addWidget(Self.Curr.Text);
                YesNo = MakeSection(Self.Curr.Yes, Self.Curr.No);
                Self.Curr.Layout.addWidget(YesNo);
                
                Self.Curr.Yes.clicked.connect(Self.Y);
                Self.Curr.No.clicked.connect(Self.N)

            def Y(Self):
                Self.Overwrite = True;
                Self.Curr.deleteLater();
            
            def N(Self):
                Self.Overwrite = False;
                Self.Curr.deleteLater();
        
        O = Overwrite();

        Loop = QtCore.QEventLoop();
        O.Curr.show();
        O.Curr.destroyed.connect(Loop.quit);
        Loop.exec();
        #print(O.Overwrite);
        return O.Overwrite;

    # Funny function that calls delete.
    def Kill(Self):
        try:
            Self.DoKill();
        except Exception as E:
            Self.OopsError(E);

    # The actual deletion function.
    def DoKill(Self):
        # Really simple, just send a message to kill the file to the server.
        # Would probably make sense to make sure the user didn't misclick with an "are you sure" or whatever, but whatever.
        FileToKill = Self.ServerFileName.text();
        if Self.ServerFileName.text() == "":
            raise(Exception("No file to kill set."));
        Self.Connect();
        Self.Socket.send(f"DELETE@./Files/{FileToKill}".encode());
        Response = Self.GetMessage();
        Self.Popup(Response);
        Self.Socket.close();

    # The download wrapper.
    def Download(Self):
        try:
            Self.DoDownload();
        except Exception as E:
            Self.OopsError(E);
   
    # Download.
    def DoDownload(Self):
        
        Self.Connect();
        
        # Open a prompt for the user to select the file location to download to.
        FileDialogDownload = QtWidgets.QFileDialog();
        Loop = QtCore.QEventLoop();
        FileDialogDownload.fileSelected.connect(Self.SetDownloadFileLocation);
        FileDialogDownload.fileSelected.connect(Loop.quit)
        FileDialogDownload.show();
        Loop.exec();
        
        DownloadPath = Self.DownloadFileLocation;
        Path = DownloadPath.split("/");

        FileDownload = Self.ServerFileName.text();
        if Self.ServerFileName.text() == "":
            raise(Exception("No download file set."));
        
        # Temp folder for if file installs get interrupted.
        Temp = "./.TEMP/"
        if not os.path.exists(Temp):
            os.mkdir(Temp);

        Loc = "./Files/";
        if not os.path.exists(Loc):
            os.mkdir(Loc);
        try:
            Start = Path.index("Files");
        except:
            # I don't want to accidentally overwrite an important file.
            raise(Exception("For safety purposes, files may only\nbe saved in the Files folder within the\ndirectory the script is in."));
        # Make directories if needed, and get the file location relative to Files.
        for i in range(Start+1, len(Path)-1):
            CurPath = Path[i];
            Loc += CurPath + "/";
            if not os.path.exists(Loc):
                os.mkdir(Loc);
        Loc += Path[-1];
        TempLoc = Temp + Path[-1];
        
        # Check if file download was in progress.
        Pos = 0;
        TempFile = False;
        if os.path.exists(Loc) and os.path.exists(TempLoc):
            Pos = os.path.getsize(Loc);
            TempFile = True;

        # Request the file.
        Self.Socket.send(f"DOWNLOAD@./Files/{FileDownload}@{Pos}".encode());
        
        Responses = Self.GetMessage([0, 1]);
        if Responses[0] == "DNE":
            raise(Exception("Server file does not exist."));

        # Get the size of the file.
        EndSize = int(Responses[1]);
        
        # Create temp file if it doesn't exist.
        if not os.path.exists(TempLoc):
            with open(TempLoc, "x") as File:
                print("Temp file created.");
        
        # Start time for download speed.
        StartTime = time.time_ns();
        
        Response = Self.Socket.recv(1024);
        Pos += len(Response);
        
        # Set type based on whether the file download is in progress.
        Type = "wb"
        if TempFile:
            Type = "ab"
        
        # Iterate through the responses until the entire file is downloaded, or the server responds a blank message for some other reason.
        with open(Loc, Type) as File:
            while Response != b"":
                File.write(Response);
                Response = Self.Socket.recv(1024);
                #print(len(Response));
                Pos += len(Response);
        Self.Socket.close()
        EndTime = time.time_ns();
        # Speed.
        print("MB/s :", GetRateMBps(Pos, EndTime - StartTime));
        # Compare the size of the full file to what was actually downloaded. If the entire thing wan't downloaded, inform the user and store the temporary file.
        if EndSize > Pos:
            Self.Popup("File NOT successfully downloaded.");
        else:
            Self.Popup("File downloaded successfully.");
            os.remove(TempLoc);
    
    # Thing for thing.
    def SetDownloadFileLocation(Self, File):
        Self.DownloadFileLocation = File;
    
    # Show file dialog for thing.
    def ShowFileDialog(Self):
        Self.FileDialog.show();
        Self.FileDialog.fileSelected.connect(Self.SetFile);
    
    # Set the file text to be whatever was selected by the uh file dialog I think.
    def SetFile(Self, File):
        Self.File = File;
        Self.FileText.setText(f"Selected File : {File}")
    
    # Select the server file.
    def SelectServerFile(Self):
        try:
            Self.ServerFileSelector();
        except Exception as E:
            Self.OopsError(E);
    
    # Actually select the server file.
    def ServerFileSelector(Self):
        # Make widget for selecting the server file and then get the list of files from the server.
        Self.ServerFileWidge = QtWidgets.QWidget();
        Self.Connect()
        Self.FileList = QtWidgets.QListWidget();
        Self.CurrServerDir = "";
        Self.UpdateFileList();
        Self.ServerFileWidge.Layout = QtWidgets.QVBoxLayout(Self.ServerFileWidge);
        Self.ServerFileWidge.Layout.addWidget(Self.FileList);
        Access = QtWidgets.QPushButton("Access");
        Done = QtWidgets.QPushButton("Done");
        
        Access.clicked.connect(Self.ServerDirInteract);
        Done.clicked.connect(Self.KillWidge);
        
        Buttons = MakeSection(Access, Done)
        
        Self.ServerFileWidge.Layout.addWidget(Buttons);
        Self.ServerFileWidge.resize(200, 200);
        Loop = QtCore.QEventLoop();
        Self.ServerFileWidge.show();
        Self.ServerFileWidge.destroyed.connect(Loop.quit);
        Loop.exec();
        Self.Socket.close();
    
    # Update the files on the server file selector I made.
    def UpdateFileList(Self):
        Self.FileList.clear();
        Dir = "./Files/" + Self.CurrServerDir
        Self.Socket.send(("DIRECTORY@" + Dir).encode());
        Contents = Self.GetMessage();
        DirData = Self.ReadDir(Contents);
        Self.Types = [];
        # Add item to list thing, while also adding the type to the types array. Could add an icon for folder or file but I don't have any lowkey.
        for Item in DirData:
            Thing = QtWidgets.QListWidgetItem(Item[1]);
            Self.Types.append(Item[0]);
            Self.FileList.addItem(Thing);
    
    # Kill Widge.
    def KillWidge(Self):
        print("Killing Widge.");
        Self.ServerFileName.setText(Self.CurrServerDir);
        Self.ServerFileWidge.deleteLater();
    
    # This is the stuff for the interact button on the server file selector.
    def ServerDirInteract(Self):
        Item = Self.FileList.currentItem();
        # I lowkey don't think this is possible to occur but just in case, I have this.
        if Item == None:
            raise(Exception("No item selected."));
        Text = Item.text();
        Type = Self.Types[Self.FileList.currentRow()];
        # If directory, get the directory.
        if Type == "[Directory]":
            Self.CurrServerDir += Text + "/";
            Self.UpdateFileList();
        # Otherwise, just set the file text to be the file.
        elif Type == "[File]":
            Self.CurrServerDir += Text;
            Self.KillWidge()
    
    # Bye bye.
    def Quit(Self):
        sys.exit();

# Get the arguments passed.
Args = sys.argv[1:];

if __name__ == "__main__":
    # Setup the app.
    App = QtWidgets.QApplication([]);
    # Widget for widget maxxing.
    Widget = MainWidget();
    Widget.resize(200, 200);
    Widget.show();
    # Pretty much requested, so I threw in the ability to use system theming.
    if "--SystemDefaultTheming" not in Args:
        if os.path.exists("Style.qss"):
            # My style.
            with open("Style.qss", "r") as F:
                Style = F.read();
                App.setStyleSheet(Style);
    # Actually do the thing.
    App.exec();
