"""Rebuild tools/prun2_costs.json (cost estimates for tools/prun2.py) from the measured wall times of the last prun2
run (results/logs/prun2/timing.json) and, for steps not in it, from the wall_s / time_s stored in the step outputs.
usage: python tools/prun2_costs.py [timing.json]"""
import json, os, sys, glob
sys.path.insert(0, os.getcwd())
import run_all as R
cost = json.load(open('tools/prun2_costs.json')) if os.path.exists('tools/prun2_costs.json') else {}
for f in glob.glob('data/derived/paths/*.json'):                      # stored wall_s of path steps
    d = json.load(open(f))
    if 'wall_s' in d:
        for s in R.load():
            if any(o['path'] == os.path.relpath(f) for o in s['outs']):
                cost[s['name']] = round(float(d['wall_s']), 1)
t = sys.argv[1] if len(sys.argv) > 1 else 'results/logs/prun2/timing.json'
if os.path.exists(t):
    for n, v in json.load(open(t))['steps'].items():
        cost[n] = v['wall_s']
json.dump(dict(sorted(cost.items(), key=lambda kv: -kv[1])), open('tools/prun2_costs.json', 'w'), indent=1)
print(len(cost), 'costs written')
