import sys
from PySide6 import QtCore, QtWidgets, QtGui
import socket
import os
import hashlib

HostName = socket.gethostname();
IP = socket.gethostbyname(HostName)
print(HostName, IP);

def MakeSection(*Args):
    Out = QtWidgets.QWidget();
    Out.Layout = QtWidgets.QHBoxLayout(Out);
    for Arg in Args:
        Out.Layout.addWidget(Arg);
    return Out;

class MainWidget(QtWidgets.QWidget):
    def __init__(Self):
        super().__init__();
        Self.IP = QtWidgets.QLineEdit();
        
        Self.Socket = None;

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

        Self.PrintButton.clicked.connect(Self.Print)
        Self.QuitButton.clicked.connect(Self.Quit);
        Self.SendButton.clicked.connect(Self.Send);
        Self.FileSelect.clicked.connect(Self.ShowFileDialog);
        Self.KillButton.clicked.connect(Self.Kill);
        Self.DownloadButton.clicked.connect(Self.Download);
        Self.ServerContentButton.clicked.connect(Self.SelectServerFile);

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

    def Print(Self):
        print("IP :", Self.IP.text());
    
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

    def Send(Self):
        #IP = Self.IP.text();
        #Port = Self.Port.text();
        #print("Sending to", Self.IP.text() + ":" + Self.Port.text());
        try:
            Self.DoSend();
        except Exception as E:
            Self.OopsError(E);

    def Popup(Self, Text):
        Dialog = QtWidgets.QDialog(Self);
        Dialog.Layout = QtWidgets.QVBoxLayout(Dialog);
        Dialog.Layout.addWidget(QtWidgets.QLabel(Text, alignment = QtCore.Qt.AlignCenter));
        Dialog.exec();

    def OopsError(Self, E):
        if Self.Socket:
            Self.Socket.close();
            Self.Socket = None;
        Err = str(E);
        Self.Popup("Error! Check all fields!\n\n" + Err);
    
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

    def GetMessage(Self, Portion=0):
        #print("Here.");
        Msg = Self.Socket.recv(1024).decode().split("@")[Portion];
        #print(Msg);
        return Msg;

    def DoSend(Self):
        if not Self.File:
            raise(Exception("No file selected."));
        Self.Connect();

        FileName = Self.ServerFileName.text();
        
        if FileName == "":
            NewFileName = Self.File.split("/")[-1];
        else: 
            NewFileName = FileName.split("/")[-1];
        print("New : ", NewFileName, "Oth : ", Self.File);
        
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
        Self.Socket.send(f"UPLOAD@{FullPath + NewFileName}".encode());
        Response = Self.GetMessage();
        #print(Response);
        if Response == "EXISTS":
            Overwrite = Self.CheckOverwrite()
            if Overwrite:
                Self.Socket.send("OVRW".encode());
                Response = Self.GetMessage();
            else:
                Self.Socket.send("NO".encode());
                print("Not overwriting.");
                Self.Socket.close();
                return;
        #print(Response);
        if Response == "RDYRECV":
            print("Sending.");
            with open(Self.File, "rb") as File:
                FileText = File.read(1024);
                while FileText != b"":    
                    Self.Socket.send(FileText)
                    FileText = File.read(1024);
        print("File sent.");
        Self.Socket.close();
        return;
    
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

    def Kill(Self):
        try:
            Self.DoKill();
        except Exception as E:
            Self.OopsError(E);

    def DoKill(Self):
        FileToKill = Self.ServerFileName.text();
        if Self.ServerFileName.text() == "":
            raise(Exception("No file to kill set."));
        Self.Connect();
        Self.Socket.send(f"DELETE@./Files/{FileToKill}".encode());
        Response = Self.GetMessage();
        Self.Popup(Response);
        Self.Socket.Close();

    def Download(Self):
        try:
            Self.DoDownload();
        except Exception as E:
            Self.OopsError(E);
   
    def DoDownload(Self):
        
        Self.Connect();

        FileDialogDownload = QtWidgets.QFileDialog();
        Loop = QtCore.QEventLoop();
        FileDialogDownload.fileSelected.connect(Self.SetDownloadFileLocation);
        FileDialogDownload.fileSelected.connect(Loop.quit)
        FileDialogDownload.show();
        Loop.exec();
        
        FileDownload = Self.ServerFileName.text();
        if Self.ServerFileName.text() == "":
            raise(Exception("No download file set."));
        Self.Socket.send(f"DOWNLOAD@./Files/{FileDownload}".encode());
        Response = Self.Socket.recv(1024);
        Loc = "./Files/";
        if not os.path.exists(Loc):
            os.mkdir(Loc);
        DownloadPath = Self.DownloadFileLocation;
        Path = DownloadPath.split("/");
        try:
            Start = Path.index("Files");
        except:
            raise(Exception("For safety purposes, files may only\nbe saved in the Files folder within the\ndirectory the script is in."));
        for i in range(Start+1, len(Path)-1):
            CurPath = Path[i];
            Loc += CurPath + "/";
            if not os.path.exists(Loc):
                os.mkdir(Loc);
        Loc += Path[-1]; 
        with open(Loc, "wb") as File:
            while Response != b"":
                File.write(Response);
                Response = Self.Socket.recv(1024);
        Self.Socket.close()
    
    def SetDownloadFileLocation(Self, File):
        Self.DownloadFileLocation = File;

    def ShowFileDialog(Self):
        Self.FileDialog.show();
        Self.FileDialog.fileSelected.connect(Self.SetFile);
    
    def SetFile(Self, File):
        Self.File = File;
        Self.FileText.setText(f"Selected File : {File}")

    def SelectServerFile(Self):
        try:
            Self.ServerFileSelector();
        except Exception as E:
            Self.OopsError(E);

    def ServerFileSelector(Self):
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

    def UpdateFileList(Self):
        Self.FileList.clear();
        Dir = "./Files/" + Self.CurrServerDir
        Self.Socket.send(("DIRECTORY@" + Dir).encode());
        Contents = Self.GetMessage();
        DirData = Self.ReadDir(Contents);
        Self.Types = [];
        for Item in DirData:
            Thing = QtWidgets.QListWidgetItem(Item[1]);
            Self.Types.append(Item[0]);
            Self.FileList.addItem(Thing);
    
    def KillWidge(Self):
        print("Killing Widge.");
        Self.ServerFileName.setText(Self.CurrServerDir);
        Self.ServerFileWidge.deleteLater();

    def ServerDirInteract(Self):
        Item = Self.FileList.currentItem();
        if Item == None:
            raise(Exception("No item selected."));
        Text = Item.text();
        Type = Self.Types[Self.FileList.currentRow()];
        if Type == "[Directory]":
            Self.CurrServerDir += Text + "/";
            Self.UpdateFileList();
        elif Type == "[File]":
            Self.CurrServerDir += Text;
            Self.KillWidge()

    def Quit(Self):
        sys.exit();

Args = sys.argv[1:];

if __name__ == "__main__":
    App = QtWidgets.QApplication([]);
    Widget = MainWidget();
    Widget.resize(200, 200);
    Widget.show();
    if "--SystemDefaultTheming" not in Args:
        with open("Style.qss", "r") as F:
            Style = F.read();
            App.setStyleSheet(Style);
    App.exec();
