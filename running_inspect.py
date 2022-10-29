#!/usr/bin/env python3
import abu_inspect as ai
import time
import sys
import json
from signal import signal, SIGINT
from environment import Environment

# BEGIN user defined code
def json_output(filename, results):
    print("serializing results")
    results = json.dumps(results, indent = 4)
    print("writing results")
    output = open(filename, "w")
    output.write(results)

def user_main(env):
    namespace = sys.argv[1]
    quantity = int(sys.argv[2])
    seconds = int(sys.argv[3])
    iterations = int(sys.argv[4])
    filename = sys.argv[5]
   
    agents_info = ai.get_info(namespace, quantity)
    results = list()
    for i in range(0, iterations):
        print(f"start {i}th iteration")
        counts = ai.get_initial(agents_info)
        print("got initial")
        env.post_input(f'agent0', 'start_all = true')
        print(f"start sleeping {seconds} seconds")
        print("remaining: ")
        for i in range(seconds,0,-1):
            print(f"{i}", end="\r", flush=True)
            time.sleep(1)
        print("woke up")
        results.append(ai.get_final(agents_info, counts))
        print(f"finished {i}th iteration")
        json_output(filename, results)

# END user defined code

def main():
    env = Environment()
    signal(SIGINT, lambda *_: (print(), exit(0)))
    user_main(env)
    #env.loop()

if __name__ == '__main__':
    main()
