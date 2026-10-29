"""Real-World Use tab.

Added as a separate module so no existing code had to change.
It reuses the project's own Banker's Algorithm functions (banker.py)
and the dashboard's existing CSS classes (panel, cc, cgrid, vd, chip, tag ...).
"""
import copy
import streamlit as st
from banker import compute_need, is_safe, request_resource, vec_le

ss = st.session_state

# ---------------------------------------------------------------- scenarios
SCENARIOS = {
    "Cloud server (AWS / Azure style)": dict(
        icon="☁️", noun="job",
        story="A cloud provider has a limited pool of CPU cores, memory and GPUs. Every customer job declares the "
              "most it may ever need. Before handing out more, the scheduler asks: can every job still finish afterwards?",
        names=["Training job", "Web API", "DB backup", "Analytics"],
        res=["vCPU", "RAM (GB)", "GPU"],
        alloc=[[2, 4, 1], [1, 2, 0], [2, 8, 0], [1, 2, 1]],
        mx=[[6, 16, 2], [3, 8, 1], [4, 16, 1], [4, 8, 2]],
        avail=[3, 6, 1],
        examples=[("Safe request", 1, [1, 0, 0]), ("Risky request", 0, [0, 1, 0])]),
    "Hospital (beds, ventilators, doctors)": dict(
        icon="🏥", noun="ward",
        story="A hospital shares beds, ventilators and doctors between wards. Each ward has a declared maximum. "
              "Giving a ward a ventilator is refused if it could leave every ward waiting for someone else's equipment.",
        names=["Emergency", "Surgery", "ICU", "Maternity"],
        res=["Beds", "Ventilators", "Doctors"],
        alloc=[[3, 1, 1], [1, 0, 2], [2, 1, 0], [1, 1, 1]],
        mx=[[8, 3, 4], [4, 1, 3], [5, 2, 2], [4, 2, 3]],
        avail=[3, 1, 2],
        examples=[("Safe request", 1, [1, 0, 0]), ("Risky request", 0, [1, 0, 0])]),
    "Office computer (printer, scanner, disk)": dict(
        icon="🖥️", noun="program",
        story="The classic operating-system case. Several programs share devices such as printers, scanners and "
              "disk channels. The OS must never let programs lock each other out of the devices they still need.",
        names=["Word", "Photoshop", "Backup tool", "Browser"],
        res=["Printer", "Scanner", "Disk"],
        alloc=[[1, 0, 1], [0, 1, 0], [1, 1, 0], [0, 0, 1]],
        mx=[[3, 2, 2], [2, 2, 1], [2, 2, 1], [1, 1, 2]],
        avail=[1, 1, 1],
        examples=[("Safe request", 2, [1, 0, 0]), ("Risky request", 0, [1, 0, 0])]),
}

USE_CASES = [
    ("Operating systems", "Resources: printers, disk channels, memory frames, locks. Processes: running programs.",
     "Decides whether a program may be given one more device without risking a freeze.", "Classic OS textbooks"),
    ("Cloud and data centres", "Resources: vCPU, RAM, GPU, storage. Processes: customer jobs and virtual machines.",
     "Decides whether a new VM or job can be admitted and still let every running job finish.", "Resource quotas, VM scheduling"),
    ("Database systems", "Resources: row, table and page locks. Processes: transactions.",
     "Stops transactions from waiting on each other in a circle. Databases detect or prevent this daily.", "MySQL, PostgreSQL, Oracle"),
    ("Hospitals and emergency services", "Resources: beds, ventilators, ambulances, staff. Processes: wards and incidents.",
     "Makes sure scarce equipment is never split in a way that leaves every ward waiting.", "Resource planning"),
    ("Banking and finance", "Resource: money. Processes: customers with credit limits.",
     "The original idea. A bank lends only if it can still satisfy every customer's maximum limit later.", "Where the name comes from"),
    ("Embedded and real-time systems", "Resources: sensors, buses, memory buffers. Processes: control tasks.",
     "In cars, aircraft and robots a freeze is unacceptable, so resource claims are declared up front.", "Automotive, avionics"),
    ("Telecom and networks", "Resources: bandwidth, channels, ports. Processes: calls and data sessions.",
     "Admission control: accept a new session only if existing ones can still complete.", "Call admission control"),
    ("Manufacturing and robotics", "Resources: robot arms, conveyors, tools. Processes: production jobs.",
     "Prevents two jobs each holding a tool the other one needs next.", "Factory scheduling"),
]

