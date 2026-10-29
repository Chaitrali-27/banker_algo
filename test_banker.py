from banker import *

ALLOC = [[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]]
MAX   = [[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]]
AVAIL = [3,3,2]

def test_tc1_safe():
    need = compute_need(ALLOC, MAX)
    assert need == [[7,4,3],[1,2,2],[6,0,0],[0,1,1],[4,3,1]]
    safe, seq, _ = is_safe(ALLOC, need, AVAIL)
    assert safe and seq == [1,3,0,2,4]  # one valid order; [1,3,4,0,2] is also valid

def test_tc2_exceeds_available():
    r = request_resource(0, [7,4,3], ALLOC, MAX, AVAIL)
    assert r["status"] == "WAIT"

def test_tc3_unsafe():
    r = request_resource(4, [3,3,0], ALLOC, MAX, AVAIL)
    assert r["status"] == "DENIED_UNSAFE"
    assert ALLOC[4] == [0,0,2] and AVAIL == [3,3,2]   # unchanged

def test_granted_example():
    r = request_resource(1, [1,0,2], ALLOC, MAX, AVAIL)
    assert r["status"] == "GRANTED"

D_ALLOC = [[1,0,0],[0,1,0],[0,0,1]]
D_REQ   = [[0,1,0],[0,0,1],[1,0,0]]

def test_tc4_deadlock_and_recovery():
    dead, _ = detect_deadlock(D_ALLOC, D_REQ, [0,0,0])
    assert dead == [0,1,2]
    cyc = find_cycle(wait_for_edges(D_ALLOC, D_REQ))
    assert cyc is not None
    a, r, av = terminate_process(2, D_ALLOC, D_REQ, [0,0,0])
    dead2, _ = detect_deadlock(a, r, av)
    assert dead2 == []

def test_tc5_prevention():
    assert ordering_violation([0,0,1], [1,0,0]) is True     # P3 holds R2 wants R0 -> blocked
    assert ordering_violation([1,0,0], [0,1,0]) is False

def test_tc6_boundary_invalid():
    need = compute_need(ALLOC, MAX)
    assert request_resource(9, [0,0,0], ALLOC, MAX, AVAIL)["status"] == "INVALID"
    assert request_resource(1, [-1,0,0], ALLOC, MAX, AVAIL)["status"] == "INVALID"
    assert request_resource(1, [5,0,0], ALLOC, MAX, AVAIL)["status"] == "INVALID"   # > Need
    assert validate_state([[5,0,0]], [[3,0,0]], [0,0,0])                              # alloc > max
    assert request_resource(1, [1,0,0], ALLOC, MAX, [0,0,0])["status"] == "WAIT"      # zero available
    assert request_resource(2, [0,0,0], ALLOC, MAX, AVAIL)["status"] in ("GRANTED",)  # zero request ok
    safe, seq, _ = is_safe([[0]],[[0]],[0])                                           # zero need
    assert safe
