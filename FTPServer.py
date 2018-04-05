import sys
import socket
import random
import os
import platform


OS = platform.system()
BytesRcvd = 0

def carry_around_add(a, b):
    c = a + b
    d = (c & 0xffff) + (c >> 16)
    return d

def validate_chcksum(app_data,chcksum):                     #To generate and sum 16-bit words from application data and compare it with the received checksum
    word_sum = 0
    for idx in range(0,len(app_data),2):
        if app_data[idx] == app_data[len(app_data)-1]:
            word = (ord(app_data[idx])<<8)
        else:
            word = (ord(app_data[idx])<<8) + ord(app_data[idx+1])
        word_sum = carry_around_add(word_sum,word)
        word_sum = word_sum & 0xffff
    if (word_sum ^ int(chcksum,2)) == 0xffff:
        return False
    else:
        return True
    

def main():

    global BytesRcvd
    
    hostname = socket.gethostbyname(socket.gethostname())
    wd = os.getcwd()
    if OS == "Windows":
        directory = wd + "\IP_Project2"
    else:
        directory = wd + "/IP_Project2"
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.chdir(directory)
    
    InputArgs = raw_input("\nEnter prompt to invoke the server\n")
    args = InputArgs.split(' ')
    serverport = int(args[1])
    filename = args[2] #+ ".txt"    
    PcktLoss_Prob = float(args[3])

    ServerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ServerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    ServerSock.settimeout(60)
    server_address = ('',serverport)
    print "\nStarting up SERVER on %s port %s" %(server_address)
    ServerSock.bind(server_address)

    ACKheadrfld = "0000000000000000"
    ACKindicator = "1010101010101010"
    FinalSgmntIndctr = "1111111111111111"
    seqnum = 0

    fptr = open(filename,"wb")
        
    while True:
        try:
            print "\n\nWaiting to receive message..."
            data, client_address = ServerSock.recvfrom(2048)
            print "\nReceived %s bytes from %s" %(len(data), client_address)
            msg = str.split(data,"(%^&***)")
            SeqNumRcvd = msg[1]
            ChckSum = msg[2]
            FileData = msg[3]
            rnum = random.uniform(0,1)
            if (rnum <= PcktLoss_Prob):
                print "\nPacket with sequence number %s is LOST!" %(int(SeqNumRcvd,2))
            elif (rnum > PcktLoss_Prob):
                IsCorrupt = validate_chcksum(FileData,ChckSum)
                if (IsCorrupt == False):
                    print "\nReceived packet with sequence number %s is not corrupt..." %(int(SeqNumRcvd,2))
                    if (SeqNumRcvd == '{0:032b}'.format(seqnum)):
                        print "\nReceived packet is in-sequence...sending ACK!"
                        ACKmsg = ACKindicator+"(%^&***)"+SeqNumRcvd+"(%^&***)"+ACKheadrfld
                        ServerSock.sendto(ACKmsg,client_address)
                        print "\nWriting data to file..."
                        #fptr = open(filename,"a+")
                        fptr.write(FileData)
                        #fptr.close()
                        if msg[0] == FinalSgmntIndctr:
                            fptr.close()
                            print "\nFile has been transferred successfully!"
                            break
                        BytesRcvd = len(msg[3])
                        seqnum += BytesRcvd
                    else:
                        print "\nReceived packet is out-of-order!"
                        print "\nSending ACK for previous in-sequence packet..."
                        ACKmsg = ACKindicator+"(%^&***)"+'{0:032b}'.format(seqnum-BytesRcvd)+"(%^&***)"+ACKheadrfld
                        ServerSock.sendto(ACKmsg,client_address)
                else:
                    print "\nReceived packet with sequence number %s is corrupt..." %(int(SeqNumRcvd,2))
                    print "\nReceived packet is discarded!"    
        except KeyboardInterrupt:
            print "\nCTRL C was pressed"
            break
        except Exception as e:
            print e
            break
               
                    
if __name__ == '__main__':
    main()
                    
                    
            
            
            
                    
