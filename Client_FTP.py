
from socket import *
import time
import os
import platform


OS = platform.system()
server = []
server_tuple = []
estimate_servers = 0
directory = ''
BytesRead = 0
timeout_val = 0.5

def carry_around_add(a, b):
    c = a + b
    d = (c & 0xffff) + (c >> 16)
    return d

def Generate_checksum(msg):  
    s = 0
    try:
        for i in range(0, len(msg), 2):
            if msg[i] == msg[len(msg)-1]:
                w = (ord(msg[i]) << 8)
            else:
                w = (ord(msg[i]) << 8) + ord(msg[i+1])
            s = carry_around_add(s, w)
        return ~s & 0xffff
    except IndexError as e:
        print e
        

def SAW(seq_no_bin,segment,LastSegmntFlg,clientSocket):
    
    global server
    global ack
    global server_tuple
    global estimate_servers
    global timeout_val
    
    checksum_dec = Generate_checksum(segment)
    checksum_bin = '{0:016b}'.format(checksum_dec)
    if LastSegmntFlg == True:
        data_indctr_field = '1111111111111111'
    else:
        data_indctr_field = '0101010101010101'
    header = data_indctr_field+"(%^&***)"+seq_no_bin+"(%^&***)"+checksum_bin
    Packet_tosend = header+"(%^&***)"+segment
    i = 0
    while i < estimate_servers:
        clientSocket.sendto(Packet_tosend,(server_tuple[i]))
        i = i + 1
    j = 0
    ack = []
    start_time = time.time()
    while j < estimate_servers:
        try:
            message, addr = clientSocket.recvfrom(1024)
            time_elapsed = time.time() - start_time
            clientSocket.settimeout(timeout_val - time_elapsed)
            message_split = message.split('(%^&***)')
            if message_split[0] == '1010101010101010':
                ack.append(addr)
                j = j + 1
        except timeout:
            clientSocket.settimeout(timeout_val)
            break
    server_set = set(server_tuple)
    ack_set = set(ack)
    difference = server_set.union(ack_set) - server_set.intersection(ack_set)
    left_out = list(difference)
    if not left_out:
        return
    else:
        while len(left_out) != 0:
            print "\nTimeout occured for packet with sequence number %d" %(int(seq_no_bin,2))
            print "\nServers that didn't respond with an ACK: " + str(left_out)
            ServrsLeft = len(left_out)
            i = 0
            while i < ServrsLeft:
                clientSocket.sendto(Packet_tosend,(left_out[i]))
                i = i + 1
            j = 0
            ack_new = []
            start_time = time.time()
            while j < ServrsLeft:
                try:
                    message, add = clientSocket.recvfrom(1024)
                    time_elapsed = time.time() - start_time
                    clientSocket.settimeout(timeout_val - time_elapsed)
                    message_split = message.split('(%^&***)')
                    if message_split[0] == '1010101010101010':
                        ack_new.append(add)
                        j = j + 1
                except timeout:
                    clientSocket.settimeout(timeout_val)
                    break
            left_out_set = set(left_out)
            ack_new_set = set(ack_new)
            difference = left_out_set.union(ack_new_set) - left_out_set.intersection(ack_new_set)
            left_out = list(difference)
        return
        

def rdt_send(filename,MSS,serverport):

    global directory
    global BytesRead
    global timeout_val
    
    seq_no = 0
    in_file = open(filename, 'rb+')
    FileContent = True
    LastSegmntFlg = False
    in_file.seek(0,2)
    EOF = in_file.tell()
    in_file.seek(0,0)
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.settimeout(timeout_val)
    FileTrnsfr_StartTime = time.time()
    while FileContent == True:
            seq_no = seq_no + BytesRead
            seq_no_bin = '{0:032b}'.format(seq_no)
            segment = in_file.read(MSS)
            BytesRead = len(segment)
            if in_file.tell() == EOF:
                LastSegmntFlg = True
                FileContent = False
            SAW(seq_no_bin,segment,LastSegmntFlg,clientSocket)
    FileTrnsfr_EndTime = time.time()
    if FileContent == False and LastSegmntFlg == True:
        Ttl_FileTrnsfr_Time = FileTrnsfr_EndTime - FileTrnsfr_StartTime
        os.chdir(directory)
        fptr = open("Timer.txt","a")
        fptr.write(str(Ttl_FileTrnsfr_Time))
        fptr.close()
        print "\nFile successfully sent to all receivers in %s sec" %(str(Ttl_FileTrnsfr_Time))


def main ():

    global estimate_servers
    global server
    global server_tuple
    global directory

    wd = os.getcwd()
    if OS == "Windows":
        directory = wd + "\IP_Project2"
    else:
        directory = wd + "/IP_Project2"
    if not os.path.exists(directory):
        os.makedirs(directory)
    #os.chdir(directory)
    try:
        prompt = raw_input("\nEnter the prompt to invoke the client\n")
        args = prompt.split(' ')
        NumOfArgs = len(args)
        estimate_servers = NumOfArgs - 4
        i = 1
        while i <= estimate_servers:
            server.append(args[i])
            i = i + 1
        serverport = args[i]
        serverport = int(serverport)
        filename = args[i+1] #+ ".txt"
        MSS = args[i+2]
        MSS = int(MSS)
        try:
            file_size = os.path.getsize(filename) 
        except Exception as e:
            print e
        i = 0
        while i < estimate_servers:
            server_tuple.append((server[i],serverport))
            i = i + 1
        
        os.chdir(directory)
        fptr = open("Timer.txt","a")
        #fptr.write("\nFile Size(Bytes)\tNumOfReceivers\tMSS(Bytes)\tFile Transfer Time(sec)")
        fptr.write("\n"+str(file_size)+"\t\t\t"+str(estimate_servers)+"\t\t"+str(MSS)+"\t\t")
        fptr.close()
        os.chdir("..")
                          
        rdt_send(filename,MSS,serverport)
    except KeyboardInterrupt as e:
        print "\nCTRL-C was pressed!"
    except Exception as e:
        print e


if __name__ == '__main__':
    main()