MAPPING = [
    ("Process", "A job, program, ward, customer or transaction"),
    ("Resource type", "CPU, memory, GPU, printer, bed, lock, money"),
    ("Allocation", "What the job holds right now"),
    ("Maximum", "The most the job declared it could ever need"),
    ("Need = Max − Allocation", "What the job may still ask for"),
    ("Available", "What is free in the pool right now"),
    ("Safe sequence", "An order in which every job can finish one after another"),
    ("Request denied", "The system says \"wait\" so it never gets stuck later"),
]


# ---------------------------------------------------------------- helpers
def _show(html):
    st.markdown(html, unsafe_allow_html=True)


def _panel(title, body, tag="", tagcls=""):
    t = f"<em class='{tagcls}'>{tag}</em>" if tag else ""
    return f"<div class='pn'><div class='pnh'><span>{title}</span>{t}</div><div class='pnb'>{body}</div></div>"


def _vec(v):
    return "(" + ", ".join(str(int(x)) for x in v) + ")"


def _state(sc):
    """Per-scenario live state, kept in session so granted requests really change the system."""
    store = ss.setdefault("rw_state", {})
    if sc not in store:
        s = SCENARIOS[sc]
        store[sc] = dict(alloc=copy.deepcopy(s["alloc"]), avail=list(s["avail"]))
    return store[sc]


def _do_request(sc, pid, req):
    s, stt = SCENARIOS[sc], _state(sc)
    res = request_resource(pid, req, stt["alloc"], s["mx"], stt["avail"])
    if res["status"] == "GRANTED":
        stt["alloc"], stt["avail"] = res["new_alloc"], res["new_avail"]
    ss["rw_last"] = dict(sc=sc, pid=pid, req=req, res=res)


def _cb_request(sc):
    s = SCENARIOS[sc]
    pid = s["names"].index(ss[f"rw_pid_{sc}"])
    req = [int(ss[f"rw_req_{sc}_{j}"]) for j in range(len(s["res"]))]
    _do_request(sc, pid, req)


def _cb_example(sc, pid, req):
    s = SCENARIOS[sc]
    ss[f"rw_pid_{sc}"] = s["names"][pid]
    for j, v in enumerate(req):
        ss[f"rw_req_{sc}_{j}"] = v
    _do_request(sc, pid, req)


def _cb_finish(sc, pid):
    """A job that holds its full maximum finishes and gives everything back."""
    stt = _state(sc)
    stt["avail"] = [a + b for a, b in zip(stt["avail"], stt["alloc"][pid])]
    stt["alloc"][pid] = [0] * len(stt["avail"])
    ss["rw_last"] = dict(sc=sc, pid=pid, req=None, res=dict(status="FINISHED"))


def _cb_reset(sc):
    ss.get("rw_state", {}).pop(sc, None)
    if ss.get("rw_last", {}).get("sc") == sc:
        ss.pop("rw_last", None)


def _table(headers, rows):
    h = "<table class='ct'><tr>" + "".join(f"<th>{x}</th>" for x in headers) + "</tr>"
    for r in rows:
        h += "<tr>" + "".join(r) + "</tr>"
    return h + "</table>"


def _td(v, cls=""):
    return f"<td class='{cls}'>{v}</td>"


def _num(v):
    return _td(int(v), "nm" if v else "nm zero")


