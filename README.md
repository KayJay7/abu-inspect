# abu-inspect

Benchmarking scripts and results for [abusim](https://github.com/abu-lang/abusim) and [goabu](https://github.com/abu-lang/goabu).

## Results

The results of this benchmark can be found in boxplot form in the `./graphs` directory, and in csv form in the `./csv` directory.

Metrics with description:
* `received bytes`: Total received bytes per agent
* `received packets`: Total received packets per agent
* `sent bytes`: Total sent bytes per agent
* `sent packets`: Total sent packets per agent
* `received bytes per seconds`: Like above, but divided by running time
* `received packets per seconds`: Like above, but divided by running time
* `sent bytes per seconds`: Like above, but divided by running time
* `sent packets per seconds`: Like above, but divided by running time
* `bytes ratio`: received/sent bytes
* `packets ratio`: received/sent packets
* `bytes per packet`: Average size of each packet
* `total bytes`: Total bytes sent in the network by all agents
* `total packets`: Total packets sent in the network by all agents
* `total bytes per seconds`: Like above, but divided by running time
* `total packets per seconds`: Like above, but divided by running time

## Usage

Prerequisites:
* Python
* Awk (or some degree of patience)
* Docker
* Any linux system (the script accesses some linux pseudofiles)
* The following docker containers
  * `abulang/abusim-gui:latest`
  * `abulang/abusim-coordinator:latest`
  * [This](https://github.com/max-co/abusim-goabu-agent/commits/log-sends) container (on branch `log-sends`), possibly tagged as `abulang/abusim-goabu-agent-log:latest`
    * You can use any agent image that uses [this commit](https://github.com/abu-lang/goabu/commit/bd36603f1751) of goabu or a later one
* Optionally [aeg](https://github.com/KayJay7/abusim-example-generator) to generate test cases (requires a rust toolchain for compiling)

Read every section in order before running a benchmark.

### Test cases

The original test cases can be found in the `./test_configs` directory, but new can be created using `aeg`, full instructions are found on it's GitHub page.

Remember to set the agent image as `abulang/abusim-goabu-agent-log:latest` (or whatever tag you set) or you won't be able to inspect log metrics.

The original were created with:

```sh
aeg -a 10 -o idle10.yml --devices-length=3 --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 50 -o idle50.yml --devices-length=3 --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 100 -o idle100.yml --devices-length=3 --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 10 -b 10 -c 5 -d 5 --devices-length=20 -o low10.yml --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 50 -b 10 -c 5 -d 5 --devices-length=20 -o low50.yml --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 100 -b 10 -c 5 -d 5 --devices-length=20 -o low100.yml --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 10 -e=3 --devices-length=5 -o high10.yml --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 50 -e=3 --devices-length=5 -o high50.yml --image="abulang/abusim-goabu-agent-log:latest"
aeg -a 100 -e=3 --devices-length=5 -o high100.yml --image="abulang/abusim-goabu-agent-log:latest"
```

### Launching an logging

To launch abusim without logging use:

```sh
./abusim -c <path to config file> -g up
```

To launch abusim with logging use the following command, *and* from the web GUI (at https://localhost:8080) manually set the log level to "debug" for *one* of the agents, the test were run logging 'agent0'.

```sh
./abusim -c <path to config file> -g up | tee <path to log file>
```

In case of failed start you might need to manually tear down the environment *before* retrying, using:

```sh
./abusim -c <path to config file> -g down
```

To run tests with more than ~35 agents you might need to edit your `/etc/sysctl.conf` file and increase the values of the `net.ipv4.neigh.default.gc_thresh{1,2,3}` variables and reload/reboot. The tests were run win the following values (maximum):

```
net.ipv4.neigh.default.gc_thresh1 = 2147483647
net.ipv4.neigh.default.gc_thresh2 = 2147483647
net.ipv4.neigh.default.gc_thresh3 = 2147483647

net.ipv6.neigh.default.gc_thresh1 = 2147483647
net.ipv6.neigh.default.gc_thresh2 = 2147483647
net.ipv6.neigh.default.gc_thresh3 = 2147483647
```

### Idle benchmark

Logs don't provide useful information for idle benchmarking, don't bother collect those logs.\
To run the idle tests, launch abusim as explained above and run:

```sh
./idle_inspect.py <namespace> <number of devices> <running time> <iterations> <output file>
```

If you didn't specify otherwise, the namespace will be 'abusim-example'. The tests were run with 500 seconds of running time and 5 iterations.

*All tests should have the same number of iterations, later scripts make this assumption.*

### Running benchmark

A running benchmark requires a bit more work.\
Before the test you need to discover how long it takes for one computation to end, because the overhead of the simulator causes the actual running times to be longer than expected when increasing the number of devices. For that you will need to launch normally abusim, then start a stopwatch and send to any agent the command `start_all = true` (from the GUI) and wait for every queue to empty.\
Repeat this for every configuration and write down every running time.

Once you know every running time, relaunch again the configuration you want to benchmark (eventually with logging) and once it's up run:

```sh
./running_inspect.py <namespace> <number of devices> <measured running time> <number of iterations> <output file>
```

The output file of the original benchmarks (found in the `./results` directory, alongside log files) are in the form `type_<devices>_<time>_<iterations>`. The configuration were chosen so that the running time with a few devices would be around 500 seconds on a certain machine and then the number was increased to 10, 50 and 100. The benchmarks with more devices required much more time.

*All tests (even idle ones) should have the same number of iterations, later scripts make this assumption.*

### Splitting the log files

The data digestion script requires the logs of each benchmark to be split in multiple files, one for each iteration. The files *must* to be in separate directories (the split logs from original test, these directories can be found in the `./results/log-digest` directory), and the files from each iteration must be named `1.log` to `n.log` (not from 0).

To split the files you can just use the awk command:
```sh
awk 'BEGIN {count=0; filename="0.log"} /Input: start_all = true/{filename=++count".log"}; {print >filename}' <path to log file to split>
```

This awk command will generate all the files (splitting at the "start_all = true" command which starts the computation) and a file named `0.log` which doesn't contain useful information and will be ignored by the next script, you can delete it.

### Data digestion

The last step is reading all the data produced and turing it into useful CSVs and graphs with the `./graph.py` script.

All the filenames and all the information needed for the digestion are hardcoded into the first lines of the script file (from 9 to 30). Before running the script remember to edit those lines it according to your benchmark setup.\
Make sure to "align" the data in the lists, e.g.: the first element of the `all_files` list must refer to the same benchmark as the first element of the `all_times` list.\
*Each parameter is commented with its description.*

Once everything is setup you can digest the data by running:

```sh
./graph.py
```

The results will appear in the `./csv` and `./graphs` directories. It might return an error if such directories don't exist.\
This script can take a couple seconds to run.