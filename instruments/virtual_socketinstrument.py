import socket as sck
import threading
import time
import numpy as np


class VirtualSocketInstrument():
    def __init__(self, verbose = False):
        self.listen_addr = "0.0.0.0"
        self.listen_port = 0
        self.conn_ip = "127.0.0.1"
        self.hostname = "host"
        self.running = False
        self.verbose = verbose
        self.s = None

        # Commands dictionaries
        self.comms_dicts = {}
        self.comms_misc = {}
        self.comms_scpi = {}
        self.comms_root = {}

        # Misc commands
        self.comms_misc["close"] = self.close
        self.comms_misc["exit"] = self.close
        self.comms_misc["quit"] = self.close
        self.comms_dicts["scksrv"] = self.comms_misc

        # Basic SCPI functions
        self.comms_scpi["*cls"] = self.CLS
        self.comms_scpi["*ese"] = self.SET_ESE
        self.comms_scpi["*esr?"] = self.GET_ESR
        self.comms_scpi["*idn?"] = self.GET_IDN
        self.comms_scpi["*opc"] = self.SET_OPC
        self.comms_scpi["*opc?"] = self.GET_OPC
        self.comms_scpi["*opt?"] = self.GET_OPT
        self.comms_scpi["*psc"] = self.SET_PSC
        self.comms_scpi["*rcl"] = self.SET_RCL
        self.comms_scpi["*rst"] = self.RST
        self.comms_scpi["*sav"] = self.SET_SAV
        self.comms_scpi["*sre"] = self.SET_SRE
        self.comms_scpi["*stb?"] = self.GET_STB
        self.comms_scpi["*trg"] = self.TRG
        self.comms_scpi["*tst?"] = self.GET_TST
        self.comms_scpi["*wai"] = self.WAI
        self.comms_dicts["*"] = self.comms_scpi

        # Root commands
        self.comms_root["test?"] = self.test
        self.comms_dicts["root"] = self.comms_root
    
    def start(self, listen_ip="0.0.0.0", port=0):
        temp_s = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
        temp_s.connect(("1.1.1.1", 80))
        self.conn_ip = temp_s.getsockname()[0]
        temp_s.close()

        if port < 1024:
            port = np.random.randint(1024, 65536)

        self.s = sck.socket(sck.AF_INET, sck.SOCK_STREAM, sck.IPPROTO_TCP)
        self.s.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)
        self.hostname = sck.gethostname()
        self.s.bind((listen_ip, port))
        self.s.listen(16)
        self.listen_addr = listen_ip
        self.listen_port = port
        if self.verbose:
            print(f"Server initialized on host '{self.hostname}'. IP for connection is {self.conn_ip}. Listening on port {self.listen_port}...")

        self.running = True
        threading.Thread(target=self.mainLoop).start()
        
    def listen(self):
        conn, addr = self.s.accept()
        if self.verbose:
            print(f"Connection received from {addr}")
        return conn, addr
            
    def receive(self, conn):
        # Receive data
        data = conn.recv(1024000)
        resp = ""
        ok_comms = False
        if not data:
            return None
        
        # Parse data
        raw_comm = data.decode("Latin1").lower()
        raw_comm = raw_comm.replace("\r", "\n").replace("\n\n", "\n")
        raw_comms = raw_comm.split("\n")
        raw_comms = list(filter(None, raw_comms))
        
        for full_comm in raw_comms:
            # Separate categories
            cat_comm = full_comm.split(":")
            cats = []
            if len(cat_comm) > 1:
                cats = cat_comm[:-1]
                full_comm = cat_comm[-1]

            # Separate arguments
            comm = full_comm.split(" ")
            
            # SCPI commands
            if (len(cats) < 1) and (comm[0][0] == "*"):
                if comm[0] in self.comms_scpi:
                    if self.verbose:
                        print(f"Valid SCPI command received: {comm}")
                    if len(comm) > 1:
                        resp = self.comms_scpi[comm[0]](comm[1:])
                    else:
                        resp = self.comms_scpi[comm[0]]([])
                    if resp:
                        resp = f"{resp}\n"
                        if self.verbose:
                            print(f"Sending response: {resp}"[:100])
                        conn.sendall(resp.encode("Latin1"))
                    else:
                        resp = "1"
                else:
                    resp = "Error: Invalid SCPI command received."
                    if self.verbose:
                        print(resp)
            
            # Root commands
            elif (len(cats) < 1) and (comm[0] in self.comms_root):
                if self.verbose:
                    print(f"Valid command received: {comm}")
                if len(comm) > 1:
                    resp = self.comms_root[comm[0]](comm[1:])
                else:
                    resp = self.comms_root[comm[0]]([])
                if resp:
                    resp = f"{resp}\n"
                    if self.verbose:
                        print(f"Sending response: {resp}"[:100])
                    conn.sendall(resp.encode("Latin1"))
                else:
                    resp = "1"
            
            # Categorized commands
            elif (len(cats) > 0):
                branch = self.comms_dicts
                for i in range(len(cats)):
                    if cats[i] in branch:
                        branch = branch[cats[i]]
                    else:
                        resp = f"Error: Command {cats} {comm} not understood. It is invalid or incomplete."
                        if self.verbose:
                            print(resp)

                if comm[0] in branch:
                    if self.verbose:
                        print(f"Valid command received: {comm}")
                    if len(comm) > 1:
                        resp = branch[comm[0]](comm[1:])
                    else:
                        resp = branch[comm[0]]([])
                    if resp:
                        resp = f"{resp}\n"
                        if self.verbose:
                            print(f"Sending response: {resp}"[:100])
                        conn.sendall(resp.encode("Latin1"))
                    else:
                        resp = "1"
            # Invalid command
            else:
                resp = f"Error: Command {data.decode('Latin1')} not understood. It is invalid or incomplete."
                if self.verbose:
                    print(resp)

            ok_comms = ok_comms or bool(resp)
        
        return ok_comms
    
    def receiveLoop(self, conn, addr):
        while self.running:
            try:
                resp = self.receive(conn)
                if (not resp) or (resp is None):
                    break
            except:
                conn.close()
                if self.verbose:
                    print(f"Error communicating with client {addr}. Connection closed.")
                break

    def mainLoop(self):
        while self.running:
            try:
                conn, addr = self.listen()
                threading.Thread(target=self.receiveLoop, args=(conn, addr)).start()
            except:
                pass

    ### START OF SCPI FUNCTIONS ###
    def CLS(self, args):
        pass

    def SET_ESE(self, args):
        pass
    
    def GET_ESR(self, args):
        return "1"
    
    def GET_IDN(self, args):
        return "Unknown Instrument - No IDN set"
    
    def SET_OPC(self, args):
        pass
    
    def GET_OPC(self, args):
        return "1"
    
    def GET_OPT(self, args):
        return "1"
    
    def SET_PSC(self, args):
        pass
    
    def SET_RCL(self, args):
        pass
    
    def RST(self, args):
        pass
    
    def SET_SAV(self, args):
        pass
    
    def SET_SRE(self, args):
        pass
    
    def GET_STB(self, args):
        return "1"
    
    def TRG(self, args):
        pass
    
    def GET_TST(self, args):
        return "1"
    
    def WAI(self, args):
        pass
    
    ### END OF SCPI FUNCTIONS

    # Server close
    def close(self, args):
        self.running = False
        if self.s:
            self.s.close()

    # Root test function
    def test(self, args):
        return("Communication test successful!")

        

    