"""Core logic: Banker's Algorithm (avoidance), deadlock detection, recovery, prevention.
Kept separate from the UI so it can be tested on its own."""
from copy import deepcopy

# ---------- helpers ----------
def vec_le(a, b):
    return all(x <= y for x, y in zip(a, b))

def vec_add(a, b):
    return [x + y for x, y in zip(a, b)]

def vec_sub(a, b):
    return [x - y for x, y in zip(a, b)]

# ---------- input validation (INVALID state) ----------
def validate_state(alloc, mx, avail):
    errors = []
    n, m = len(alloc), len(avail)
    if len(mx) != n:
        errors.append("Allocation and Max must have the same number of processes.")
        return errors
    for i in range(n):
        if len(alloc[i]) != m or len(mx[i]) != m:
            errors.append(f"P{i}: row length must equal number of resources ({m}).")
            return errors
    if any(v < 0 for v in avail):
        errors.append("Available contains a negative value.")
    for i in range(n):
        for j in range(m):
            if alloc[i][j] < 0 or mx[i][j] < 0:
                errors.append(f"P{i}, R{j}: negative value in Allocation/Max.")
            elif alloc[i][j] > mx[i][j]:
                errors.append(f"P{i}, R{j}: Allocation ({alloc[i][j]}) exceeds Max ({mx[i][j]}).")
    return errors

def compute_need(alloc, mx):
    return [vec_sub(mx[i], alloc[i]) for i in range(len(alloc))]

# ---------- AVOIDANCE: safety algorithm ----------
def is_safe(alloc, need, avail):
    """Returns (safe, sequence, trace). trace = list of step dicts."""
    n = len(alloc)
    work = list(avail)
    finish = [False] * n
    seq, trace = [], []
    while True:
        found = False
        for i in range(n):
            if not finish[i] and vec_le(need[i], work):
                before = list(work)
                work = vec_add(work, alloc[i])
                finish[i] = True
                seq.append(i)
                trace.append({"process": f"P{i}", "Need": list(need[i]),
                              "Work before": before, "Work after": list(work)})
                found = True
                break
        if not found:
            break
    return all(finish), seq, trace

# ---------- AVOIDANCE: resource-request algorithm ----------
def request_resource(pid, req, alloc, mx, avail):
    """Statuses: INVALID, WAIT, DENIED_UNSAFE, GRANTED.
    Original state is NEVER modified; the new state is returned on GRANT."""
    n, m = len(alloc), len(avail)
    if not isinstance(pid, int) or pid < 0 or pid >= n:
        return {"status": "INVALID", "reason": f"Process id {pid} does not exist (valid: 0..{n-1})."}
    if len(req) != m:
        return {"status": "INVALID", "reason": f"Request must have {m} values."}
    if any(r < 0 for r in req):
        return {"status": "INVALID", "reason": "Request contains a negative value."}
    need = compute_need(alloc, mx)
    if not vec_le(req, need[pid]):
        return {"status": "INVALID",
                "reason": f"Request {req} exceeds P{pid}'s remaining Need {need[pid]} (process exceeded its declared maximum)."}
    if not vec_le(req, avail):
        return {"status": "WAIT",
                "reason": f"Request {req} <= Need but > Available {avail}. Not enough free resources; P{pid} must wait. State unchanged."}
    # pretend to allocate
    new_avail = vec_sub(avail, req)
    new_alloc = deepcopy(alloc); new_alloc[pid] = vec_add(new_alloc[pid], req)
    new_need = compute_need(new_alloc, mx)
    safe, seq, trace = is_safe(new_alloc, new_need, new_avail)
    if safe:
        return {"status": "GRANTED", "reason": "Resulting state is safe.",
                "sequence": seq, "trace": trace,
                "new_alloc": new_alloc, "new_avail": new_avail}
    return {"status": "DENIED_UNSAFE",
            "reason": f"Granting would leave Available {new_avail} and no complete safe sequence exists. "
                      "Request denied, original state restored. (Unsafe is NOT the same as deadlocked.)",
            "trace": trace, "sequence": seq,
            "simulated_alloc": new_alloc, "simulated_avail": new_avail}

# ---------- DETECTION (separate from Banker's) ----------
def detect_deadlock(alloc, request, avail):
    """Detection algorithm for multiple-instance resources.
    request[i] = what Pi is currently waiting for. Returns (deadlocked_pids, trace)."""
    n = len(alloc)
    work = list(avail)
    finish = [all(v == 0 for v in alloc[i]) for i in range(n)]
    trace = []
    changed = True
    while changed:
        changed = False
        for i in range(n):
            if not finish[i] and vec_le(request[i], work):
                before = list(work)
                work = vec_add(work, alloc[i])
                finish[i] = True
                trace.append({"process": f"P{i}", "Work before": before, "Work after": list(work)})
                changed = True
    return [i for i in range(n) if not finish[i]], trace

def wait_for_edges(alloc, request):
    """Single-instance wait-for graph: Pi -> Pj if Pi requests a resource Pj holds."""
    n, m = len(alloc), len(alloc[0])
    edges = []
    for i in range(n):
        for j in range(m):
            if request[i][j] > 0:
                for k in range(n):
                    if k != i and alloc[k][j] > 0:
                        edges.append((i, k))
    return sorted(set(edges))

def find_cycle(edges):
    graph = {}
    for a, b in edges:
        graph.setdefault(a, []).append(b)
    def dfs(node, stack, seen):
        if node in stack:
            return stack[stack.index(node):] + [node]
        if node in seen:
            return None
        seen.add(node)
        for nxt in graph.get(node, []):
            c = dfs(nxt, stack + [node], seen)
            if c:
                return c
        return None
    seen = set()
    for start in list(graph):
        c = dfs(start, [], seen)
        if c:
            return c
    return None

# ---------- RECOVERY ----------
def terminate_process(pid, alloc, request, avail):
    alloc2, req2 = deepcopy(alloc), deepcopy(request)
    avail2 = vec_add(avail, alloc2[pid])
    alloc2[pid] = [0] * len(avail)
    req2[pid] = [0] * len(avail)
    return alloc2, req2, avail2

# ---------- PREVENTION (break circular wait via resource ordering) ----------
def ordering_violation(held_row, req_row):
    """Processes must request resources in increasing index order.
    Violation if requesting R_j while holding some R_k with k > j."""
    held = [k for k, v in enumerate(held_row) if v > 0]
    wanted = [j for j, v in enumerate(req_row) if v > 0]
    if not held or not wanted:
        return False
    return min(wanted) < max(held)
