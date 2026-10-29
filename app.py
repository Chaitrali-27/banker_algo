import copy
import urllib.parse
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
from banker import *

st.set_page_config(page_title="Deadlock", layout="wide", initial_sidebar_state="expanded")
ss = st.session_state

from pathlib import Path
DARK = st.get_option("theme.base") == "dark"
CONFIG_TEXT = """[theme]
base = "dark"
primaryColor = "#00F5FF"
backgroundColor = "#050B10"
secondaryBackgroundColor = "#0A151D"
textColor = "#E6F4FF"

[server]
headless = true
"""
_cfg_written = False
if not DARK:
    _cfg = Path(".streamlit") / "config.toml"
    try:
        if not _cfg.exists():
            _cfg.parent.mkdir(exist_ok=True); _cfg.write_text(CONFIG_TEXT); _cfg_written = True
    except OSError:
        pass

# ====================================================================== CSS
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{--bg:#050B10;--side:#091219;--panel:#0A151D;--cy:#00F5FF;--teal:#00D6B8;--green:#00FF88;--amber:#FFB000;--red:#FF304F;--purple:#D946EF;--tx:#E6F4FF;--mut:#8297A8;--line:rgba(0,245,255,.22);--mono:'JetBrains Mono',ui-monospace,monospace;}
html, body, .stApp, [class*="st-"]{font-family:'Rajdhani','Segoe UI',system-ui,sans-serif;}
[data-testid="stIconMaterial"], [class*="material-symbols"], .material-icons{font-family:'Material Symbols Rounded','Material Icons' !important;font-feature-settings:'liga' 1;}
.stApp{background-color:var(--bg);color:var(--tx);GRID}
#MainMenu, footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:1rem;max-width:1680px;}
p, li, label, span{letter-spacing:.01em}

/* sidebar */
[data-testid="stSidebar"]{background:var(--side);border-right:1px solid var(--line);}
[data-testid="stSidebar"] .block-container{padding-top:1rem;}
.brand{display:flex;align-items:center;gap:.7rem;margin:.2rem 0 1.2rem;}
.brand .hex{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border:2px solid var(--cy);border-radius:10px;box-shadow:0 0 14px rgba(0,245,255,.45), inset 0 0 10px rgba(0,245,255,.2);}
.brand .hex i{width:12px;height:12px;border-radius:50%;background:var(--cy);box-shadow:0 0 10px var(--cy);}
.brand b{font-size:1.45rem;font-weight:700;letter-spacing:.12em;color:var(--tx);text-shadow:0 0 12px rgba(0,245,255,.35)}
.side-h{font-size:.74rem;font-weight:600;color:var(--mut);letter-spacing:.16em;margin:1.2rem 0 .4rem;}

/* status bar */
.sbar{display:flex;align-items:center;gap:1.4rem;flex-wrap:wrap;border:1px solid rgba(0,245,255,.4);border-radius:12px;padding:.75rem 1.3rem;background:rgba(10,21,29,.85);box-shadow:0 0 22px rgba(0,245,255,.10), inset 0 0 18px rgba(0,245,255,.04);margin-bottom:.9rem;}
.sbar .t{font-size:1.1rem;font-weight:700;letter-spacing:.1em;white-space:nowrap}
.lm{display:flex;align-items:center;gap:.5rem;font-weight:600;letter-spacing:.05em;font-size:.95rem;white-space:nowrap;opacity:.38;transition:opacity .2s}
.lm.on{opacity:1}
.lm i{width:20px;height:20px;border-radius:50%;border:2px solid;display:block}
.lm.g{color:var(--green)}.lm.g i{border-color:var(--green);background:radial-gradient(circle,var(--green) 0 45%,transparent 50%)}
.lm.a{color:var(--amber)}.lm.a i{border-color:var(--amber);background:radial-gradient(circle,var(--amber) 0 45%,transparent 50%)}
.lm.r{color:var(--red)}.lm.r i{border-color:var(--red);background:radial-gradient(circle,var(--red) 0 45%,transparent 50%)}
.lm.v{color:var(--mut)}.lm.v i{border-color:var(--mut);background:radial-gradient(circle,var(--mut) 0 45%,transparent 50%)}
.lm.on.g i{box-shadow:0 0 12px var(--green);animation:pulse 2.4s ease-in-out infinite}
.lm.on.a i{box-shadow:0 0 12px var(--amber);animation:pulse 2.4s ease-in-out infinite}
.lm.on.r i{box-shadow:0 0 14px var(--red);animation:alert 1.2s ease-in-out infinite}
.lm.on.v i{box-shadow:0 0 8px var(--mut)}
.sbar .ts{margin-left:auto;color:var(--mut);font-size:.95rem;letter-spacing:.05em;white-space:nowrap}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}
@keyframes alert{0%,100%{box-shadow:0 0 6px var(--red)}50%{box-shadow:0 0 20px 4px var(--red)}}

/* panels */
.pn{border:1px solid var(--line);border-radius:12px;background:rgba(10,21,29,.88);box-shadow:0 0 18px rgba(0,245,255,.06), inset 0 0 22px rgba(0,245,255,.025);margin-bottom:.9rem;overflow:hidden;transition:border-color .2s, box-shadow .2s;}
.pn:hover{border-color:rgba(0,245,255,.5);box-shadow:0 0 22px rgba(0,245,255,.14), inset 0 0 22px rgba(0,245,255,.04);}
.pnh{display:flex;justify-content:space-between;align-items:center;padding:.6rem 1rem;border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(0,245,255,.08),transparent);}
.pnh span{font-size:1.08rem;font-weight:700;letter-spacing:.1em;}
.pnh em{font-style:normal;font-size:.8rem;font-weight:600;letter-spacing:.08em;color:var(--cy);border:1px solid rgba(0,245,255,.3);border-radius:6px;padding:.1rem .5rem;}
.pnh em.bad{color:var(--red);border-color:rgba(255,48,79,.5)}.pnh em.ok{color:var(--green);border-color:rgba(0,255,136,.4)}.pnh em.warn{color:var(--amber);border-color:rgba(255,176,0,.5)}
.pnb{padding:.7rem .85rem;}
.scroll{max-height:310px;overflow:auto;}
.pnb{overflow-x:auto}
.scroll::-webkit-scrollbar{width:6px}.scroll::-webkit-scrollbar-thumb{background:rgba(0,245,255,.3);border-radius:6px}

