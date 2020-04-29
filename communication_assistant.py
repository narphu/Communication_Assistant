import sys
import json
import time
import random
import subprocess


class Network :
    visibleSat = {}
    connectedSat = {}
    phyavailable = {}

    def __init__(self, sats, phys) :
        self.defineconnectedSat(sats, phys)
        self.definephysavailable(sats, phys)
        self.definevisibleSats(sats, phys)

    def defineconnectedSat(self, sats, phys) :
        for sat in range(0, sats) :
            iphys = []
            self.connectedSat["SAT%s" % (sat + 1)] = []
            for phy in range(0, phys) :
                iphys.append(0)
            self.connectedSat["SAT%s" % (sat + 1)] = iphys

    def definephysavailable(self, sats, phys) :
        for sat in range(0, sats) :
            iphys = []
            self.phyavailable["SAT%s" % (sat + 1)] = []
            for phy in range(0, phys) :
                iphys.append(0)
            self.phyavailable["SAT%s" % (sat + 1)] = iphys

    def definevisibleSats(self, sats, phys) :
        for sat in range(0, sats) :
            iphys = []
            self.visibleSat["SAT%s" % (sat + 1)] = []

    def definevisibleSat(self, src, dst) :
        if (src == dst) :
            return
        for vals in self.visibleSat["SAT%s" % src] :
            if vals == dst :
                return
        self.visibleSat["SAT%s" % src].append(dst)


def loadvisibilitygraphs() :
    # Loading visibility graph for GPS info
    with open('VisibleGPS_12.json', 'r') as jsonfile :
        vis_json = json.load(jsonfile)
    with open('ovsPortsMap_12.json', 'r') as jsonfile :
        ovs_ports_map = json.load(jsonfile)
    return vis_json, ovs_ports_map


def findsrcphy(network, src, dst) :
    index = 0
    for phy in network.phyavailable[src] :
        if phy == 0 :
            break
        index += 1
    network.phyavailable[src][index] = 1
    network.connectedSat[src][index] = int(dst.split('T')[1])
    return index

def finddstphy(network, src, dst) :
    index = 0
    for phy in network.phyavailable[dst] :
        if phy == 0 :
            break
        index += 1
    network.phyavailable[dst][index] = 1
    network.connectedSat[dst][index] = int(src.split('T')[1])
    return index


def addlink(network, src, dst, ovsPortsMap) :
    srcphy = findsrcphy(network, src, dst)
    dstphy = finddstphy(network, src, dst)
    src_port = ovsPortsMap[(src)][srcphy]
    dst_port = ovsPortsMap[(dst)][dstphy]
    # Using a shell script to delete direct link between two PHYs
    print("Add link between %s and %s using ports %s and %s" % (src,dst,src_port,dst_port))
    #subprocess.call(['./set_link.sh', "add", str(src_port), str(dst_port)])


def updatelinks(network, ovsPortsMap) :
    for src in network.visibleSat :
        while 0 in network.phyavailable[src] :
            dst = (random.choice(network.visibleSat[src]))
            if 0 in network.phyavailable["SAT%s" % dst] :
                if dst in network.connectedSat[src] or src in network.connectedSat["SAT%s" %dst]:
                    print("Link already exists between %s and SAT%s" % (src, dst))
                    break
                addlink(network, src, "SAT%s" % dst, ovsPortsMap)
            else :
                print("Couldnt find available PHY in %s" %dst)
                break


def runSimulation(sats, phys) :
    vis_json, ovs_ports_map = loadvisibilitygraphs()
    sim_duration_time = vis_json["SatcomScnDef"]["simDuration"]
    sim_current_time = 0
    sim_next_time = 0
    sat_point = 0
    # start_time = time.localtime()

    while (sim_current_time < sim_duration_time) :
        start_time = time.time()
        network = Network(sats, phys)
        sat_point = 0
        for sat in vis_json["SatcomScnDef"]["SateDef"] :
            # Only fetch the visibility graph portion used for current time slot simulation
            if sat["Time"] != sim_current_time :
                sim_next_time = sat["Time"]
                break
            else :
                sat_point += 1
                srcvid = int(sat["satName"].split('-')[1])
                for visibleSAT in sat["visibilityGraph"] :
                    if visibleSAT["LoS"] :
                        dstvid = int(visibleSAT["satName"].split('-')[1])
                        network.definevisibleSat(srcvid, dstvid)
        updatelinks(network, ovs_ports_map)
        vis_json["SatcomScnDef"]["SateDef"] = vis_json["SatcomScnDef"]["SateDef"][sat_point :]
        if len(vis_json["SatcomScnDef"]["SateDef"]) == 0 :
            sim_next_time = sim_duration_time
        if sim_current_time == 0 :
            print("> Start of the simulation!")
            print(network.visibleSat)
            time.sleep(10)
        else :
            print("> Current simulation time:", sim_current_time)
            print(network.visibleSat)
        time_elapsed = time.time() - start_time
        if time_elapsed >= sim_next_time - sim_current_time :
            sim_current_time = sim_next_time
            continue
        else :
            time.sleep(10)
            sim_current_time = sim_next_time


def main(sat_num, phy_num) :
    runSimulation(sat_num, phy_num)


if __name__ == "__main__" :
    sat_num = sys.argv[0]
    phy_num = sys.argv[1]
    main(sat_num, phy_num)
