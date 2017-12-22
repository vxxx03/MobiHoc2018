# Simulator
This simulator produces the results of Figure 7 in the paper. Given a group of paths between one set of source and destination, and the amount of backup paths, it will choose the corresponding number of backup paths using greedy algorithm, then it will evaluate the portion of traffic successfully routed by these paths.

## Example
```
python simulator.py 15to55c 8
```
The command above will select 8 backup paths for the flow from Node 15 to Node 55.

## Topology Dataset
Please unzip anglova_topo_c.zip to get the topology file for emulation. This data set is provided by The Network Science Research Laboratory of ARL. For more information, please visit http://www.arl.army.mil/nsrl and https://www.ihmc.us/nomads/scenarios/.