/* tables */
table.ct{width:100%;border-collapse:collapse;font-size:.95rem;}
table.ct th{white-space:nowrap;font-size:.72rem;font-weight:600;letter-spacing:.06em;color:var(--mut);text-align:left;padding:.45rem .45rem;border-bottom:1px solid rgba(0,245,255,.4);position:sticky;top:0;background:#0A151D;}
table.ct td{white-space:nowrap;padding:.4rem .55rem;border-bottom:1px solid rgba(0,245,255,.10);font-family:var(--mono);font-size:.88rem;transition:background .15s;}
table.ct tr:hover td{background:rgba(0,245,255,.07);}
table.ct td.pid{font-family:'Rajdhani',sans-serif;font-weight:700;font-size:1rem;}
table.ct td.nm{color:var(--green);}
table.ct td.cy{color:var(--cy);}
table.ct td.tx{font-family:'Rajdhani',sans-serif;font-size:.98rem;color:var(--tx);}
table.ct td.zero{color:#3C5566;}
table.ct tr.hl td{background:rgba(0,255,136,.10);}
.tag{display:inline-block;padding:.05rem .55rem;border-radius:6px;font-size:.78rem;font-weight:700;letter-spacing:.08em;font-family:'Rajdhani',sans-serif;border:1px solid}
.tag.pass{color:var(--green);border-color:rgba(0,255,136,.5);background:rgba(0,255,136,.08)}
.tag.fail{color:var(--red);border-color:rgba(255,48,79,.5);background:rgba(255,48,79,.08)}
.tag.wait{color:var(--amber);border-color:rgba(255,176,0,.5);background:rgba(255,176,0,.08)}
.tag.run{color:var(--cy);border-color:rgba(0,245,255,.5);background:rgba(0,245,255,.08)}
.bar{height:6px;border-radius:99px;background:#12303b;overflow:hidden;min-width:30px}.bar>div{height:100%;background:linear-gradient(90deg,var(--teal),var(--cy));box-shadow:0 0 8px var(--cy)}
.avail{margin-top:.55rem;font-size:.82rem;letter-spacing:.08em;color:var(--mut)}.avail b{font-family:var(--mono);color:var(--cy);font-size:.95rem;margin-left:.4rem}

/* checklist + chips */
.cl{list-style:none;margin:0;padding:0}
.cl li{display:flex;align-items:center;gap:.55rem;padding:.32rem .55rem;font-size:.92rem;white-space:nowrap;border:1px solid rgba(0,245,255,.12);border-radius:7px;margin-bottom:.35rem;background:rgba(0,245,255,.03);}
.cl li.last{border-color:rgba(0,255,136,.5);background:rgba(0,255,136,.08)}
.ic{width:20px;height:20px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:700;color:#04110B}
.ic.p{background:var(--green);box-shadow:0 0 8px rgba(0,255,136,.6)}.ic.f{background:var(--red);color:#fff;box-shadow:0 0 8px rgba(255,48,79,.6)}.ic.s{background:#33495a;color:#8297A8}
.sq-h{color:var(--cy);font-weight:700;letter-spacing:.06em;font-size:1.1rem;margin-bottom:.9rem}.sq-h span{color:var(--tx);font-weight:500}
.sq{display:flex;align-items:center;flex-wrap:wrap;gap:.2rem;padding:.4rem 0}
.chip{position:relative;min-width:50px;text-align:center;padding:.55rem .4rem;font-weight:700;font-size:1.12rem;border:2px solid var(--cy);border-radius:8px;color:var(--cy);background:rgba(0,245,255,.06);box-shadow:0 0 14px rgba(0,245,255,.4), inset 0 0 12px rgba(0,245,255,.12);margin:8px 3px;transition:transform .15s;}
.chip:hover{transform:translateY(-2px)}
.chip::before,.chip::after{content:"";position:absolute;left:7px;right:7px;height:6px;background:repeating-linear-gradient(90deg,var(--cy) 0 3px,transparent 3px 7px);opacity:.9}
.chip::before{top:-9px}.chip::after{bottom:-9px}
.chip.red{border-color:var(--red);color:var(--red);background:rgba(255,48,79,.07);box-shadow:0 0 14px rgba(255,48,79,.45), inset 0 0 12px rgba(255,48,79,.12)}
.chip.red::before,.chip.red::after{background:repeating-linear-gradient(90deg,var(--red) 0 3px,transparent 3px 7px)}
.chip.dim{border-color:#33495a;color:#5d7284;background:transparent;box-shadow:none}.chip.dim::before,.chip.dim::after{background:repeating-linear-gradient(90deg,#33495a 0 3px,transparent 3px 7px)}
.chip.cur{border-color:var(--green);color:var(--green);box-shadow:0 0 18px rgba(0,255,136,.55), inset 0 0 12px rgba(0,255,136,.15)}
.chip.cur::before,.chip.cur::after{background:repeating-linear-gradient(90deg,var(--green) 0 3px,transparent 3px 7px)}
.arw{width:24px;height:2px;background:var(--cy);position:relative;box-shadow:0 0 8px var(--cy);flex:none;margin:0 2px}
.arw::after{content:"";position:absolute;right:-1px;top:-4px;border-left:8px solid var(--cy);border-top:5px solid transparent;border-bottom:5px solid transparent}

/* graph */
.gwrap{display:flex;flex-direction:column;align-items:center}
.gwrap svg{width:100%;max-width:430px;height:auto}
.gl{font-weight:700;letter-spacing:.08em;text-align:center;line-height:1.35;margin-top:.1rem}
.gl.bad{color:var(--red);text-shadow:0 0 12px rgba(255,48,79,.5)}.gl.ok{color:var(--green)}.gl.mut{color:var(--mut);font-weight:500}
.nd{filter:drop-shadow(0 0 5px var(--cy))}.nd.dead{filter:drop-shadow(0 0 7px var(--red));animation:alertn 1.4s ease-in-out infinite}
@keyframes alertn{0%,100%{filter:drop-shadow(0 0 4px #FF304F)}50%{filter:drop-shadow(0 0 12px #FF304F)}}
.eg{filter:drop-shadow(0 0 3px rgba(0,245,255,.8))}.eg.cyc{filter:drop-shadow(0 0 4px rgba(255,48,79,.9))}

/* verdict, cards, notes */
.vd{border:1px solid var(--line);border-left:4px solid var(--mut);border-radius:9px;padding:.65rem .95rem;margin:.5rem 0;background:rgba(10,21,29,.9)}
.vd.safe{border-left-color:var(--green);box-shadow:0 0 14px rgba(0,255,136,.1)}.vd.unsafe{border-left-color:var(--amber);box-shadow:0 0 14px rgba(255,176,0,.1)}
.vd.dead{border-left-color:var(--red);box-shadow:0 0 14px rgba(255,48,79,.14)}.vd.wait{border-left-color:var(--cy)}.vd.invalid{border-left-color:var(--purple)}
.vd b{display:block;letter-spacing:.06em;font-size:1.02rem}.vd span{color:#B7C9D6;font-size:.95rem;line-height:1.45}
.cap{color:var(--mut);font-size:.95rem;line-height:1.5;margin:.15rem 0 .6rem;max-width:80ch}
.h2{font-size:.95rem;font-weight:700;letter-spacing:.14em;color:var(--cy);margin:1rem 0 .4rem}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:.8rem}
.pcard{border:1px solid var(--line);border-radius:12px;background:rgba(10,21,29,.9);padding:.75rem .9rem;transition:border-color .2s, transform .15s}
.pcard:hover{border-color:var(--cy);transform:translateY(-2px)}
.pcard .top{display:flex;justify-content:space-between;align-items:center;margin-bottom:.35rem}.pcard .top b{font-size:1.2rem;letter-spacing:.06em}
.pcard .r{display:grid;grid-template-columns:30px 1fr 54px;gap:.5rem;align-items:center;margin-top:.35rem;font-size:.85rem;color:var(--mut)}
.pcard .n{text-align:right;font-family:var(--mono);color:var(--green);font-size:.82rem}
.pcard .need{margin-top:.55rem;font-size:.82rem;color:var(--mut);letter-spacing:.06em}.pcard .need b{color:var(--cy);font-family:var(--mono)}
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:.8rem;margin-bottom:.4rem}
.cc{border:1px solid var(--line);border-radius:12px;background:rgba(10,21,29,.9);padding:.8rem 1rem;transition:border-color .2s}
.cc:hover{border-color:var(--cy)}
.cc b{display:block;font-size:1.1rem;letter-spacing:.06em;margin-bottom:.2rem}.cc span{font-size:.97rem;color:#B7C9D6;line-height:1.45}
.cc em{display:block;font-style:normal;font-size:.8rem;color:var(--teal);margin-top:.45rem;letter-spacing:.06em;font-weight:600}
.cc.k{border-top:2px solid var(--purple)}
.aim{border:1px solid rgba(0,245,255,.4);border-radius:12px;padding:.85rem 1.1rem;background:rgba(0,245,255,.06);line-height:1.5;font-size:1.02rem}
.formula{display:inline-block;font-family:var(--mono);font-size:1.4rem;font-weight:600;color:var(--cy);border:1px solid var(--cy);border-radius:10px;padding:.8rem 1.3rem;box-shadow:0 0 18px rgba(0,245,255,.3), inset 0 0 14px rgba(0,245,255,.08)}
.steps{counter-reset:s;list-style:none;padding:0;margin:0}
.steps li{counter-increment:s;display:flex;gap:.8rem;align-items:flex-start;border:1px solid var(--line);border-radius:9px;padding:.55rem .85rem;margin-bottom:.45rem;background:rgba(10,21,29,.9);font-size:1rem;line-height:1.45}
.steps li::before{content:counter(s);flex:none;width:24px;height:24px;border-radius:50%;background:var(--purple);color:#fff;font-weight:700;font-size:.82rem;display:flex;align-items:center;justify-content:center;box-shadow:0 0 8px rgba(217,70,239,.6)}
code{font-family:var(--mono);background:rgba(0,245,255,.1);color:var(--cy);padding:.05rem .35rem;border-radius:5px;font-size:.85rem}
.pill{display:inline-block;padding:.15rem .7rem;border-radius:999px;font-family:var(--mono);font-size:.88rem;color:var(--cy);border:1px solid rgba(0,245,255,.4);background:rgba(0,245,255,.06)}

/* streamlit widgets */
.stTabs [data-baseweb="tab-list"]{gap:.4rem;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{height:2.4rem;padding:0 1rem;font-weight:600;letter-spacing:.06em;color:var(--mut);}
.stTabs [aria-selected="true"]{color:var(--cy);text-shadow:0 0 10px rgba(0,245,255,.5)}
.stTabs [data-baseweb="tab-highlight"]{background:var(--cy);box-shadow:0 0 8px var(--cy)}
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="base-input"]{background:#0A151D !important;border-color:rgba(0,245,255,.25) !important;border-radius:8px !important}
.stButton>button, .stDownloadButton>button{border-radius:8px;border:1px solid rgba(0,245,255,.4);background:rgba(0,245,255,.05);color:var(--tx);font-weight:600;letter-spacing:.06em;transition:all .18s ease;}
.stButton>button:hover, .stDownloadButton>button:hover{border-color:var(--cy);box-shadow:0 0 14px rgba(0,245,255,.4);color:var(--cy);background:rgba(0,245,255,.1)}
.stButton>button[kind="primary"]{background:rgba(0,245,255,.16);border-color:var(--cy);color:var(--cy);box-shadow:0 0 12px rgba(0,245,255,.3)}
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{border:1px solid var(--line);border-radius:10px;overflow:hidden}
*:focus-visible{outline:2px solid var(--cy) !important;outline-offset:2px;}

/* ---- widgets: force dark even if the theme file was not loaded ---- */
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, .stApp label, .stApp [data-testid="stWidgetLabel"] p{color:var(--tx) !important;}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
[data-testid="stNumberInputContainer"], [data-testid="stTextInput"] > div > div, [data-testid="stNumberInput"] > div > div{background-color:#0A151D !important;border-color:rgba(0,245,255,.28) !important;border-radius:8px !important;}
[data-baseweb="input"] input, [data-baseweb="base-input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] input, [data-baseweb="select"] div{color:var(--tx) !important;-webkit-text-fill-color:var(--tx) !important;background-color:transparent !important;}
[data-baseweb="select"] svg, [data-testid="stNumberInput"] svg, [data-baseweb="input"] svg{fill:var(--cy) !important;color:var(--cy) !important;}
[data-testid="stNumberInput"] button{background:#0F2230 !important;border-color:rgba(0,245,255,.25) !important;color:var(--cy) !important;}
[data-baseweb="popover"] > div, [data-baseweb="menu"], [data-baseweb="popover"] ul{background:#0A151D !important;border:1px solid rgba(0,245,255,.3);}
[data-baseweb="popover"] li, [data-baseweb="menu"] li{background:#0A151D !important;color:var(--tx) !important;}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover, [data-baseweb="popover"] li[aria-selected="true"]{background:rgba(0,245,255,.14) !important;}
[data-testid="stExpander"] details{background:#0A151D !important;border:1px solid var(--line) !important;border-radius:10px !important;}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p{color:var(--tx) !important;}
[data-testid="stSidebar"] [data-testid="stSelectbox"] div{color:var(--tx) !important;}
.stSlider [data-baseweb="slider"] div[role="slider"]{background:var(--cy) !important;box-shadow:0 0 10px var(--cy)}
[data-testid="stToggle"] p, .stRadio p, .stCheckbox p{color:var(--tx) !important;}
[data-testid="stDownloadButton"] button, .stButton > button{background-color:rgba(0,245,255,.06) !important;color:var(--tx) !important;}
.stButton > button[kind="primary"]{background-color:rgba(0,245,255,.18) !important;color:var(--cy) !important;}
/* ---- current Streamlit layout (data-testid selectors) ---- */
[data-testid="stSelectbox"] [role="group"], [data-testid="stMultiSelect"] [role="group"], [data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"], [data-testid="stTextInput"] [role="group"]{background:#0A151D !important;background-color:#0A151D !important;border:1px solid rgba(0,245,255,.28) !important;border-radius:8px !important}
[data-testid="stSelectbox"] input, [data-testid="stSelectbox"] [role="combobox"], [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input{color:#E6F4FF !important;-webkit-text-fill-color:#E6F4FF !important;caret-color:#00F5FF;background:transparent !important}
[data-testid="stSelectbox"] svg, [data-testid="stSelectbox"] button{color:#00F5FF !important;fill:#00F5FF !important}
[data-testid="stSelectbox"] [role="group"] *{color:#E6F4FF}
[data-testid="stSelectboxVirtualDropdown"], [data-testid="stSelectboxVirtualDropdown"] > div{background:#0A151D !important;background-color:#0A151D !important;border:1px solid rgba(0,245,255,.3) !important;border-radius:8px}
[data-testid="stSelectboxVirtualDropdown"] *{color:#E6F4FF !important}
[data-testid="stSelectboxVirtualDropdown"] [role="option"] > div{background:transparent !important}
[data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover > div, [data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"] > div{background:rgba(0,245,255,.16) !important}
[data-testid="stTab"], [data-testid="stTab"] *{color:#8297A8 !important}
[data-testid="stTab"]:hover, [data-testid="stTab"]:hover *{color:#E6F4FF !important}
[data-testid="stTab"][aria-selected="true"], [data-testid="stTab"][aria-selected="true"] *{color:#00F5FF !important;text-shadow:0 0 10px rgba(0,245,255,.5)}
[data-testid="stTab"] > div:not([data-testid]){background-color:#00F5FF !important;box-shadow:0 0 8px #00F5FF}
[data-testid="stTabs"] [role="tablist"]{border-bottom:1px solid rgba(0,245,255,.2)}
[data-testid="stRadioOption"] p{color:#E6F4FF !important}
[data-testid="stSlider"] [role="slider"], [data-testid="stSlider"] [role="group"] > div > div:nth-child(2){background-color:#00F5FF !important;box-shadow:0 0 10px #00F5FF}
[data-testid="stSlider"] [data-testid="stSliderThumbValue"], [data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"]{color:#00F5FF !important}
[data-testid="stExpander"] summary{background:#0A151D !important;border-radius:9px}
[data-testid="stExpander"] summary:hover{background:rgba(0,245,255,.08) !important}
label:has(input[role="switch"]) > div:not([data-testid]){background-color:#1B3340 !important}
label:has(input[role="switch"]:checked) > div:not([data-testid]){background-color:#00D6B8 !important;box-shadow:0 0 8px rgba(0,214,184,.6)}
label:has(input[role="switch"]) > div:not([data-testid]) > div{background-color:#E6F4FF !important}
[data-testid="stRadioOption"] > div > div:first-child{background-color:#0A151D !important;border:2px solid #00F5FF !important}
[data-testid="stRadioOption"][data-selected="true"] > div > div:first-child{background-color:#00F5FF !important;box-shadow:0 0 8px rgba(0,245,255,.6)}
[data-testid="stRadioOption"] > div > div:first-child > div{background-color:#050B10 !important}
/* floating overlays: cell editor, menus */
#portal [role="dialog"], #portal [role="menu"]{background:#0A151D !important;color:#E6F4FF !important}
.gdg-style, .gdg-input, .gdg-clip-region, #portal textarea, #portal input{background:#0A151D !important;color:#E6F4FF !important;border-color:rgba(0,245,255,.4) !important}
.cfg-note{border:1px solid rgba(255,176,0,.5);border-left:4px solid var(--amber);border-radius:9px;padding:.55rem .9rem;margin-bottom:.8rem;background:rgba(255,176,0,.07);font-size:.95rem}
FALLBACK
ANIM
</style>
"""
FALLBACK_CSS = r"""
/* ---- tables and charts are drawn on a canvas, so they follow the Streamlit theme. When the dark theme file is missing, invert them to dark ---- */
[data-testid="stDataFrame"], [data-testid="stDataEditor"], [data-testid="stVegaLiteChart"]{filter:invert(.93) hue-rotate(180deg) saturate(1.15);background:#F5EAE2;}
[data-testid="stSlider"] [role="group"] > div > div:first-child{filter:hue-rotate(180deg) saturate(1.3);}
"""
GRID_ON = "background-image:linear-gradient(rgba(0,245,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(0,245,255,.035) 1px,transparent 1px);background-size:44px 44px;"
ANIM_OFF = "*{animation:none !important;transition:none !important}"
REDUCE = "@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}}"


# ====================================================================== state
for k, v in dict(anim=True, grid=True, labels="R0, R1, R2", det_mode="Deadlock example (3 processes in a ring)", term=[]).items():
    ss.setdefault(k, v)
LABELS = {"R0, R1, R2": [f"R{j}" for j in range(6)], "A, B, C": list("ABCDEF"),
          "CPU, RAM, GPU, I/O, HDD, NET": ["CPU", "RAM", "GPU", "I/O", "HDD", "NET"]}
st.markdown(CSS.replace("GRID", GRID_ON if ss["grid"] else "")
            .replace("FALLBACK", "" if DARK else FALLBACK_CSS).replace("ANIM", (ANIM_OFF if not ss["anim"] else "") + REDUCE), unsafe_allow_html=True)

# ====================================================================== helpers
fmt = lambda v: "(" + ", ".join(str(int(x)) for x in v) + ")"
vec = lambda v: "(" + ",".join(str(int(x)) for x in v) + ")"
def show(html): st.markdown(html, unsafe_allow_html=True)
def cap(t): show(f"<div class='cap'>{t}</div>")
def h2(t): show(f"<div class='h2'>{t}</div>")

def panel(title, body, tag="", tagcls=""):
    t = f"<em class='{tagcls}'>{tag}</em>" if tag else ""
    return f"<div class='pn'><div class='pnh'><span>{title}</span>{t}</div><div class='pnb'>{body}</div></div>"

def td(v, cls=""): return f"<td class='{cls}'>{v}</td>"
def num_td(v): return td(int(v), "nm" if v else "nm zero")
def table(headers, rows, hl=()):
    h = "<table class='ct'><tr>" + "".join(f"<th>{x}</th>" for x in headers) + "</tr>"
    for i, r in enumerate(rows):
        h += f"<tr{' class=hl' if i in hl else ''}>" + "".join(r) + "</tr>"
    return h + "</table>"

def matrix_html(rows, rlabels, clabels, hl=()):
    return table([""] + clabels, [[td(rlabels[i], "pid")] + [num_td(v) for v in r] for i, r in enumerate(rows)], hl)

def vd(kind, title, body=""):
    show(f"<div class='vd {kind}'><b>{title}</b><span>{body}</span></div>")

def chips(seq, cls=""):
    out = []
    for i, p in enumerate(seq):
        out.append(f"<div class='chip {cls}'>P{p}</div>")
        if i < len(seq) - 1: out.append("<div class='arw'></div>")
    return "<div class='sq'>" + "".join(out) + "</div>"

def checklist(res, last_cls_idx=None):
    sym = {"p": "✓", "f": "✕", "s": "–"}
    h = "<ul class='cl'>"
    for i, (txt, st_) in enumerate(res):
        cls = " class='last'" if (i == len(res) - 1 and st_ == "p") else ""
        h += f"<li{cls}><div class='ic {st_}'>{sym[st_]}</div>{txt}</li>"
    return h + "</ul>"

def svg_graph(n, edges, cycle=None, dead=(), blocked=(), uid="g"):
    import math
    W, H, R, r = 380, 300, 108, 25
    cx, cy = W / 2, H / 2 - 4
    pos = {i: (cx + R * math.sin(2*math.pi*i/max(n,1)), cy - R * math.cos(2*math.pi*i/max(n,1))) for i in range(n)}
    cyc = set(zip(cycle, cycle[1:])) if cycle else set()
    allp = [(e, "live") for e in edges if e not in blocked] + [(e, "blk") for e in edges if e in blocked]
    eset = set(edges)
    s = f"<svg viewBox='0 0 {W} {H}' xmlns='http://www.w3.org/2000/svg'><defs>"
    for nm, col in (("c", "#00F5FF"), ("r", "#FF304F"), ("g", "#8297A8")):
        s += f"<marker id='{uid}{nm}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill='{col}'/></marker>"
    s += "</defs>"
    for (i, k), kind in allp:
        (x1, y1), (x2, y2) = pos[i], pos[k]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1; ux, uy = dx / L, dy / L
        sx, sy, ex, ey = x1 + ux*(r+2), y1 + uy*(r+2), x2 - ux*(r+7), y2 - uy*(r+7)
        off = 16 if (k, i) in eset else 0
        mx, my = (sx+ex)/2 - uy*off, (sy+ey)/2 + ux*off
        if (i, k) in cyc: col, mk, w, cls, dash = "#FF304F", "r", 2.6, "eg cyc", ""
        elif kind == "blk": col, mk, w, cls, dash = "#8297A8", "g", 1.8, "", " stroke-dasharray='6 5'"
        else: col, mk, w, cls, dash = "#00F5FF", "c", 1.8, "eg", ""
        s += f"<path class='{cls}' d='M{sx:.1f} {sy:.1f} Q{mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}' fill='none' stroke='{col}' stroke-width='{w}'{dash} marker-end='url(#{uid}{mk})'/>"
    for i in range(n):
        x, y = pos[i]; d = i in dead
        col = "#FF304F" if d else "#00F5FF"
        s += (f"<g class='nd{' dead' if d else ''}'><circle cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{'rgba(255,48,79,.10)' if d else 'rgba(0,245,255,.07)'}' stroke='{col}' stroke-width='2.2'/>"
              f"<text x='{x:.1f}' y='{y+6:.1f}' text-anchor='middle' font-size='17' font-weight='700' fill='{col}' font-family='Rajdhani,sans-serif'>P{i}</text></g>")
    return "<div class='gwrap'>" + s + "</svg></div>"

# ====================================================================== scenarios + sidebar
TEXTBOOK = dict(alloc=[[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]],
                mx=[[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]], avail=[3,3,2])
BOUNDARY = dict(alloc=[[1,0,0],[0,1,0]], mx=[[2,1,0],[0,1,0]], avail=[0,0,0])
PRESETS = {"Textbook: 5 processes, 3 resources": TEXTBOOK,
           "Boundary: zero available, zero need": BOUNDARY,
           "Blank: enter your own": dict(alloc=[[0,0,0]]*3, mx=[[0,0,0]]*3, avail=[0,0,0])}
D_ALLOC = [[1,0,0],[0,1,0],[0,0,1]]
D_REQ = [[0,1,0],[0,0,1],[1,0,0]]
RING_NAMES = ["P0 holds the 1st resource and wants the 2nd", "P1 holds the 2nd and wants the 3rd", "P2 holds the 3rd and wants the 1st"]

with st.sidebar:
    show("<div class='brand'><div class='hex'><i></i></div><b>DEADLOCK</b></div>")
    show("<div class='side-h'>SCENARIO</div>")
    choice = st.selectbox("Load data", list(PRESETS), label_visibility="collapsed")
    p = PRESETS[choice]
    n = int(st.number_input("Processes", 1, 10, len(p["alloc"])))
    m = int(st.number_input("Resource types", 1, 6, len(p["avail"])))
    show("<div class='side-h'>DISPLAY</div>")
    with st.expander("Display settings"):
        st.toggle("Animations", value=ss["anim"], key="anim_w", on_change=lambda: ss.__setitem__("anim", ss["anim_w"]))
        st.toggle("Grid texture", value=ss["grid"], key="grid_w", on_change=lambda: ss.__setitem__("grid", ss["grid_w"]))
        _opts = list(LABELS)
        st.radio("Resource labels", _opts, index=_opts.index(ss["labels"]), key="labels_w", on_change=lambda: ss.__setitem__("labels", ss["labels_w"]))
    show("<div class='side-h'>SESSION</div>")
    if st.button("Reset session", width="stretch"):
        for k_ in list(ss.keys()): del ss[k_]
        st.rerun()

LB = LABELS[ss["labels"]]; CL = LB[:m]; RL = [f"P{i}" for i in range(n)]

def resize(rows, nn, mm):
    rows = [list(r)[:mm] + [0] * (mm - len(r)) for r in rows]
    return (rows + [[0] * mm for _ in range(nn)])[:nn]

skey = (choice, n, m)
if ss.get("skey") != skey:
    ss["skey"] = skey; ss["term"] = []; ss.pop("last_req", None)
    ss["store"] = dict(alloc=resize(p["alloc"], n, m), mx=resize(p["mx"], n, m),
                       avail=(list(p["avail"]) + [0] * m)[:m], req=[[0] * m for _ in range(n)])
store = ss["store"]
alloc, mx, avail = store["alloc"], store["mx"], store["avail"]

# ---------------------------------------------------------------- compute (every run, every page)
errs = validate_state(alloc, mx, avail)
sig = (str(alloc), str(mx), str(avail))
need, safe, seq, trace = None, False, [], []
if not errs:
    need = compute_need(alloc, mx)
    safe, seq, trace = is_safe(alloc, need, avail)

if ss.pop("do_req", False) and not errs:
    try: req_ = [int(x) for x in str(ss.get("rq_txt", "")).split(",")]
    except ValueError: req_ = None
    pid_ = int(ss.get("rq_pid", 0))
    res_ = ({"status": "INVALID", "reason": "The request must be whole numbers separated by commas, such as 1,0,2."}
            if req_ is None else request_resource(pid_, req_, alloc, mx, avail))
    ss["last_req"] = dict(sig=sig, pid=pid_, req=req_, res=res_)

if errs: av_kind, av_why = "invalid", errs[0]
elif safe: av_kind, av_why = "safe", "Safe sequence " + ", ".join(f"P{i}" for i in seq)
else: av_kind, av_why = "unsafe", "No complete safe sequence exists."
lr = ss.get("last_req")
if lr and lr["sig"] == sig and not errs:
    s_ = lr["res"]["status"]
    if s_ == "GRANTED": av_kind, av_why = "safe", "Last request granted."
    elif s_ == "DENIED_UNSAFE": av_kind, av_why = "unsafe", "Last request denied: it would make the state unsafe."
    elif s_ == "INVALID": av_kind, av_why = "invalid", lr["res"]["reason"]

own = ss["det_mode"].startswith("My")
if own: a0, r0, v0 = alloc, store["req"], avail
else: a0, r0, v0 = D_ALLOC, D_REQ, [0, 0, 0]
da, dr, dv = a0, r0, v0
for v_ in ss["term"]:
    da, dr, dv = terminate_process(v_, da, dr, dv)
dead, _ = detect_deadlock(da, dr, dv)
dedges = wait_for_edges(da, dr); dcyc = find_cycle(dedges)
dn, dm = len(da), len(da[0])
DL = LB[:dm]; DRL = [f"P{i}" for i in range(dn)]

if _cfg_written:
    show("<div class='cfg-note'><b>Dark theme file created.</b> Press Ctrl+C in the terminal and run <code>python -m streamlit run app.py</code> again for the full dark look.</div>")
elif not DARK:
    show("<div class='cfg-note'>The dark theme file is not being loaded. Run the app from the folder that contains <code>.streamlit/config.toml</code>.</div>")

# ---------------------------------------------------------------- status bar
def lamp(cls, label, on): return f"<div class='lm {cls}{' on' if on else ''}'><i></i>{label}</div>"
now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
show("<div class='sbar'><span class='t'>SYSTEM STATUS:</span>"
     + lamp("g", "SAFE STATE", av_kind == "safe") + lamp("a", "UNSAFE STATE", av_kind == "unsafe")
     + lamp("r", "DEADLOCK DETECTED", bool(dead)) + (lamp("v", "INVALID INPUT", True) if av_kind == "invalid" else "")
     + f"<span class='ts'>LAST ANALYSIS: {now}</span></div>")

# ---------------------------------------------------------------- shared panel builders
def sysmatrix_panel():
    if errs: return panel("SYSTEM MATRIX", "<div class='cap'>Fix the input errors on the Resource Matrix page.</div>", "INVALID", "bad")
    rows = []
    for i in range(n):
        order = f"#{seq.index(i)+1}" if i in seq else "–"
        rows.append([td(f"P{i}", "pid"), td(vec(alloc[i]), "nm"), td(vec(mx[i]), "cy"), td(vec(need[i]), "nm"), td(order, "tx")])
    body = "<div class='scroll'>" + table(["PID", "ALLOC", "MAX", "NEED", "ORDER"], rows) + "</div>"
    body += f"<div class='avail'>AVAILABLE<b>{fmt(avail)}</b></div>"
    return panel("SYSTEM MATRIX", body, f"{n} × {m}")

def allocation_panel():
    if errs: return panel("RESOURCE ALLOCATION TABLE", "<div class='cap'>Fix the input errors first.</div>", "INVALID", "bad")
    rows = [[td(f"P{i}", "pid"), td(CL[j], "cy"), num_td(alloc[i][j]), num_td(mx[i][j]), num_td(need[i][j])] for i in range(n) for j in range(m)]
    return panel("RESOURCE ALLOCATION TABLE", "<div class='scroll'>" + table(["PID", "RESOURCE", "ALLOCATED", "MAX", "REMAINING"], rows) + "</div>")

def graph_panel(uid="d"):
    svg = svg_graph(dn, dedges, dcyc, dead, uid=uid)
    if dead:
        txt = "<div class='gl bad'>DEADLOCK DETECTED<br>CYCLE FOUND: " + " → ".join(f"P{x}" for x in (dcyc or dead)) + "</div>"
        return panel("WAIT-FOR GRAPH", svg + txt, "ACTIVE CYCLES", "bad")
    txt = "<div class='gl ok'>NO DEADLOCK<br><span class='gl mut'>Every process can finish</span></div>" if dedges else "<div class='gl mut'>Nobody is waiting on anyone</div>"
    return panel("WAIT-FOR GRAPH", svg + txt, "CLEAR", "ok")

def bankers_panel():
    if errs: return panel("BANKER'S ALGORITHM ANALYSIS", "<div class='cap'>Fix the input errors first.</div>", "INVALID", "bad")
    any_ = len(seq) > 0
    steps = [("Compute the Need matrix", "p"), ("Initialize Work = Available", "p"),
             ("Find a process whose Need fits in Work", "p" if any_ else "f"),
             ("Release its Allocation back to Work", "p" if any_ else "s"),
             ("Repeat until all finish", "p" if safe else ("f" if any_ else "s")),
             ("Safe sequence generated" if safe else "No safe sequence exists", "p" if safe else "f")]
    left = checklist(steps)
    if safe:
        right = f"<div class='sq-h'>SAFE SEQUENCE <span>{' → '.join(f'P{i}' for i in seq)}</span></div>" + chips(seq)
        tag, tc = "SAFE", "ok"
    else:
        stuck = [i for i in range(n) if i not in seq]
        right = ("<div class='sq-h'>UNSAFE <span>only these can finish: " + (", ".join(f"P{i}" for i in seq) or "none") + "</span></div>"
                 + (chips(seq) if seq else "") + "<div class='sq'>" + "".join(f"<div class='chip red'>P{i}</div>" for i in stuck) + "</div>")
        tag, tc = "UNSAFE", "warn"
    body = f"<div style='display:grid;grid-template-columns:auto 1fr;gap:1.4rem;align-items:center'><div>{left}</div><div>{right}</div></div>"
    return panel("BANKER'S ALGORITHM ANALYSIS", body, tag, tc)

def util_panel():
    if errs: return panel("RESOURCE UTILIZATION", "<div class='cap'>Fix the input errors first.</div>", "INVALID", "bad")
    rows = []
    for j in range(m):
        used = sum(alloc[i][j] for i in range(n)); tot = used + avail[j]
        pct = 100 * used / tot if tot else 0
        rows.append([td(CL[j], "pid"), num_td(tot), num_td(used), num_td(avail[j]), td(f"<div class='bar'><div style='width:{pct:.0f}%'></div></div>", "")])
    return panel("RESOURCE UTILIZATION", table(["RESOURCE", "TOTAL", "ALLOCATED", "AVAILABLE", "USED"], rows))

def editor(df, key):
    out = st.data_editor(df, key=key, width="stretch")
    return out.fillna(0).astype(int).values.tolist()

# ====================================================================== pages
tabs = st.tabs(["Overview", "Banker's algorithm", "Request", "Deadlock detection", "Prevention", "Test results", "Concepts"])

# ---------------- Overview ----------------
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        h2("ALLOCATION: WHAT EACH PROCESS HOLDS")
        new_alloc = editor(pd.DataFrame(alloc, index=RL, columns=CL), f"ed_al|{skey}")
    with c2:
        h2("MAXIMUM: THE MOST EACH MAY ASK FOR")
        new_mx = editor(pd.DataFrame(mx, index=RL, columns=CL), f"ed_mx|{skey}")
    h2("AVAILABLE: FREE INSTANCES RIGHT NOW")
    new_av = editor(pd.DataFrame([avail], index=["FREE"], columns=CL), f"ed_av|{skey}")[0]
    if (new_alloc, new_mx, new_av) != (alloc, mx, avail):
        store.update(alloc=new_alloc, mx=new_mx, avail=new_av); st.rerun()
    if errs:
        vd("invalid", "INVALID INPUT", "<br>".join(errs))
    else:
        vd("safe", "INPUT IS VALID", "Edit any cell. Every page recalculates from these numbers.")
        a_, _ = st.columns([1, 1])
        a_.markdown(panel("NEED = MAXIMUM − ALLOCATION", matrix_html(need, RL, CL)), unsafe_allow_html=True)


with tabs[0]:
    h2("SYSTEM OVERVIEW")
    c1, c2, c3 = st.columns([1.1, 1.05, 1.2])
    c1.markdown(sysmatrix_panel(), unsafe_allow_html=True)
    c2.markdown(graph_panel("dash"), unsafe_allow_html=True)
    c3.markdown(allocation_panel(), unsafe_allow_html=True)
    c4, c5 = st.columns([1.75, 1])
    c4.markdown(bankers_panel(), unsafe_allow_html=True)
    c5.markdown(util_panel(), unsafe_allow_html=True)


with tabs[0]:
    h2("PROCESS STATUS")
    cap("Each card shows what a process holds out of its declared maximum, and whether its remaining Need fits in the free resources right now.")
    if errs:
        vd("invalid", "INVALID INPUT", "<br>".join(errs))
    else:
        cards = "<div class='pgrid'>"
        for i in range(n):
            runnable = vec_le(need[i], avail)
            tag = "<span class='tag run'>CAN RUN NOW</span>" if runnable else "<span class='tag wait'>WAITING</span>"
            order = f"<span class='tag pass'>SAFE ORDER #{seq.index(i)+1}</span>" if i in seq else "<span class='tag fail'>NOT IN SAFE ORDER</span>"
            cards += f"<div class='pcard'><div class='top'><b>P{i}</b>{tag}</div>"
            for j in range(m):
                pct = 100 * alloc[i][j] / mx[i][j] if mx[i][j] else 0
                cards += f"<div class='r'><span>{CL[j]}</span><div class='bar'><div style='width:{min(pct,100):.0f}%'></div></div><span class='n'>{alloc[i][j]}/{mx[i][j]}</span></div>"
            cards += f"<div class='need'>NEED<b> {fmt(need[i])}</b></div><div style='margin-top:.5rem'>{order}</div></div>"
        show(cards + "</div>")


# ---------------- other tabs ----------------
if True:
    t1, t2 = tabs[1], tabs[2]
    with t1:
        if errs:
            vd("invalid", "INVALID INPUT", "Fix the errors on the Resource Matrix page first.")
        else:
            a_, b_ = st.columns([1, 1.4])
            a_.markdown(panel("NEED MATRIX", matrix_html(need, RL, CL)), unsafe_allow_html=True)
            b_.markdown(bankers_panel(), unsafe_allow_html=True)
            h2("STEP THROUGH THE SAFETY CHECK")
            cap("A process can run when its Need fits inside Work. When it finishes, it returns what it holds to Work. Move the slider to replay each step.")
            k = st.slider("Step", 0, len(trace), 0, label_visibility="collapsed") if trace else 0
            done = seq[:k]; cur = seq[k-1] if k else None
            ch = "<div class='sq'>" + "".join(
                f"<div class='chip {'cur' if i == cur else '' if i in done else ('red' if (k == len(trace) and not safe) else 'dim')}'>P{i}</div>"
                for i in range(n)) + "</div>"
            l_, r_ = st.columns([1.3, 1])
            with l_:
                show(ch)
                if k:
                    t = trace[k-1]
                    cap(f"<b>{t['process']}</b> can run: its Need {fmt(t['Need'])} fits inside Work {fmt(t['Work before'])}. It finishes and returns its Allocation, so Work becomes {fmt(t['Work after'])}.")
                else:
                    cap(f"Start: Work equals Available, {fmt(avail)}.")
                if trace and k == len(trace) and not safe:
                    cap("The red processes cannot continue: each Need is larger than Work, and no process left can run.")
                show(f"<div class='pill'>WORK {fmt(trace[k-1]['Work after'] if k else avail)}</div>")
            with r_:
                hist = [avail] + [t["Work after"] for t in trace]
                st.line_chart(pd.DataFrame(hist[:k+1], columns=CL, index=["Start"] + [t["process"] for t in trace][:k]), height=200)
            if trace:
                rows = [[td(i, "tx"), td(t["process"], "pid"), td(fmt(t["Need"]), "nm"), td(fmt(t["Work before"]), "cy"), td(fmt(t["Work after"]), "nm")] for i, t in enumerate(trace, 1)]
                show(panel("FULL TRACE", table(["STEP", "PROCESS", "NEED", "WORK BEFORE", "WORK AFTER"], rows)))
    with t2:
        if errs:
            vd("invalid", "INVALID INPUT", "Fix the errors on the Resource Matrix page first.")
        else:
            if "rq_pid" not in ss: ss["rq_pid"] = 0
            if "rq_txt" not in ss: ss["rq_txt"] = ",".join(["0"] * m)
            def set_req(pid, txt): ss["rq_pid"] = pid; ss["rq_txt"] = txt; ss["do_req"] = True
            def go_req(): ss["do_req"] = True
            left, right = st.columns([1, 1.3])
            with left:
                h2("MAKE A REQUEST")
                st.number_input("Process number", -5, 50, key="rq_pid")
                st.text_input(f"Request: {m} numbers, comma separated", key="rq_txt")
                st.button("Check request", type="primary", width="stretch", on_click=go_req)
                if choice == list(PRESETS)[0]:
                    h2("QUICK EXAMPLES")
                    b = st.columns(2)
                    b[0].button("Granted", on_click=set_req, args=(1, "1,0,2"), width="stretch")
                    b[1].button("Must wait", on_click=set_req, args=(0, "7,4,3"), width="stretch")
                    b[0].button("Unsafe", on_click=set_req, args=(4, "3,3,0"), width="stretch")
                    b[1].button("Invalid", on_click=set_req, args=(9, "0,0,0"), width="stretch")
            with right:
                h2("DECISION")
                names = ["Request is valid", "Within the process's Need", "Resources are free right now", "State stays safe after granting"]
                if not (lr and lr["sig"] == sig):
                    cap("Submit a request or press an example. The four checks run in this order and stop at the first one that fails.")
                    show(panel("CHECKS", checklist([(x, "s") for x in names])))
                else:
                    res, pid_ = lr["res"], lr["pid"]; s_ = res["status"]
                    code = {"GRANTED": "pppp", "DENIED_UNSAFE": "pppf", "WAIT": "ppfs"}.get(s_, "pfss" if "exceeds" in res.get("reason", "") else "fsss")
                    show(panel("CHECKS", checklist(list(zip(names, code)))))
                    if s_ == "GRANTED":
                        vd("safe", "GRANTED", "The state after granting is safe. Safe sequence: " + ", ".join(f"P{i}" for i in res["sequence"]) + ".")
                    elif s_ == "WAIT":
                        vd("wait", "NOT GRANTED YET: THE PROCESS MUST WAIT", res["reason"])
                    elif s_ == "DENIED_UNSAFE":
                        vd("unsafe", "DENIED: GRANTING WOULD MAKE THE STATE UNSAFE", res["reason"])
                    else:
                        vd("invalid", "INVALID REQUEST", res["reason"])
            if lr and lr["sig"] == sig:
                res, pid_ = lr["res"], lr["pid"]; s_ = res["status"]
                if s_ == "GRANTED":
                    x1, x2 = st.columns(2)
                    x1.markdown(panel("NEW ALLOCATION", matrix_html(res["new_alloc"], RL, CL, hl=(pid_,))), unsafe_allow_html=True)
                    x2.markdown(panel("NEW AVAILABLE", f"<span class='pill'>{fmt(res['new_avail'])}</span>"), unsafe_allow_html=True)
                elif s_ == "DENIED_UNSAFE":
                    x1, x2, x3 = st.columns(3)
                    x1.markdown(panel("IF IT HAD BEEN GRANTED", matrix_html(res["simulated_alloc"], RL, CL, hl=(pid_,))), unsafe_allow_html=True)
                    x2.markdown(panel("AVAILABLE WOULD BE", f"<span class='pill'>{fmt(res['simulated_avail'])}</span>"), unsafe_allow_html=True)
                    x3.markdown(panel("ORIGINAL, RESTORED", matrix_html(alloc, RL, CL)), unsafe_allow_html=True)
                elif s_ == "WAIT":
                    cap("The request is legitimate, so this is not an error. The allocation is exactly as it was.")


if True:
    t1, t2 = tabs[3], tabs[4]
    with t1:
        cap("Detection is separate from Banker's. It does not ask “is this request safe?”. It asks “is anyone stuck right now?”, using what each process holds and what it is waiting for.")
        def set_mode(): ss["det_mode"] = ss["det_mode_w"]; ss["term"] = []
        modes = ["Deadlock example (3 processes in a ring)", "My own request matrix"]
        st.radio("Data", modes, index=modes.index(ss["det_mode"]), key="det_mode_w", on_change=set_mode, horizontal=True, label_visibility="collapsed")
        if own:
            h2("WAITING FOR: EDIT WHAT EACH PROCESS IS REQUESTING")
            newreq = editor(pd.DataFrame(store["req"], index=RL, columns=CL), f"ed_rq|{skey}")
            if newreq != store["req"]:
                store["req"] = newreq; ss["term"] = []; st.rerun()
        x1, x2 = st.columns(2)
        x1.markdown(panel("HOLDS", matrix_html(da, DRL, DL)), unsafe_allow_html=True)
        x2.markdown(panel("WAITING FOR", matrix_html(dr, DRL, DL)), unsafe_allow_html=True)
        if ss["term"]: cap("Terminated so far: " + ", ".join(f"P{x}" for x in ss["term"]) + ".")
        if dead:
            vd("dead", "DEADLOCK DETECTED", "Stuck together: " + ", ".join(f"P{i}" for i in dead) + ". Each is waiting for a resource that another stuck process holds.")
        else:
            vd("safe", "NO DEADLOCK", "Every process can eventually get what it needs and finish.")
        g1, g2 = st.columns([1, 1])
        g1.markdown(graph_panel("det"), unsafe_allow_html=True)
        with g2:
            h2("CYCLE OR DEADLOCK?")
            cap("With one instance of each resource, a cycle means confirmed deadlock. With several instances a cycle only shows a possible deadlock, so the detection algorithm makes the final call.")
            if dead:
                h2("RECOVERY: END ONE PROCESS")
                victim = st.selectbox("Process to terminate", dead, format_func=lambda i: f"P{i}", label_visibility="collapsed")
                if st.button("Terminate and release its resources", type="primary"):
                    ss["term"].append(victim); st.rerun()
            if ss["term"] and st.button("Reset example"):
                ss["term"] = []; st.rerun()
    with t2:
        cap(f"Rule added: resources must be requested in increasing order ({LB[0]}, then {LB[1]}, then {LB[2]}). A process holding a later resource cannot ask for an earlier one, so a circular wait can never close.")
        ed = wait_for_edges(D_ALLOC, D_REQ)
        blocked_p = [i for i in range(3) if ordering_violation(D_ALLOC[i], D_REQ[i])]
        blocked = {(i, k) for (i, k) in ed if i in blocked_p}
        y1, y2 = st.columns(2)
        y1.markdown(panel("BEFORE: ANY ORDER ALLOWED", svg_graph(3, ed, find_cycle(ed), {0, 1, 2}, uid="pb")
                          + "<div class='gl bad'>CIRCULAR WAIT IS POSSIBLE<br><span class='gl mut'>P0, P1 and P2 each wait for the next one</span></div>", "DEADLOCK", "bad"), unsafe_allow_html=True)
        y2.markdown(panel("AFTER: RESOURCE ORDERING", svg_graph(3, ed, None, (), blocked, uid="pa")
                          + "<div class='gl ok'>CIRCULAR WAIT REMOVED<br><span class='gl mut'>Dashed arrows are blocked: " + ", ".join(f"P{i}" for i in blocked_p) + "</span></div>", "PREVENTED", "ok"), unsafe_allow_html=True)
        h2("WHAT IT COSTS")
        cap("Lower concurrency: a blocked process must release what it holds and ask again in order. Resources can sit idle longer, because processes sometimes have to acquire them earlier than they need them.")


if True:
    t1, t2 = tabs[5], tabs[6]
    with t1:
        cap("Computed live by the same code the dashboard uses, on fixed textbook data. Copy these into Section 3 of your worksheet and add your own analysis.")
        T = TEXTBOOK; nd = compute_need(T["alloc"], T["mx"]); snap = copy.deepcopy(T)
        s1, q1, _ = is_safe(T["alloc"], nd, T["avail"])
        r2 = request_resource(0, [7,4,3], T["alloc"], T["mx"], T["avail"])
        r3 = request_resource(4, [3,3,0], T["alloc"], T["mx"], T["avail"])
        d4, _ = detect_deadlock(D_ALLOC, D_REQ, [0,0,0])
        e5 = [(i, k) for (i, k) in wait_for_edges(D_ALLOC, D_REQ) if not ordering_violation(D_ALLOC[i], D_REQ[i])]
        c6 = [request_resource(9, [0,0,0], T["alloc"], T["mx"], T["avail"])["status"],
              request_resource(1, [-1,0,0], T["alloc"], T["mx"], T["avail"])["status"],
              request_resource(1, [1,0,0], T["alloc"], T["mx"], [0,0,0])["status"],
              request_resource(3, [0,0,0], T["alloc"], T["mx"], T["avail"])["status"]]
        rows_ = [
            ("TC1", "Safe state", ("Safe sequence " + ", ".join(f"P{i}" for i in q1)) if s1 else "Unsafe", "Safe sequence found", s1),
            ("TC2", "Request exceeds Available (P0 asks 7,4,3)", r2["status"] + ", state unchanged", "Request not granted immediately", r2["status"] == "WAIT"),
            ("TC3", "Request makes state unsafe (P4 asks 3,3,0)", r3["status"] + ", state restored", "Request denied; state unchanged", r3["status"] == "DENIED_UNSAFE" and T == snap),
            ("TC4", "Deadlocked scenario (ring of 3)", "Deadlocked: " + ", ".join(f"P{i}" for i in d4), "Deadlock identified", d4 == [0, 1, 2]),
            ("TC5", "Prevention: resource ordering", f"Waits left in the ring: {len(e5)} of 3, no cycle", "Selected condition eliminated", find_cycle(e5) is None),
            ("TC6", "Invalid id, negative, zero available, zero request", " / ".join(c6), "Correct handling or validation message", c6 == ["INVALID", "INVALID", "WAIT", "GRANTED"]),
        ]
        trs = [[td(t[0], "pid"), td(t[1], "tx"), td(t[2], "tx"), td(t[3], "tx"),
                td("<span class='tag pass'>PASS</span>" if t[4] else "<span class='tag fail'>FAIL</span>", "")] for t in rows_]
        show(panel("TEST CASES TC1 TO TC6", table(["TEST", "CONDITION", "ACTUAL RESULT", "EXPECTED", "MATCH"], trs),
                   "ALL PASS" if all(t[4] for t in rows_) else "FAILURES", "ok" if all(t[4] for t in rows_) else "bad"))
        st.download_button("Download as CSV", pd.DataFrame([t[:4] for t in rows_], columns=["Test", "Condition", "Actual result", "Expected"]).to_csv(index=False),
                           "test_results.csv", "text/csv")
    with t2:
        show("<div class='aim'><b>ACTIVITY AIM.</b> Build an interactive dashboard that analyzes multi-instance resource allocation, checks safe states with Banker's Algorithm, evaluates resource requests, and shows deadlock detection, prevention and recovery.</div>")
        h2("CORE TERMS")
        terms = [("Process", "A program currently loaded and executing in memory.", "Rows P0, P1, ... in every table"),
                 ("Resource", "A physical or logical entity a process needs to make progress, such as CPU, memory, printers or mutex locks.", "Columns of every matrix"),
                 ("Deadlock", "A state where a set of processes are permanently blocked, because each holds a resource and waits for one held by another process in the set.", "Deadlock Analysis page"),
                 ("Allocation", "The number of instances of each resource type currently assigned to each process.", "Resource Matrix page"),
                 ("Maximum", "The declared peak number of instances a process may ever request during execution.", "Resource Matrix page"),
                 ("Need", "The instances a process still requires to finish and release what it holds.", "Banker's Algorithm page"),
                 ("Available", "The instances of each type currently free in the unallocated pool.", "Resource Matrix page")]
        show("<div class='cgrid'>" + "".join(f"<div class='cc'><b>{t}</b><span>{d}</span><em>{w}</em></div>" for t, d, w in terms) + "</div>")
        h2("THE GOVERNING FORMULA")
        show("<div class='formula'>Need = Maximum − Allocation</div>")
        cap("Applied to every process <code>i</code> and every resource <code>j</code>: <code>Need[i][j] = Max[i][j] − Allocation[i][j]</code>.")
        h2("BANKER'S ALGORITHM: EXECUTION RULES")
        show("<ol class='steps'>"
             "<li><div><b>Compute the Need matrix.</b> <code>Need[i][j] = Max[i][j] − Allocation[i][j]</code> for all processes i and resources j.</div></li>"
             "<li><div><b>Initialize Work and Finish.</b> Set <code>Work = Available</code> and <code>Finish[i] = False</code> for every i from 0 to n−1.</div></li>"
             "<li><div><b>Find a candidate process.</b> Look for an i where <code>Finish[i] == False</code> and <code>Need[i] ≤ Work</code>.</div></li>"
             "<li><div><b>Simulate completion and release.</b> Assume Pi runs to completion and releases what it holds: <code>Work = Work + Allocation[i]</code>, <code>Finish[i] = True</code>.</div></li>"
             "<li><div><b>Iterate.</b> Repeat steps 3 and 4 until every process has finished or no eligible process remains.</div></li>"
             "<li><div><b>Read the result.</b> If all finish, the system is <b>safe</b> and the order of completion is the <b>safe sequence</b>. Otherwise it is unsafe.</div></li></ol>")
        h2("CLASSROOM EXAMPLE: SAFE SEQUENCES")
        cap("The same data can have several valid safe sequences. The first is the classroom answer. The second is the one this dashboard finds, because it scans processes from P0 upward.")
        z1, z2 = st.columns(2)
        z1.markdown(panel("CLASSROOM ANSWER", chips([1, 3, 4, 0, 2])), unsafe_allow_html=True)
        z2.markdown(panel("DASHBOARD ANSWER", chips([1, 3, 0, 2, 4])), unsafe_allow_html=True)
        h2("FOUR NECESSARY CONDITIONS FOR DEADLOCK (COFFMAN)")
        cap("Deadlock can arise only if all four hold at the same time. Remove any one and it cannot happen.")
        cond = [("Mutual exclusion", "At least one resource is held in a non-shareable mode: only one process can use it at a time.", ""),
                ("Hold and wait", "A process holds at least one resource while waiting to acquire more resources held by other processes.", ""),
                ("No preemption", "Resources cannot be forcibly taken from a process. They are released only voluntarily, after it finishes.", ""),
                ("Circular wait", "A closed chain of processes exists: P0 waits for P1, P1 waits for P2, and so on until Pn waits for P0.", "Drawn in red on the wait-for graph")]
        show("<div class='cgrid'>" + "".join(f"<div class='cc k'><b>{t}</b><span>{d}</span>{'<em>' + w + '</em>' if w else ''}</div>" for t, d, w in cond) + "</div>")
        h2("FOUR DEADLOCK HANDLING STRATEGIES")
        strat = [("Avoidance", "Checks every incoming request before allocating. Grants it only if the resulting state is guaranteed safe, as Banker's Algorithm does. Needs advance knowledge of maximum claims.", "Banker's Algorithm page"),
                 ("Detection", "Reactively inspects the actual current state, using wait-for graphs and detection matrices, to find processes that are deadlocked right now.", "Deadlock Analysis page"),
                 ("Recovery", "Corrective action after deadlock is detected, such as terminating one or more processes or preempting resources to break the cycle.", "Terminate button, Deadlock Analysis"),
                 ("Prevention", "Sets fixed rules on how requests are made, so at least one Coffman condition can never hold. Strict linear resource ordering removes circular wait.", "Prevention tab, Deadlock Analysis")]
        show("<div class='cgrid'>" + "".join(f"<div class='cc'><b>{t}</b><span>{d}</span><em>{w}</em></div>" for t, d, w in strat) + "</div>")
        cap("Avoidance looks ahead at a request. Detection looks at what is stuck now. They are separate functions in this dashboard on purpose.")