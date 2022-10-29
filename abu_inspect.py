#!/bin/env python3
import sys
import docker
import time
import operator

client = docker.APIClient(base_url='unix://var/run/docker.sock')

class agent_info:
    def __init__(self, ip, pid, device):
        self.ip = ip
        self.pid = pid
        self.device = device

    def __repr__(self):
        return f"{type(self).__name__}(ip={self.ip}, pid={self.pid}, device={self.device})"

    def get_packets(self):
        entries = open(f"/proc/{self.pid}/net/dev").readlines()
        line = get_line_with_substring(entries, self.device)
        values = line.split()
        return {
            'received_bytes': int(values[1]),
            'received_packets': int(values[2]), 
            'sent_bytes': int(values[9]),
            'sent_packets': int(values[10])
        }

def extract_network_part(ip):
    ip_parts = ip.split('.')
    network_parts = ip_parts[0:1 if ip_parts[0] == "10" else 2 if ip_parts[0] == "172" else 3]
    return ".".join(network_parts)

def get_device_from_line(line):
    return line.strip().split(' ')[-1]

def get_line_with_substring(lines, substring):
    return list(filter(lambda line: substring in line, lines))[0]

def get_info(namespace, quantity):
    agents_info = {}
    for i in range(0, quantity):
        ip = (client.inspect_container(f"{namespace}-agent{i}")
              ["NetworkSettings"]
              ["Networks"]
              [f"{namespace}-data"]
              ["IPAddress"])
        pid = (client.inspect_container(f"{namespace}-agent{i}")
               ["State"]
               ["Pid"])
        devices = open(f"/proc/{pid}/net/arp").readlines()
        network_ip = extract_network_part(ip)
        device = get_device_from_line(get_line_with_substring(devices, network_ip))
        agents_info[f"{namespace}-agent{i}"] = agent_info(ip, pid, device)
    return agents_info

def get_initial(agents_info):
    counts = {}
    for k, v in agents_info.items():
        counts[k] = v.get_packets()
    return counts

def get_final(agents_info, counts):
    final_counts = {}
    for k, v in agents_info.items():
        final_counts[k] = {key: v.get_packets()[key] - (counts[k])[key]
                            for key in (counts[k]).keys()}
    return final_counts


def main():
    namespace = sys.argv[1]
    quantity = int(sys.argv[2])
    agents_info = get_info(namespace, quantity)
    for k, v in agents_info.items():
        print(f"{k}@{v.ip} -> {v.get_packets()}")

    counts = get_initial(agents_info)
    time.sleep(1)
    counts = get_final(agents_info, counts)
    print(counts)

if __name__ == "__main__":
    main()
