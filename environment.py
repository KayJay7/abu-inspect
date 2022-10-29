from time import sleep
from multiprocess import Pool
from requests import get, post
from json import loads

class Environment(object):
    actions = []

    def loop(self):
        def executer(trigger):
            agent, variable, tick, callback = trigger
            while True:
                print(f'Executing on agent {agent}, variable {variable}')
                variables = self.get_variables(agent)
                callback(variables[variable], variables)
                sleep(tick)
        with Pool(len(self.actions)) as p:
            p.map(executer, self.actions)
        
    def on(self, agent, variable, tick, callback):
        self.actions.append((agent, variable, tick, callback))

    def get_variables(self, agent):
        r = get(f'http://localhost:4000/memory/{agent}')
        memory = loads(r.content)['memory']
        return {k: v for d in [v for _, v in memory.items()] for k, v in d.items()}

    def post_input(self, agent, input_command):
        post(f'http://localhost:4000/memory/{agent}', json={'actions': input_command})