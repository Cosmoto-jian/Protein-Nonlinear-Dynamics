"""Two-VM scheduler for pipeline.yaml (run on the master VM, inside the project root).

Same staleness logic and the same pipeline.lock entries as `run_all.py`; steps run as soon as the producers of all
their deps have finished, on the master (local subprocess) or on a remote worker VM (Freestyle `vm ssh` / `vm scp`).

  python tools/prun2.py [--all] [--dry]

* Priority: longest-processing-time first on the critical-path rank (own cost + longest downstream chain), costs
  from tools/prun2_costs.json (stored wall_s / time_s of the previous single-VM run; unknown steps 30 s).
* Slots: every VM has SLOTS (4) cores.  Big Piezo1 (6b3r) steps run as 1 process x 4 threads (4 slots); when only
  2-3 slots are free on a VM and the others are held by long single-slot steps, a big step starts with as many
  threads as free slots instead of leaving them idle.  nulls takes 4 slots (its own pool of 4 single-threaded
  processes); every other step 1 slot x 1 thread.
  OMP/OPENBLAS/MKL_NUM_THREADS are set per process so that processes x threads <= 4 per VM.
* Data movement: the master keeps every output.  Before a step starts on the worker, deps whose digest differs from
  what the worker holds are pushed (one tar); after it finishes its outs are pulled back (one tar).  The worker
  records the digests of the deps it actually used; the master locks the step only if they equal its own digests
  (pipeline.lock semantics of run_all.py: cmd, params, dep and out digests).
* A failing step is retried once; a second failure stops dispatching (running steps finish) and the run exits 1.
Environment: PRUN2_WORKER (Freestyle VM id), PRUN2_TEAM, FREESTYLE_API_KEY (or the file $HOME/.fskey), PRUN2_WROOT
(worker project root, default $HOME/pnd_fast), PRUN2_WPY (worker python, default $HOME/venv/bin/python).
Timing is written to results/logs/prun2/timing.json.
"""
import sys, os, json, time, subprocess, shlex, argparse
sys.path.insert(0, os.getcwd())
import run_all as R

ap = argparse.ArgumentParser(); ap.add_argument('--all', action='store_true'); ap.add_argument('--dry', action='store_true')
ap.add_argument('--no-worker', action='store_true'); ap.add_argument('--slots', type=int, default=4)
A = ap.parse_args()
WORKER = None if A.no_worker else os.environ.get('PRUN2_WORKER')
TEAM = os.environ.get('PRUN2_TEAM', '')
WROOT = os.environ.get('PRUN2_WROOT', '$HOME/pnd_fast'); WPY = os.environ.get('PRUN2_WPY', '$HOME/venv/bin/python')   # expanded by the worker shell
_KF = os.path.join(os.path.expanduser('~'), '.fskey')
KEY = os.environ.get('FREESTYLE_API_KEY') or (open(_KF).read().strip() if os.path.exists(_KF) else '')
LOGD = 'results/logs/prun2'; os.makedirs(LOGD, exist_ok=True)
COST = json.load(open('tools/prun2_costs.json')) if os.path.exists('tools/prun2_costs.json') else {}


def log(*a):
    print(time.strftime('%F %T'), *a, flush=True)


def fs(args, timeout=600):
    """run the Freestyle CLI; returns (rc, stdout)."""
    env = dict(os.environ, FREESTYLE_API_KEY=KEY)
    if args[0] == 'scp':                      # the CLI runs in /tmp: make local paths absolute
        args = ['scp'] + [x if ':' in x else os.path.abspath(x) for x in args[1:]]
    cmd = ['npx', '-y', 'freestyle@latest', 'vm'] + args + (['--team', TEAM] if TEAM else [])
    for attempt in range(3):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, cwd='/tmp')
            if r.returncode == 0:
                return 0, r.stdout
        except subprocess.TimeoutExpired:
            pass
        time.sleep(3 * (attempt + 1))
    return 1, ''


def wexec(sh, timeout=600):
    return fs(['ssh', WORKER, '--exec', sh], timeout)