# ---------------------------------------------------------------- live demo
def _live_demo():
    _show("<div class='h2'>LIVE DEMO: TRY A REAL SYSTEM</div>")
    _show("<div class='cap'>Pick a real-life situation. The numbers below are processed by the same Banker's Algorithm code "
          "used on the other tabs. Make a request and watch the system accept it or hold it back. Granted requests "
          "really change the system, so you can keep going.</div>")

    sc = st.radio("Real-life situation", list(SCENARIOS), horizontal=True, key="rw_sc", label_visibility="collapsed")
    s, stt = SCENARIOS[sc], _state(sc)
    names, res, noun = s["names"], s["res"], s["noun"]
    n, m = len(names), len(res)

    _show(f"<div class='aim'><b>{s['icon']} {sc.split(' (')[0].upper()}.</b> {s['story']}</div>")

    need = compute_need(stt["alloc"], s["mx"])
    safe, seq, _ = is_safe(stt["alloc"], need, stt["avail"])

    # ---- current state
    rows = []
    for i in range(n):
        order = f"<span class='tag pass'>#{seq.index(i) + 1}</span>" if i in seq else "<span class='tag fail'>NOT IN ORDER</span>"
        rows.append([_td(names[i], "pid"), _td(_vec(stt["alloc"][i]), "nm"), _td(_vec(s["mx"][i]), "cy"),
                     _td(_vec(need[i]), "nm"), _td(order, "")])
    body = _table([noun.upper()] + ["HOLDS", "MAX", "STILL MAY NEED", "SAFE ORDER"], rows)
    body += f"<div class='avail'>FREE NOW ({', '.join(res)})<b>{_vec(stt['avail'])}</b></div>"
    _show(_panel("CURRENT SYSTEM", "<div class='scroll'>" + body + "</div>",
                 "SAFE" if safe else "UNSAFE", "ok" if safe else "warn"))

    if safe:
        chips = []
        for k, p in enumerate(seq):
            chips.append(f"<div class='chip'>{names[p]}</div>")
            if k < len(seq) - 1:
                chips.append("<div class='arw'></div>")
        _show("<div class='sq-h'>EVERY " + noun.upper() + " CAN FINISH IN THIS ORDER</div><div class='sq'>" + "".join(chips) + "</div>")

    # ---- request form
    left, right = st.columns([1, 1.25])
    with left:
        _show("<div class='h2'>MAKE A REQUEST</div>")
        st.selectbox(f"Which {noun} is asking?", names, key=f"rw_pid_{sc}")
        cols = st.columns(m)
        for j in range(m):
            ss.setdefault(f"rw_req_{sc}_{j}", 0)
            cols[j].number_input(res[j], 0, 20, key=f"rw_req_{sc}_{j}")
        st.button("Ask the system", type="primary", width="stretch", on_click=_cb_request, args=(sc,), key=f"rw_go_{sc}")
        ex = st.columns(len(s["examples"]))
        for c, (label, pid, req) in zip(ex, s["examples"]):
            c.button(label, width="stretch", on_click=_cb_example, args=(sc, pid, req), key=f"rw_ex_{sc}_{label}")

        done = [i for i in range(n) if all(v == 0 for v in need[i]) and any(stt["alloc"][i])]
        if done:
            _show("<div class='h2'>FINISHED " + noun.upper() + "S</div>")
            for i in done:
                st.button(f"{names[i]} is done: release its resources", width="stretch",
                          on_click=_cb_finish, args=(sc, i), key=f"rw_fin_{sc}_{i}")
        st.button("Reset this situation", width="stretch", on_click=_cb_reset, args=(sc,), key=f"rw_rs_{sc}")

    with right:
        _show("<div class='h2'>WHAT THE SYSTEM DECIDES</div>")
        lr = ss.get("rw_last")
        if not lr or lr["sc"] != sc:
            _show("<div class='cap'>No request yet. Try <b>Safe request</b> to see it granted, then <b>Risky request</b> "
                  "to see the system refuse something that looks harmless but could freeze everyone.</div>")
        else:
            r, who = lr["res"], names[lr["pid"]]
            st_ = r["status"]
            ask = f" asked for {_vec(lr['req'])} of ({', '.join(res)})" if lr["req"] is not None else ""
            if st_ == "GRANTED":
                _show(f"<div class='vd safe'><b>GRANTED</b><span>{who}{ask}. The system stays safe, so it says yes. "
                      f"Every {noun} can still finish in this order: {', '.join(names[i] for i in r['sequence'])}.</span></div>")
            elif st_ == "WAIT":
                _show(f"<div class='vd wait'><b>PLEASE WAIT</b><span>{who}{ask}, but that much is not free right now. "
                      f"Nothing was changed.</span></div>")
            elif st_ == "DENIED_UNSAFE":
                _show(f"<div class='vd unsafe'><b>DENIED: TOO RISKY</b><span>{who}{ask}. The resources exist, but handing them over "
                      f"could leave every {noun} waiting on another forever. The system holds the request back and keeps "
                      f"the old state.</span></div>")
            elif st_ == "FINISHED":
                _show(f"<div class='vd safe'><b>{who.upper()} FINISHED</b><span>It returned everything it held, so more is free for the others.</span></div>")
            else:
                _show(f"<div class='vd invalid'><b>INVALID REQUEST</b><span>{r['reason']}</span></div>")

        _show("<div class='h2'>POOL UTILISATION</div>")
        bars = ""
        for j in range(m):
            used = sum(stt["alloc"][i][j] for i in range(n))
            tot = used + stt["avail"][j]
            pct = 100 * used / tot if tot else 0
            bars += (f"<div class='pcard' style='margin-bottom:.5rem'><div class='r' style='grid-template-columns:90px 1fr 70px;margin-top:0'>"
                     f"<span>{res[j]}</span><div class='bar'><div style='width:{pct:.0f}%'></div></div>"
                     f"<span class='n'>{used}/{tot}</span></div></div>")
        _show(bars)


