import sys
import os
import time
import threading
import socket

subnet='10.0.0.'
Iden='0'		# serial number of this node
K=0			# number of neighbors
ports=['0','0']		# list of neighbors
port_status_temp=[0,0]	# if neighbor links are up or down
port_status=[0,0]
switch=''		# corresponding switch of this node

M=0			# number of flows
flow_m=[]		# amount of available paths
flow_s=[]		# source of flows
flow_d=[]		# destination of flows
paths=[]		# available paths
next_hop=[]		# next hop of each path
last_hop=[]

routing=[]		# current routing path
active_links=set([])	# links in the network known to be available

def load_configuration():
    global K,ports,switch,Iden,M,flow_m,flow_s,paths,next_hop
    conf=open(sys.argv[1],'r')

    # read port information
    conf.readline()
    Iden=conf.readline().split()[0]
    switch='s'+str(Iden)
    K=int(conf.readline())
    conf.readline()
    for i in range(K):
        ports.append(conf.readline().split()[0])
        port_status_temp.append(1)
        port_status.append(1)

    # read flow information
    conf.readline()
    M=int(conf.readline())
    conf.readline()
    for i in range(M):
        paths.append([])
        next_hop.append([])
        last_hop.append([])
        m=int(conf.readline())
        flow_m.append(m)
        for j in range(m):			# extract information from paths
            paths[i].append(conf.readline())
            temp=paths[i][j].split()
            indicator=0
            for k in range(len(temp)):
                if temp[k]==Iden:
                    indicator=1
                    if k>0:
                        last_hop[i].append(temp[k-1])
                    else:
                        last_hop[i].append('0')
                    if k<len(temp)-1:
                        next_hop[i].append(temp[k+1])
                    else:
                        next_hop[i].append('0')
                    break
            if indicator==0:
                last_hop[i].append('0')
                next_hop[i].append('0')
        temp=paths[i][0].split()
        flow_s.append(temp[0])
        flow_d.append(temp[-1])

        routing.append(0)
        #for j in range(m):			# set initial routing path
        #    if Iden in paths[i][j].split():
        #        routing[i]=j
        #        break
    #print paths
    #print last_hop
    #print next_hop

def initialization():
    global K,ports,subnet,Iden,switch,routing,active_links
    load_configuration()

    # rules for receiving packets
    os.system('sudo ovs-ofctl add-flow '+switch+' priority=100,dl_type=0x0806,nw_dst='+subnet+Iden+',actions=output:1')
    os.system('sudo ovs-ofctl add-flow '+switch+' priority=100,dl_type=0x0800,nw_dst='+subnet+Iden+',actions=output:1')

    # rules for communicating with neighbors
    for i in range(2,K+2):
        os.system('sudo ovs-ofctl add-flow '+switch+' priority=3,dl_type=0x0806,nw_src='+subnet+Iden+',nw_dst='+subnet+ports[i]+',actions=output:'+str(i))
        os.system('sudo ovs-ofctl add-flow '+switch+' priority=3,udp,tp_dst=11451,nw_src='+subnet+Iden+',nw_dst='+subnet+ports[i]+',actions=output:'+str(i))
        os.system('sudo ovs-ofctl add-flow '+switch+' priority=3,udp,tp_dst=14514,nw_src='+subnet+Iden+',nw_dst='+subnet+ports[i]+',actions=output:'+str(i))

    # rules for primary paths
    for i in range(M):
        temp=paths[i][routing[i]].split()
        for j in range(len(temp)-1):			# initialize the set of active links
            active_links.add(temp[j]+'_'+temp[j+1])
        dst=1
        for j in range(2,K+2):				# look for the port of next hop
            if ports[j]==next_hop[i][0]:
                dst=j
        if dst!=1:
            os.system('sudo ovs-ofctl add-flow '+switch+' priority=2,dl_type=0x0806,nw_src='+subnet+flow_s[i]+',nw_dst='+subnet+flow_d[i]+',actions=output:'+str(dst))
            os.system('sudo ovs-ofctl add-flow '+switch+' priority=2,dl_type=0x0800,nw_src='+subnet+flow_s[i]+',nw_dst='+subnet+flow_d[i]+',actions=output:'+str(dst))
    

    