# ------------------------------------------------------------------ graph
steps = R.load(); byname = {s['name']: s for s in steps}; prod = R.producer(steps); lock = R.read_lock()
todo_names = [s['name'] for s in steps] if A.all else list(R.stale(steps, lock))
todo = [byname[n] for n in todo_names]; names = set(todo_names)
up = {s['name']: {prod[d] for d in s['deps'] if prod.get(d) and prod[d] != s['name']} for s in steps}
down = {n: set() for n in byname}
for n, u in up.items():
    for x in u:
        down[x].add(n)
cost = {n: float(COST.get(n, 30.0)) for n in byname}
rank = {}
for s in reversed(steps):                     # pipeline.yaml is topologically ordered
    rank[s['name']] = cost[s['name']] + max([rank[d] for d in down[s['name']]] or [0.0])


def slots_of(s):
    n = s['name']
    if n == 'nulls':
        return 4, 1
    if '6b3r' in n and n.split('-')[0] in ('path', 'variant', 'arclength', 'load') and n != 'path-6b3r-rc8':
        return 4, 4                           # 1 process x 4 threads
    return 1, 1


def envs(threads, extra=None):
    e = {'OMP_NUM_THREADS': threads, 'OPENBLAS_NUM_THREADS': threads, 'MKL_NUM_THREADS': threads, 'NUMEXPR_NUM_THREADS': threads}
    e.update(extra or {})
    return {k: str(v) for k, v in e.items()}


if A.dry:
    for s in sorted(todo, key=lambda s: -rank[s['name']]):
        print(f"{s['name']:28s} cost {cost[s['name']]:7.0f} rank {rank[s['name']]:7.0f} slots {slots_of(s)}")
    sys.exit(0)

# ------------------------------------------------------------------ worker state
have = {}                                     # path -> digest currently on the worker
dep_paths = sorted({d for s in steps for d in s['deps']} | {o['path'] for s in steps for o in s['outs']})
if WORKER:
    code = ("import sys,json;sys.path.insert(0,'.');import run_all as R;"
            f"print('DIG'+json.dumps({{d:R.digest(d) for d in {dep_paths!r}}}))")
    open(f'{LOGD}/_dig.py', 'w').write(code)
    wexec(f'mkdir -p {WROOT}/{LOGD} && rm -f {WROOT}/{LOGD}/*.rc {WROOT}/{LOGD}/*.log {WROOT}/{LOGD}/*.deps.json')
    fs(['scp', f'{LOGD}/_dig.py', f'{WORKER}:/tmp/prun2_dig.py'])
    rc, outp = wexec(f'cd {WROOT} && {WPY} /tmp/prun2_dig.py')
    line = [l[l.index('DIG{') + 3:] for l in outp.splitlines() if 'DIG{' in l]
    if rc or not line:
        sys.exit(f'worker digest check failed rc={rc} out={outp[-500:]!r}')
    have = json.loads(line[-1])
    loc = {d: R.digest(d) for d in dep_paths}
    diff = [d for d in dep_paths if have.get(d) != loc.get(d) and d in {x for s in steps for x in s['deps']}]
    log('worker', WORKER, 'dep digests differing from master:', len(diff), diff[:10])


def push(paths, tagname):
    need = [p for p in paths if R.digest(p) is not None and have.get(p) != R.digest(p)]
    if not need:
        return True
    tgz = f'/tmp/push_{tagname}.tgz'
    subprocess.run(['tar', 'czf', tgz] + need, check=True)
    if fs(['scp', tgz, f'{WORKER}:/tmp/push_{tagname}.tgz'])[0]:
        return False
    rm = ' '.join(shlex.quote(p) for p in need)
    if wexec(f'cd {WROOT} && rm -rf {rm} && tar xzf /tmp/push_{tagname}.tgz && rm -f /tmp/push_{tagname}.tgz')[0]:
        return False
    for p in need:
        have[p] = R.digest(p)
    log('pushed', tagname, need)
    return True


