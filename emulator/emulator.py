#!/usr/bin/python

import sys
import time
import multiprocessing
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

ports=[[]]		# ports information
init_topo=[[]]		# initial topology
N=0			# number of nodes

M=0			# number of flows
paths=[]		# backup paths (string)
selected_paths=[]	# active backup paths

def topo_change(net):
    topo_f=open(sys.argv[1])
    N=int(topo_f.readline())
    old_topo=[[]]
    for i in range(N):
        old_topo.append([0])
        temp=topo_f.readline().split()
        for j in temp:
            old_topo[i+1].append(j)
    print 'Topology initialization finishes.'
    time.sleep(30)

    print 'Topology evolution starts.'
    t=0
    time0=time.time()
    while(topo_f.readline()):
        new_topo=[[]]

        print 't='+str(t)
        time1=time.time()
        print time1-time0

        for i in range(N):
            new_topo.append([0])
            temp=topo_f.readline().split()
            for j in temp:
                new_topo[i+1].append(j)

        for i in range(1,N+1):
            for j in range(i+1,N+1):
                if new_topo[i][j]=='1' and old_topo[i][j]=='0':
                    net.configLinkStatus('s'+str(i),'s'+str(j),'up')
                if new_topo[i][j]=='0' and old_topo[i][j]=='1':
                    net.configLinkStatus('s'+str(i),'s'+str(j),'down')
                old_topo[i][j]=new_topo[i][j]

        time_delta=time.time()-time1
        while time_delta>1:
            for i in range(N+1):
                topo_f.readline()
            t=t+1
            time_delta=time_delta-1
        time.sleep(1-time_delta)
        t=t+1

def read_topo(topo_name):
    global init_topo,ports,N
    topo_f=open(topo_name)
    N=int(topo_f.readline())  		# first line contains the number of nodes
    for i in range(N):
        init_topo.append([0])
        ports.append([0,0])
        neighbors=topo_f.readline().split()

        for j in range(N):
            init_topo[i+1].append(int(neighbors[j]))

def read_flow(flow_name):
    global M,paths,selected_paths
    flow_f=open(flow_name)
    M=int(flow_f.readline())		# number of flows
    for i in range(M):
        paths.append([])
        selected_paths.append([])
        K=int(flow_f.readline())	# number of backup paths of flow i
        for j in range(K):
            paths[i].append(flow_f.readline())

def greedily_select(P):				# select P backup paths for every flow
    global M,paths,selected_paths
    for i in range(M):
        K=len(paths[i])				# K = number of paths
        selected_paths[i].append(paths[i][0])	# primary path must be chosen
        covered=set([])
        costs=[]
        chosen=[]				# make sure one path will not be chosen for more than one time

        for j in range(K):			# initialize costs of all backup paths
            chosen.append(0)
            costs.append(set([]))
            route=paths[i][j].split()		# necessary information in the backup path
            for k in range(len(route)-1):
                link=route[k]+'_'+route[k+1]	# represent a link by "src_dst"
                costs[j].add(link)
            route=paths[i][0].split()		# necessary information in the primary path
            for k in range(len(route)-1):
                link=route[k]+'_'+route[k+1]	
                costs[j].add(link)

        for j in range(P):			# run greedy algorithm by P times
            min_cost=65535
            candidate=0
            for k in range(1,K):
                if len(costs[k])<min_cost and chosen[k]==0:
                    min_cost=len(costs[k])
                    candidate=k
            selected_paths[i].append(paths[i][candidate])
            chosen[candidate]=1
            covered.update(costs[candidate])

            for k in range(1,K):
                costs[k].difference_update(covered)
        

def write_configuration():
    global ports,M,selected_paths
    for i in range(1,N+1):
        conf=open('./local_conf/conf_'+str(i),'w')
        conf.write('Node:\n')
        conf.write(str(i)+'\n')					# serial number of the node
        conf.write(str(len(ports[i])-2)+'\n')			# amount of neighbors
        conf.write('Neighbors:\n')
        for j in range(2,len(ports[i])):
            conf.write(str(ports[i][j])+'\n')			# list of neighbors
        conf.write('Flows:\n')
        conf.write(str(M)+'\n')					# amount of flows
        conf.write('Paths:\n')
        for j in range(M):
            conf.write(str(len(selected_paths[j]))+'\n')	# amount of paths
            for k in selected_paths[j]:
                conf.write(k)					# list of paths
        


def myNetwork():

    topo_name=sys.argv[1]

    flow_name=sys.argv[2]

    read_topo(topo_name)  		# read ports information from file
    
    read_flow(flow_name)  		# read flow information and backup paths

    greedily_select(int(sys.argv[3]))	# select backup paths using greedy algorithm

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')


    info( '*** Adding controller\n' )
    c=net.addController(name='c0',
                      controller=RemoteController,
                      ip="127.0.0.1",
                      protocol='tcp',
                      port=6633)
  

    info( '*** Add switches\n')
    switches=[0]
    for i in range(1,N+1):
        switches.append ( net.addSwitch('s'+str(i), cls=OVSKernelSwitch) )

    info( '*** Add hosts\n')
    hosts=[0]
    for i in range(1,N+1):
        hosts.append ( net.addHost('h'+str(i), cls=Host, ip='10.0.0.'+str(i), defaultRoute=None) )


    info( '*** Add links\n')
    for i in range(1,N+1):
        net.addLink(switches[i], hosts[i])

    #para_delay={'delay':'50000'}
    for i in range(1,N+1):
        for j in range(i+1,N+1):
            if init_topo[i][j]==1:
                #net.addLink(switches[i], switches[j], cls=TCLink , **para_delay)
                net.addLink(switches[i], switches[j])
                ports[i].append(j)
                ports[j].append(i)

    info( '*** Starting network\n')
    net.build()

#    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

#    info( '*** Starting switches\n')
    for i in range(1,N+1):
        net.get('s'+str(i)).start([c])


    info( '*** Post configure switches and hosts\n')
    
    write_configuration()
    #print selected_paths

    active_nodes=[0]*(N+1)
    for i in selected_paths:
        for j in i:
            for k in j.split():
                active_nodes[int(k)]=1

    for i in range(1,N+1):						# start local agents
        if active_nodes[i]!=0:
            hosts[i].cmd('sudo python ./agent.py ./local_conf/conf_'+str(i)+' &')
            print 'Local agent starts on Node '+str(i)+'.'

    for i in range(M):							# start flows
        src=selected_paths[i][0].split()[0]
        dst=selected_paths[i][0].split()[-1]
        hosts[int(src)].cmd('ping 10.0.0.'+dst+' >./ping_results/'+src+'_'+dst+'.txt &')

    p = multiprocessing.Process(target = topo_change, args = (net,))	# introduce topology changes
    p.start()    

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