def listen_heartbeat():
    global subnet,Iden,K,ports,port_status,port_status_temp

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((subnet+Iden, 11451))			# listen at port 11451 (UDP)
    
    while True:						# when receive heartbeat, update link status
        data, addr = sock.recvfrom(1024)

        for i in range(2,K+2):
            if subnet+ports[i]==addr[0]:
                port_status_temp[i]=1
                #print 'received.',port_status
                break

def send_heartbeat():
    global subnet,Iden,K,ports,port_status,port_status_temp
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for i in range(2,K+2):
            sock.sendto('heartbeat',(subnet+ports[i], 11451))	# send heartbeat messages to every neighbor
        #print 'sent.'
        time.sleep(1)						# interval = 1 second


def judge_heartbeat():
    global subnet,Iden,K,ports,port_status,port_status_temp,flow_s,flow_m
    while True:
        #print port_status
        for i in range(2,K+2):
            #if port_status_temp[i]^port_status[i]==1:	# status of a link changes
                port_status[i]=port_status_temp[i]
                #print port_status,ports[i]
                for j in range(M):			# if the changed link belongs to a stored path, generate a message
                    for k in range(flow_m[j]):
                        if next_hop[j][k]==ports[i]:                          
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.sendto(Iden+'_'+next_hop[j][k]+' '+str(port_status[i])+' '+str(j)+' ',(subnet+Iden, 14514))
                            break



                port_status_temp[i]=0
        time.sleep(1.2)

def check_path_availability(path_str):
    global active_links
    answer=1
    parsed=path_str.split()
    for i in range(len(parsed)-1):
        if str(parsed[i])+'_'+str(parsed[i+1]) not in active_links:	# check every link in the path
            answer=0
            break
    #print path_str,answer
    return answer

def listen_synchronization():
    global subnet,Iden,K,ports,port_status,port_status_temp,routing,flow_m,next_hop,last_hop,active_links

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((subnet+Iden, 14514))			# listen at port 14514 (UDP)
    
    while True:					
        data, addr = sock.recvfrom(1024)
        #print data,addr
        parsed=data.split()
        f=int(parsed[2])				# f-th flow

        receivers=set([])				# pass the link information message
        for m in last_hop[f]:
            if m!='0':
                receivers.add(m)
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for m in receivers:
            sock2.sendto(data,(subnet+m, 14514))



        src_dst=parsed[0].split('_')
        reverse=src_dst[1]+'_'+src_dst[0]
        if parsed[1]=='1':				# update link availability information
            active_links.add(parsed[0])
            active_links.add(reverse)
        else:
            active_links.discard(parsed[0])
            active_links.discard(reverse)


        for i in range(flow_m[f]):
            if check_path_availability(paths[f][i])==1 and Iden in paths[f][i].split():	# choose first available path
                if routing[f]!=i:
                    routing[f]=i
								# delete old forwarding rules
                    os.system('sudo ovs-ofctl del-flows '+switch+' "dl_type=0x0806,nw_src='+subnet+flow_s[f]+',nw_dst='+subnet+flow_d[f]+'"')
                    os.system('sudo ovs-ofctl del-flows '+switch+' "dl_type=0x0800,nw_src='+subnet+flow_s[f]+',nw_dst='+subnet+flow_d[f]+'"')

                    for j in range(2,K+2):			# find the port to forward
                        if ports[j]==next_hop[f][i]:
                           dst=j

								# install new forwarding rules
                    os.system('sudo ovs-ofctl add-flow '+switch+' priority=2,dl_type=0x0806,nw_src='+subnet+flow_s[f]+',nw_dst='+subnet+flow_d[f]+',actions=output:'+str(dst))
                    os.system('sudo ovs-ofctl add-flow '+switch+' priority=2,dl_type=0x0800,nw_src='+subnet+flow_s[f]+',nw_dst='+subnet+flow_d[f]+',actions=output:'+str(dst))
                break
        #print active_links
        #print routing

initialization()

t0=threading.Thread(target = listen_synchronization)
t0.start()
t1=threading.Thread(target = listen_heartbeat)
t1.start()
t2=threading.Thread(target = send_heartbeat)
t2.start()
time.sleep(3)
t3=threading.Thread(target = judge_heartbeat)
t3.start()