def pull(paths, tagname):
    rm = ' '.join(shlex.quote(p) for p in paths)
    if wexec(f'cd {WROOT} && tar czf /tmp/pull_{tagname}.tgz {rm}')[0]:
        return False
    if fs(['scp', f'{WORKER}:/tmp/pull_{tagname}.tgz', f'/tmp/pull_{tagname}.tgz'])[0]:
        return False
    subprocess.run(f'rm -rf {rm} && tar xzf /tmp/pull_{tagname}.tgz && rm -f /tmp/pull_{tagname}.tgz', shell=True, check=True)
    for p in paths:
        have[p] = R.digest(p)
    return True


# ------------------------------------------------------------------ run loop
VMS = ['master'] + (['worker'] if WORKER else [])
free = {v: A.slots for v in VMS}
running = {}                                  # name -> dict(vm, proc, t0, slots, attempt)
done, failed, attempts, timing = set(), [], {}, {}
T0 = time.time()
log('todo', len(todo), 'worker', WORKER)


def start(s, vm, grant=None):
    n = s['name']; sl, th = slots_of(s)
    if grant is not None and grant < sl and th > 1:          # malleable big step: threads = granted slots
        sl = th = grant
    e = envs(th, {'NULLS_JOBS': 4} if n == 'nulls' else None)
    attempts[n] = attempts.get(n, 0) + 1
    cmd = s['cmd']
    if vm == 'master':
        c = f'"{sys.executable}" ' + cmd[7:] if cmd.startswith('python ') else cmd
        p = subprocess.Popen(c, shell=True, stdout=open(f'{LOGD}/{n}.log', 'w'), stderr=subprocess.STDOUT, env=dict(os.environ, **e))
        running[n] = dict(vm=vm, proc=p, t0=time.time(), slots=sl, s=s)
    else:
        if not push(s['deps'], n):
            log('PUSH FAILED', n); attempts[n] -= 1; return False
        c = f'{WPY} ' + cmd[7:] if cmd.startswith('python ') else cmd
        ev = ' '.join(f'{k}={v}' for k, v in e.items())
        dig = ("import sys,json;sys.path.insert(0,'.');import run_all as R;"
               f"json.dump({{d:R.digest(d) for d in {s['deps']!r}}},open('{LOGD}/{n}.deps.json','w'))")
        inner = (f'cd {WROOT} && rm -f {LOGD}/{n}.rc && {{ {WPY} -c {shlex.quote(dig)} && env {ev} {c}; }} '
                 f'> {LOGD}/{n}.log 2>&1; echo $? > {LOGD}/{n}.rc')
        rc, _ = wexec(f'mkdir -p {WROOT}/{LOGD}; setsid -f bash -c {shlex.quote(inner)} < /dev/null > /dev/null 2>&1; echo ok')
        if rc:
            log('REMOTE START FAILED', n); attempts[n] -= 1; return False
        running[n] = dict(vm=vm, proc=None, t0=time.time(), slots=sl, s=s)
    free[vm] -= sl
    log('START', n, vm, f'slots {sl} threads {th}')
    return True


def finish(n, ok_rc):
    r = running.pop(n); s = r['s']; free[r['vm']] += r['slots']; wall = time.time() - r['t0']
    ok = ok_rc
    if ok and r['vm'] == 'worker':
        outs = [o['path'] for o in s['outs']]
        ok = pull(outs + [f'{LOGD}/{n}.log', f'{LOGD}/{n}.deps.json'], n)
        if ok:
            used = json.load(open(f'{LOGD}/{n}.deps.json'))
            bad = [d for d in s['deps'] if used.get(d) != R.digest(d)]
            if bad:
                log('DEPS DIFFER', n, bad); ok = False
    absent = [o['path'] for o in s['outs'] if R.digest(o['path']) is None]
    if not ok or absent:
        log('FAIL', n, r['vm'], f'{wall:.0f}s', absent)
        if attempts[n] < 2:
            todo.insert(0, s)                 # retry once
        else:
            failed.append(n)
        return
    lock = R.read_lock()
    lock[n] = {"cmd": s["cmd"], "params": s.get("params"), "deps": {d: R.digest(d) for d in s["deps"]},
               "outs": {o["path"]: R.digest(o["path"]) for o in s["outs"]}}
    R.LOCK.write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if r['vm'] == 'master':
        pass
    done.add(n); timing[n] = dict(vm=r['vm'], wall_s=round(wall, 1), start_s=round(r['t0'] - T0, 1), slots=r['slots'])
    json.dump(dict(total_s=round(time.time() - T0, 1), steps=timing), open(f'{LOGD}/timing.json', 'w'), indent=1)
    log('DONE', n, r['vm'], f'{wall:.0f}s')


