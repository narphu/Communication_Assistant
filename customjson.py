import random
import json
import math
import sys

class Satellite:
    def _init_(self, name, id, xpos, ypos, zpos, time, visible=None):
        if visible is None:
            visible = []
        self.name = name
        self.id = id
        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos
        self.time = time
        self.visible = visible


def calculate_bs_los():
    return True

def calculate_gps_los(src_sat, dest_sat):
    euclid_distance = round(math.sqrt(((dest_sat.xpos - src_sat.xpos) ** 2) + ((dest_sat.ypos - src_sat.ypos) ** 2) +
                                      ((dest_sat.zpos - src_sat.zpos) ** 2)), 2)

    if euclid_distance <= 6500:
        return True
    else:
        return False


def generatepositions(n_nodes, sat_list, seed=None):
    if seed is not None:
        random.seed(seed)

    # Generate a dict of positions for the given data
    for i in range(0, n_nodes):

        xpos = round(random.gauss(-1000*((i + 1) ^ 2), 1000), 6)
        # xpos = random.uniform(-10000, 10000)
        ypos = round(random.gauss(-1000*((i + 1) ^ 2), 1000), 6)
        # ypos = random.uniform(-500, 10000)
        zpos = round(random.gauss(2000 + (i * 10), 500), 6)
        # zpos = random.uniform(5000, 10000)
        sat_list[i].xpos = xpos
        sat_list[i].ypos = ypos
        sat_list[i].zpos = zpos


def generate_sats(num_nodes):
    sat_list = []

    # Create list of objects for all satellites
    for obj in range(1, num_nodes + 1):
        obj = Satellite()
        sat_list.append(obj)

    # Generate Name and ID for each satellite
    for i in range(0, num_nodes):
        sat_list[i].name = "GPS BIIF-" + str(i + 1)
        sat_list[i].id = 30000 + (100 * (i + 1)) + (50 + (i + 1)) + (i + 1)
        sat_list[i].time = float(0.00000)
    return sat_list


def visibility(num_nodes, sat_list, src_sat):
    visigraph = []

    if src_sat == "BS":
        for node in range(0, num_nodes):
            sat = {"satName": sat_list[node].name, "satID": sat_list[node].id,
                   "LoS": calculate_bs_los(),
                   "PosX": sat_list[node].xpos, "PosY": sat_list[node].ypos,
                   "PosZ": sat_list[node].zpos}
            visigraph.append(sat)

    else:
        for node in range(0, num_nodes):
            sat = {"satName": sat_list[node].name, "satID": sat_list[node].id,
                   "LoS": calculate_gps_los(src_sat, sat_list[node]),
                   "PosX": sat_list[node].xpos, "PosY": sat_list[node].ypos,
                   "PosZ": sat_list[node].zpos}
            visigraph.append(sat)
    return visigraph


def generate_json(num_nodes, timeduration, timeslot):
    gps_json_file = {"SatcomScnDef": {"simDuration": float(timeduration), "SateDef": []}}
    bs_json_file = {"SatcomScnDef": {"simDuration": float(timeduration), "SateDef": []}}
    sat_list = generate_sats(num_nodes)
    bs_name = "MC Colorado Spring"
    for curr_time in range(0, timeduration, timeslot):
        generatepositions(num_nodes, sat_list, seed=None)
        bs_json_file["SatcomScnDef"]["SateDef"].append({"BSName": bs_name, "BSID": 1,
                                                        "PosX": 4324.694434, "PosY": 2471.735847,
                                                        "PosZ": 3970.158822, "Time": float(curr_time),
                                                        "visibilityGraph": visibility(num_nodes, sat_list, "BS")
                                                        })
        for node in range(0, num_nodes):
            gps_json_file["SatcomScnDef"]["SateDef"].append({"satName": sat_list[node].name, "satID": sat_list[node].id,
                                                             "PosX": sat_list[node].xpos, "PosY": sat_list[node].ypos,
                                                             "PosZ": sat_list[node].zpos, "Time": float(curr_time),
                                                             "visibilityGraph": visibility(num_nodes, sat_list,
                                                                                           sat_list[node])
                                                             })

            with open('VisibleGPS_%s.json' % num_nodes, 'w') as fp:
                json.dump(gps_json_file, fp, indent=4)
        with open('VisibleBS_%s.json' % num_nodes, 'w') as fp:
            json.dump(bs_json_file, fp, indent=4)


def generateovsportsmap(num_nodes, num_phys):
    ovsportsmap = {}
    start = 1
    for node in range(0, num_nodes):
        portlist = []
        for port in range(start, start+num_phys):
            portlist.append(port)
            if start > num_nodes*(num_phys+1) + 1:
                break
        ovsportsmap["SAT%s" % (node+1)] = portlist
        start = port + 1
        with open('ovsPortsMap_%s.json' % num_nodes, 'w') as fp:
            json.dump(ovsportsmap, fp, indent=4)


def main():
    num_nodes = int(sys.argv[1])
    num_phys = int(sys.argv[2])
    time_duration = int(sys.argv[3])
    time_slot = 10  # sys.argv[3]

    generate_json(num_nodes, time_duration, time_slot)
    generateovsportsmap(num_nodes,num_phys)


if __name__ == "__main__":
    main()
