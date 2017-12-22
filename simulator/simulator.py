import sys


f=open('anglova_topo_c.txt')
fp=open(sys.argv[1])

M=0
paths=[]
selected_paths=[]

def read_flow():
    global M,paths,selected_paths
    M=int(fp.readline())		# number of flows
    for i in range(M):
        paths.append([])
        selected_paths.append([])
        K=int(fp.readline())	# number of backup paths of flow i
        for j in range(K):
            paths[i].append(fp.readline())

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
	
def check():
	global M
	N=f.readline()
	adj=[]
	for i in range(96):
		adj.append(f.readline().split())

	for i in range(1):
		
		for j in selected_paths[i]:
			temp=j.split()
			connectivity=1
			for k in range(len(temp)-1):
				if adj[int(temp[k])-1][int(temp[k+1])-1]=='0':
					connectivity=0

			if connectivity==1:
				break

	return connectivity

	
for i in range(97):
	f.readline()

read_flow()
greedily_select(int(sys.argv[2]))
print selected_paths
count=0
for i in range(7800):
	r=check()
	count=count+r
print float(count)/7800
