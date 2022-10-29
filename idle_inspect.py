#!/bin/env python3
import abu_inspect as ai
import time
import sys
import json

def json_output(filename, results):
    results = json.dumps(results, indent = 4)
    output = open(filename, "w")
    output.write(results)

def main():
    namespace = sys.argv[1]
    quantity = int(sys.argv[2])
    seconds = int(sys.argv[3])
    iterations = int(sys.argv[4])
    filename = sys.argv[5]
   
    agents_info = ai.get_info(namespace, quantity)
    results = list()
    for i in range(0, iterations):
        counts = ai.get_initial(agents_info)
        time.sleep(seconds)
        results.append(ai.get_final(agents_info, counts))

    json_output(filename, results)

if __name__ == "__main__" :
    main()