last_poll = 0.0
while todo or running:
    if not failed:
        todo.sort(key=lambda s: -rank[s['name']])
        for s in list(todo):
            n = s['name']
            if up[n] & (names - done):
                continue
            sl, th = slots_of(s); grant = None
            # place: the VM with enough free slots; prefer the master for steps whose deps the worker lacks
            cands = [v for v in VMS if free[v] >= sl]
            if not cands and th > 1:
                # big step: take >= 2 free slots on a VM whose other steps will not finish soon (> 60 s left)
                def busy_left(v):
                    return max([cost[m] - (time.time() - r['t0']) for m, r in running.items() if r['vm'] == v] or [0.0])
                c2 = [v for v in VMS if free[v] >= 2 and busy_left(v) > 60]
                if c2:
                    v = max(c2, key=lambda v: free[v]); grant = free[v]; cands = [v]
            if not cands:
                continue
            if len(cands) == 2:
                miss = sum(1 for d in s['deps'] if have.get(d) != R.digest(d))
                v = 'master' if (miss and free['master'] >= sl and cost[n] < 120) else max(cands, key=lambda v: (free[v], v == 'master'))
            else:
                v = cands[0]
            todo.remove(s)
            if not start(s, v, grant):
                todo.insert(0, s)
                break
    time.sleep(5)
    for n, r in list(running.items()):
        if r['vm'] == 'master' and r['proc'].poll() is not None:
            finish(n, r['proc'].returncode == 0)
    if WORKER and any(r['vm'] == 'worker' for r in running.values()) and time.time() - last_poll > 20:
        last_poll = time.time()
        rc, outp = wexec(f'cd {WROOT}/{LOGD} && for f in *.rc; do [ -e "$f" ] && echo "RC $f $(cat $f)"; done; '
                         f'for f in *.log; do [ -e "$f" ] && echo "LOG $f"; done; true')
        if rc == 0:
            logs = {l[l.index('LOG ') + 4:].split()[0][:-4] for l in outp.splitlines() if 'LOG ' in l}
            for n, r in list(running.items()):          # launch verification: no log 60 s after start -> relaunch
                if r['vm'] == 'worker' and n not in logs and time.time() - r['t0'] > 60:
                    log('LAUNCH LOST', n, '- relaunching')
                    running.pop(n); free['worker'] += r['slots']
                    if attempts[n] >= 2:
                        failed.append(n)
                    else:
                        todo.insert(0, r['s'])
            for l in outp.splitlines():
                if 'RC ' in l and '.rc' in l:
                    _, f, v = l[l.index('RC '):].split()[:3]; n = f[:-3]
                    if n in running and running[n]['vm'] == 'worker':
                        wexec(f'rm -f {WROOT}/{LOGD}/{f}')
                        finish(n, v == '0')
    if failed and not running:
        break
if not failed:
    lk = R.read_lock(); lk = {k: v for k, v in lk.items() if k in byname}
    R.LOCK.write_text(json.dumps(lk, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    R.derive(steps)
left = R.stale(steps, R.read_lock())
tot = time.time() - T0
json.dump(dict(total_s=round(tot, 1), steps=timing, failed=failed), open(f'{LOGD}/timing.json', 'w'), indent=1)
log('FAILED' if failed else 'OK', failed, f'wall {tot:.0f}s', 'still stale:', sorted(left))
sys.exit(1 if failed else 0)
