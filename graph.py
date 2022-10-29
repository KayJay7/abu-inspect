#!/usr/bin/env python3
from curses import raw
import json
import matplotlib.pyplot as plt
import copy as cp
import re
import csv

all_files = ["idle_10_500_5.json", "idle_50_500_5.json", "idle_100_500_5.json", "low_10_610_5.json", "low_50_630_5.json", "low_100_1030_5.json", "high_10_505_5.json", "high_50_620_5.json", "high_100_2000_5.json"]
all_times = [500, 500, 500, 610, 630, 1030, 505, 620, 2000]
all_folders = ["low10", "low50", "low100", "high10", "high50", "high100"]
template = {
    "received bytes": [],
    "received packets": [],
    "sent bytes": [],
    "sent packets": [],
    "received bytes per seconds": [],
    "received packets per seconds": [],
    "sent bytes per seconds": [],
    "sent packets per seconds": [],
    "bytes ratio": [],
    "packets ratio": [],
    "bytes per packet": [],
    "total bytes": [],
    "total packets": [],
    "total bytes per seconds": [],
    "total packets per seconds": []
}
logs_template = {
    "expected bytes": [],
    "actual bytes": [],
    "expected packets": [],
    "actual packets": [],
    "bytes ratio": [],
    "packets ratio": []
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

    for i in range(0, 9):
        test = read_json(f"results/{all_files[i]}", all_times[i])
        for metric in data:
            data[metric].append(test[metric])

    return data

def read_agent0(name):
    f = open(name, "r")
    data = []
    raw_data = json.load(f)
    for sample in raw_data:
        data.append(sample["abusim-example-agent0"])
    f.close()
    return data

def digest_logs():
    data = cp.deepcopy(logs_template)
    for i in range(0, 6):
        partial_data = cp.deepcopy(logs_template)
        test = read_agent0(f"results/{all_files[i]}")
        for j in range(1,6):
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
        ### Questa tronca alla metrica più corta (i totali)
        if len(metrics) > 0:
            file = open(f"csv/{prefix}{labels[i]}.csv", "w")
            writer = csv.writer(file)
            write_table_csv(writer, metrics, table)
        if len(total_metrics) > 0:
            file = open(f"csv/{prefix}totals_{labels[i]}.csv", "w")
            writer_totals = csv.writer(file)
            write_table_csv(writer_totals, total_metrics, totals)

def main():
    labels = ["Idle 10", "Idle 50", "Idle 100", "Low 10", "Low 50", "Low 100", "High 10", "High 50", "High 100"]
    data = collect_data()
    for metric in data:
        plt.clf()
        plt.boxplot(data[metric], labels = labels, )
        plt.title(metric)
        plt.autoscale()
        plt.savefig(f"graphs/{metric}.png", dpi=300)

    write_data_csv(data, labels, "")
    
    labels = ["Low 10", "Low 50", "Low 100", "High 10", "High 50", "High 100"]
    logs_data = digest_logs()
    for metric in logs_data:
        plt.clf()
        plt.boxplot(logs_data[metric], labels = labels)
        plt.title(metric)
        plt.autoscale()
        plt.savefig(f"graphs/logs_{metric}.png", dpi=300)

    write_data_csv(logs_data, labels, "logs_")
    
    

if __name__ == '__main__':
    #print(digest_logs())
    main()