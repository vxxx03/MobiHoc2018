# Local Agent
The local agent verifies the concept of flexible SDN architecture. Given a configuration file, it will automately exchange information with instances in other nodes, and maintain a group of backup paths. When link failure happens and the primary path is not available, it installs a backup path in Open vSwitch replacing the current forwarding rules.

# Emulator
The Mininet-based emulator tests the local agent using a time-variant network topology from real dataset. It will generate configuration files for local agents in every node, and start multiple ICMP flows. In order to run the emulator, Mininet should be installed in advance.

## Example
'''
python emulator.py anglova_topo_c.txt anglova_paths_1.txt 4
'''
The command above will start 10 flows in the network as written in anglova_paths_1.txt, and prepare 4 backup paths for every flow.

## Result
The configuration files containing selected backup paths can be found in the folder ./local_conf.
The ping results are recorded in the folder ./ping_results.

## Topology Dataset
Please unzip anglova_topo_c.zip to get the topology file for emulation. This data set is provided by The Network Science Research Laboratory of ARL. For more information, please visit http://www.arl.army.mil/nsrl and https://www.ihmc.us/nomads/scenarios/.