# ---------------------------------------------------------------- page
def render_real_world_tab():
    _show("<div class='aim'><b>REAL-WORLD USE.</b> Banker's Algorithm is not only a textbook exercise. It answers one question that "
          "every shared system has to ask: <b>\"If I give this resource away now, can everybody still finish later?\"</b> "
          "This page shows where that question appears in real life and lets you try it yourself.</div>")

    _live_demo()

    _show("<div class='h2'>WHERE THIS IDEA IS USED</div>")
    _show("<div class='cgrid'>" + "".join(
        f"<div class='cc k'><b>{t}</b><span>{d}</span><em>{w}</em><span style='display:block;margin-top:.4rem;color:#8297A8;font-size:.85rem'>{n}</span></div>"
        for t, d, w, n in USE_CASES) + "</div>")

    _show("<div class='h2'>THIS PROJECT'S TERMS IN REAL LIFE</div>")
    rows = [[_td(a, "pid"), _td(b, "tx")] for a, b in MAPPING]
    _show(_panel("TRANSLATION TABLE", _table(["PROJECT TERM", "REAL-WORLD MEANING"], rows)))

    _show("<div class='h2'>HONEST LIMITS IN PRACTICE</div>")
    _show("<div class='cap'>Real systems rarely run the full algorithm on every request. Knowing why is a strong point for your viva.</div>")
    limits = [("Maximum must be known", "Banker's needs every process to declare its maximum need in advance. Many real programs cannot predict this."),
              ("Fixed set of processes", "The algorithm assumes a fixed number of processes and resources. Real systems have jobs starting and stopping constantly."),
              ("Checking has a cost", "Each safety check scans every process and resource, which is expensive for large systems on every single request."),
              ("What real systems do instead", "General-purpose operating systems often ignore deadlock or use prevention (such as lock ordering) and detection with recovery. Databases detect deadlock and abort one transaction.")]
    _show("<div class='cgrid'>" + "".join(f"<div class='cc'><b>{t}</b><span>{d}</span></div>" for t, d in limits) + "</div>")
