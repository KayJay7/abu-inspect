#!/usr/bin/env python3
from curses import raw
import json
import matplotlib.pyplot as plt
import copy as cp
import re
import csv

############ Configuration
# These are filenames and other data that's been hardcoded into the digest script
# Tweak these if you want to digest different tests

# Results filenames, these are found in the './results' directory
all_files = ["idle_10_500_5.json", "idle_50_500_5.json", "idle_100_500_5.json", "low_10_610_5.json", "low_50_630_5.json", "low_100_1030_5.json", "high_10_505_5.json", "high_50_620_5.json", "high_100_2000_5.json"]
# Only the files of logged tests
logged_files = ["low_10_610_5.json", "low_50_630_5.json", "low_100_1030_5.json", "high_10_505_5.json", "high_50_620_5.json", "high_100_2000_5.json"]
# Running time of each test
all_times = [500, 500, 500, 610, 630, 1030, 505, 620, 2000]
# Folders inside the './results/log-digest' directory, they contains splitted log files numbered 1-n
all_folders = ["low10", "low50", "low100", "high10", "high50", "high100"]
# Labels for graphs and csv files
all_labels = ["Idle 10", "Idle 50", "Idle 100", "Low 10", "Low 50", "Low 100", "High 10", "High 50", "High 100"]
# Only the labels concerned with logs data
logs_labels = ["Low 10", "Low 50", "Low 100", "High 10", "High 50", "High 100"]
# Which agent has been logged
logged_agent = "abusim-example-agent0"
# In how many parts is split each log (how many iterations per test)
log_parts = 5

############ End of configuration

# All metrics with descriptions
template = {
    "received bytes": [], # Total received bytes per agent
    "received packets": [], # Total received packets per agent
    "sent bytes": [], # Total sent bytes per agent
    "sent packets": [], # Total sent packets per agent
    "received bytes per seconds": [], # Like above, but divided by running time
    "received packets per seconds": [], # Like above, but divided by running time
    "sent bytes per seconds": [], # Like above, but divided by running time
    "sent packets per seconds": [], # Like above, but divided by running time
    "bytes ratio": [], # received/sent bytes
    "packets ratio": [], # received/sent packets
    "bytes per packet": [], # Average size of each packet
    "total bytes": [], # Total bytes sent in the network by all agents
    "total packets": [], # Total packets sent in the network by all agents
    "total bytes per seconds": [], # Like above, but divided by running time
    "total packets per seconds": [] # Like above, but divided by running time
}
# Log metrics with descriptions
logs_template = {
    "expected bytes": [], # Sent bytes as reported in the logs
    "actual bytes": [], # Sent bytes as measured by the system
    "expected packets": [], # Sent packets as reported in the logs
    "actual packets": [], # Sent packets as measured by the system
    "bytes ratio": [], # actual/expected bytes
    "packets ratio": [] # actual/expected packets
}

def process(raw_data, time):
    data = cp.deepcopy(template)
    for sample in raw_data:
        total_packets = 0
        total_bytes = 0
        for agent in sample.values():
            data["received bytes"].append(agent["received_bytes"])
            data["received bytes per seconds"].append(agent["received_bytes"] / time)
            data["received packets"].append(agent["received_packets"])
            data["received packets per seconds"].append(agent["received_packets"] / time)
            data["sent bytes"].append(agent["sent_bytes"])
            data["sent bytes per seconds"].append(agent["sent_bytes"] / time)
            data["sent packets"].append(agent["sent_packets"])
            data["sent packets per seconds"].append(agent["sent_packets"] / time)
            data["bytes ratio"].append(agent["received_bytes"] / agent["sent_bytes"])
            data["packets ratio"].append(agent["received_packets"] / agent["sent_packets"])
            data["bytes per packet"].append(agent["sent_bytes"] / agent["sent_packets"])
            total_bytes += agent["sent_bytes"]
            total_packets += agent["sent_packets"]
        data["total bytes"].append(total_bytes)
        data["total packets"].append(total_packets)
        data["total bytes per seconds"].append(total_bytes / time)
        data["total packets per seconds"].append(total_packets / time)

    return data
        

def read_json(name, time):
    f = open(name, "r")
    data = process(json.load(f), time)
    f.close()
    return data

def collect_data():
    data = cp.deepcopy(template)

    for i in range(0, len(all_files)):
        test = read_json(f"results/{all_files[i]}", all_times[i])
        for metric in data:
            data[metric].append(test[metric])

    return data

def read_agent0(name):
    f = open(name, "r")
    data = []
    raw_data = json.load(f)
    for sample in raw_data:
        data.append(sample[logged_agent])
    f.close()
    return data

def digest_logs():
    data = cp.deepcopy(logs_template)
    for i in range(0, len(logs_labels)):
        partial_data = cp.deepcopy(logs_template)
        test = read_agent0(f"results/{logged_files[i]}")
        for j in range(1, log_parts+1):
            expected_bytes = 0
            expected_packets = 0
            file = open(f"results/log-digest/{all_folders[i]}/{j}.log", "r")
            for line in file.readlines():
                if "Sent" in line:
                    expected_packets += 1
                    expected_bytes += int(re.search("\\\"size\\\": (\\d*),", line).group(1))
            partial_data["expected bytes"].append(expected_bytes)
            partial_data["expected packets"].append(expected_packets)
            partial_data["actual bytes"].append(test[j - 1]["sent_bytes"])
            partial_data["actual packets"].append(test[j - 1]["sent_packets"])
            partial_data["bytes ratio"].append(test[j - 1]["sent_bytes"] / expected_bytes)
            partial_data["packets ratio"].append(test[j - 1]["sent_packets"] / expected_packets)
        for metric in data:
            data[metric].append(partial_data[metric])
    return data
            
def write_table_csv(writer, metrics, table):
    rows = list(map(list, zip(*table)))
    writer.writerow(metrics)
    writer.writerows(rows)

def write_data_csv(data, labels, prefix):
    for i in range(0,len(labels)):
        table = []
        totals = []
        metrics = []
        total_metrics = []
        for metric in data:
            if not "total" in metric:
                table.append(data[metric][i])
                metrics.append(metric)
            else:
                totals.append(data[metric][i])
                total_metrics.append(metric)
        ### Questa tronca alla metrica pi?? corta (i totali)
        if len(metrics) > 0:
            file = open(f"csv/{prefix}{labels[i]}.csv", "w")
            writer = csv.writer(file)
            write_table_csv(writer, metrics, table)
        if len(total_metrics) > 0:
            file = open(f"csv/{prefix}totals_{labels[i]}.csv", "w")
            writer_totals = csv.writer(file)
            write_table_csv(writer_totals, total_metrics, totals)

def main():

    data = collect_data()
    for metric in data:
        plt.clf()
        plt.xticks(rotation=-45, ha='left')
        plt.boxplot(data[metric], labels = all_labels, )
        plt.title(metric)
        plt.autoscale()
        plt.savefig(f"graphs/{metric}.png", dpi=300)

    write_data_csv(data, all_labels, "")
    
    logs_data = digest_logs()
    for metric in logs_data:
        plt.clf()
        plt.xticks(rotation=-45, ha='left')
        plt.boxplot(logs_data[metric], labels = logs_labels)
        plt.title(f"logs_{metric}")
        plt.autoscale()
        plt.savefig(f"graphs/logs_{metric}.png", dpi=300)

    write_data_csv(logs_data, logs_labels, "logs_")
    
    

if __name__ == '__main__':
    #print(digest_logs())
    main()