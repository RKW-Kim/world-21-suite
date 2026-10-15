#!/usr/bin/env python3
"""Drive the vendored /studio replica through a real browser (CDP) and verify
every action lands in OBS 1:1 via obs-websocket. Stdlib only.

Run from repo root:  python3 station/test_studio_ui.py [--part 1|2]
- Part 1: boot/connect, scenes, sources, mixer, transitions, studio, undo.
- Part 2: properties/filters/settings dialogs, add/remove flow, menus,
  outputs, status bar.
Leaves the loop as found (program Meet, volumes/mutes restored, no residue).
Exit code 0 = all green.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import daemon

daemon.load_secrets()
OBS = daemon.OBSRenderer()
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append(bool(cond))
    print("%-46s %s %s" % (name, "ok" if cond else "FAIL", detail), flush=True)


# ------------------------------------------------------------------ CDP ---
class CDP:
    def __init__(self, wsurl, port):
        u = urllib.parse.urlparse(wsurl)
        self.s = socket.create_connection((u.hostname, u.port), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nUpgrade: websocket\r\n"
                        "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
                        "Sec-WebSocket-Version: 13\r\n\r\n" % (u.path, port, key)).encode())
        head = b""
        while b"\r\n\r\n" not in head:
            head += self.s.recv(4096)
        assert b" 101 " in head
        self.buf, self.seq = b"", 0

    def _send(self, obj):
        payload = json.dumps(obj).encode()
        mask = os.urandom(4)
        n = len(payload)
        hdr = bytes([0x81, 0x80 | n]) if n < 126 else bytes([0x81, 0x80 | 126]) + struct.pack(">H", n)
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def _recv(self):
        while True:
            while len(self.buf) < 2:
                self.buf += self.s.recv(65536)
            b1, b2 = self.buf[0], self.buf[1]
            ln, off = b2 & 0x7F, 2
            if ln == 126:
                while len(self.buf) < 4:
                    self.buf += self.s.recv(65536)
                ln, off = struct.unpack(">H", self.buf[2:4])[0], 4
            while len(self.buf) < off + ln:
                self.buf += self.s.recv(65536)
            payload, op = self.buf[off:off + ln], b1 & 0x0F
            self.buf = self.buf[off + ln:]
            if op == 0x8:
                raise RuntimeError("cdp close")
            if op != 0x1:
                continue
            return json.loads(payload.decode())

    def call(self, method, params=None, timeout=25):
        self.seq += 1
        i = self.seq
        self._send({"id": i, "method": method, "params": params or {}})
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = self._recv()
            if m.get("id") == i:
                if "error" in m:
                    raise RuntimeError("cdp: %s" % m["error"])
                return m.get("result", {})
        raise RuntimeError("cdp timeout " + method)

    def ev(self, js, timeout=25):
        r = self.call("Runtime.evaluate", {"expression": js, "returnByValue": True}, timeout)
        if r.get("exceptionDetails"):
            raise RuntimeError("js: %s" % str(r["exceptionDetails"])[:200])
        return (r.get("result") or {}).get("value")

    def wait_for(self, js, timeout=60, poll=1.5):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                if self.ev(js, timeout=10):
                    return True
            except Exception:
                pass
            time.sleep(poll)
        return False


def launch(port):
    import shutil
    prof = "/tmp/opencode/chrome-%d" % port
    shutil.rmtree(prof, ignore_errors=True)
    os.makedirs(prof, exist_ok=True)
    p = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--window-size=1600,900",
         "--user-data-dir=" + prof,
         "--remote-debugging-port=%d" % port, "--remote-debugging-address=127.0.0.1",
         "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=2).read()
            return p
        except Exception:
            time.sleep(1)
    p.kill()
    raise RuntimeError("debugger never came up")


CHROME = "chromium"


def ocall(req, data=None, tries=4):
    last = None
    for _ in range(tries):
        try:
            return OBS._call(req, data)
        except Exception as e:
            last = e
            time.sleep(4)
    raise last


# ------------------------------------------------------- ui primitives ---
NSET = """(el, v) => {
  const desc = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
  desc.set.call(el, v);
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  return true;
}"""

CLICK_LEAF = """((scope, text) => {
  const root = scope ? document.querySelector(scope) : document;
  if (!root) return 'noroot';
  const el = [...root.querySelectorAll('*')].find(e => e.children.length === 0 && (e.textContent || '').trim() === text);
  if (!el) return 'missing';
  el.click();
  return 'clicked';
})"""

CLICK_TIP = """((scope, tip) => {
  const root = scope ? document.querySelector(scope) : document;
  if (!root) return 'noroot';
  const all = [...root.querySelectorAll('button,.dock-btn,[role=button]')];
  const el = all.find(b => ((b.title || '') + ' ' + (b.getAttribute('data-tip') || '') + ' ' + (b.getAttribute('aria-label') || '')).toLowerCase().indexOf(tip.toLowerCase()) >= 0);
  if (!el) return 'missing';
  el.click();
  return 'clicked';
})"""

MDOWN_ROW = """((scope, text) => {
  const root = document.querySelector(scope);
  if (!root) return 'noroot';
  const rows = [...root.querySelectorAll('.qlist-row')];
  const el = rows.find(e => (e.textContent || '').trim().indexOf(text) === 0 || (e.textContent || '').trim() === text);
  if (!el) return 'missing';
  el.dispatchEvent(new MouseEvent('mousedown', {button: 0, bubbles: true}));
  return 'down';
})"""

VIS_INPUT = """((sel) => {
  const el = [...document.querySelectorAll(sel)].find(e => e.offsetParent);
  return el ? 'found' : 'missing';
})"""


def vis_input(cdp, sel):
    return cdp.ev("(%s)(%r)" % (VIS_INPUT, sel))

def boot(port=9231):
    chrome = launch(port)
    req = urllib.request.Request("http://127.0.0.1:%d/json/new" % port, method="PUT")
    t = json.load(urllib.request.urlopen(req, timeout=10))
    cdp = CDP(t["webSocketDebuggerUrl"], port)
    cdp.call("Page.navigate", {"url": "http://127.0.0.1:7070/studio/"})
    return chrome, cdp


def wait_connected(cdp, timeout=90):
    return cdp.wait_for(
        "document.body.innerText.indexOf('WebSocket: Connected') >= 0", timeout)


def obs_program():
    return ocall("GetCurrentProgramScene")["currentProgramSceneName"]


def dlg_fill_ok(cdp, value):
    """Fill the last visible text input on the page, press its dialog OK."""
    v = "null" if value is None else repr(value)
    return cdp.ev("""(() => {
      const inps = [...document.querySelectorAll('input')].filter(i => i.offsetParent && ['text', '', 'search'].indexOf(i.type) >= 0);
      const inp = inps[inps.length - 1];
      let out = 'inputs=' + inps.length;
      if (inp && %s !== null) {
        const desc = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
        desc.set.call(inp, %s);
        inp.dispatchEvent(new Event('input', {bubbles: true}));
        inp.dispatchEvent(new Event('change', {bubbles: true}));
        out += ' filled=' + inp.value;
      }
      const box = inp ? inp.closest('div.qwin,div[class*=dlg],div[class*=modal],div[class*=dialog],div[class*=menu]') : null;
      const scope = box || document;
      const ok = [...scope.querySelectorAll('button')].find(b => b.textContent.trim() === 'OK' && b.offsetParent)
        || [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'OK' && b.offsetParent);
      if (ok) ok.click();
      return out + (ok ? ' ok' : ' nook');
    })()""" % (v, v))


def dlg_close(cdp):
    cdp.ev("""(() => {
      const b = [...document.querySelectorAll('button')].find(x => ['Cancel', 'Close', 'Done'].indexOf(x.textContent.trim()) >= 0 && x.offsetParent);
      if (b) b.click(); return !!b;
    })()""")


def scene_names():
    return [s["sceneName"] for s in ocall("GetSceneList")["scenes"]]


def cleanup_scratch():
    import re
    try:
        for s in [x["sceneName"] for x in ocall("GetSceneList")["scenes"]]:
            if re.match(r"^(CONFORM|Scene \d+$)", s):
                try:
                    OBS._call("RemoveScene", {"sceneName": s})
                except Exception:
                    pass
        for i in [x["inputName"] for x in ocall("GetInputList")["inputs"]]:
            if i.startswith("CONFORM"):
                try:
                    OBS._call("RemoveInput", {"inputName": i})
                except Exception:
                    pass
    except Exception:
        pass


# --------------------------------------------------------------- part 1 ---
def part1():
    chrome, cdp = boot()
    cleanup_scratch()
    try:
        check("boot: page loads", cdp.wait_for("document.title.length > 0", 20))
        check("connect: status Connected", wait_connected(cdp))
        if not RESULTS[-1]:
            return
        check("sync: SMILE scenes listed",
              cdp.wait_for("document.getElementById('dock-scenes').textContent.indexOf('SMILE | Meet') >= 0", 120))
        # toolbar tip diagnostics (one line, aids future runs)
        print("scene-tools:", cdp.ev("[...document.querySelectorAll('#dock-scenes .dock-btn, #dock-scenes button')].map(b=>((b.title||'')+'/'+(b.getAttribute('data-tip')||''))).join('|')"), flush=True)
        mdown_row(cdp, "#dock-scenes", "SMILE | Tech Diffs")
        time.sleep(2)
        check("scene cut -> Tech Diffs", obs_program() == "SMILE | Tech Diffs")
        mdown_row(cdp, "#dock-scenes", "SMILE | Meet")
        time.sleep(2)
        check("scene cut -> Meet", obs_program() == "SMILE | Meet")
        # scene add / rename (dblclick prompt) / undo / remove, all UI-driven
        print("add-click:", click_tip(cdp, "#dock-scenes", "Add"), flush=True)
        time.sleep(1.5)
        print("add-dlg:", dlg_fill_ok(cdp, "CONFORM_UI"), flush=True)
        time.sleep(3)
        names = scene_names()
        eng = cdp.ev("window.__obs.S.scenes.map(s=>s.name).join('|')")
        added = [n for n in names if n.startswith("CONFORM_UI")]
        check("scene added in OBS", len(added) == 1, "eng-has=%s obs=%s" % ("CONFORM_UI" in str(eng), added))
        if added:
            mdown_row(cdp, "#dock-scenes", added[0])
            time.sleep(1)
            hasrow = cdp.ev("""(() => {
              const rows = [...document.querySelectorAll('#dock-scenes .qlist-row')];
              const el = rows.find(e => e.textContent.trim().indexOf(%r) === 0);
              if (el) el.dispatchEvent(new MouseEvent('dblclick', {bubbles: true}));
              return !!el;
            })()""" % added[0])
            time.sleep(1.5)
            prompted = cdp.ev("document.body.innerText.indexOf('Rename Scene') >= 0")
            check("rename prompt opens", hasrow and prompted, str(hasrow))
            renamed = False
            if hasrow and prompted:
                dlg_fill_ok(cdp, "CONFORM_UI2")
                time.sleep(2)
                eng = cdp.ev("window.__obs.S.scenes.map(s=>s.name).join('|')")
                names = scene_names()
                renamed = "CONFORM_UI2" in names and added[0] not in names
                print("rename-eng-has:", "CONFORM_UI2" in str(eng), flush=True)
            check("scene renamed in OBS", renamed)
            if renamed:
                # undo reverts the rename through their undo stack
                cdp.call("Input.dispatchKeyEvent",
                         {"type": "keyDown", "key": "z", "code": "KeyZ", "ctrlKey": True})
                cdp.call("Input.dispatchKeyEvent",
                         {"type": "keyUp", "key": "z", "code": "KeyZ", "ctrlKey": True})
                time.sleep(2)
                names = scene_names()
                check("undo reverts rename", added[0] in names and "CONFORM_UI2" not in names,
                      str(names)[:120])
            else:
                check("undo reverts rename", False, "blocked: rename did not land")
            mdown_row(cdp, "#dock-scenes", added[0])
            time.sleep(1)
            click_tip(cdp, "#dock-scenes", "Remove")
            time.sleep(1.5)
            cdp.ev("""(() => {
              const wins = [...document.querySelectorAll('div.qwin')].filter(w => w.offsetParent);
              const win = wins[wins.length - 1];
              const scope = win || document;
              const b = [...scope.querySelectorAll('button')].find(x => ['OK', 'Remove', 'Yes', 'Delete'].indexOf(x.textContent.trim()) >= 0 && x.offsetParent);
              if (b) b.click(); return !!b;
            })()""")
            time.sleep(2)
            check("scene removed in OBS", added[0] not in scene_names())
        else:
            check("scene renamed in OBS", False, "blocked: add did not land")
            check("undo reverts rename", False, "blocked: add did not land")
            check("scene removed in OBS", False, "blocked: add did not land")
        mdown_row(cdp, "#dock-scenes", "SMILE | Meet")
        time.sleep(1)
        # sources dock follows THEIR preview scene, not our assumptions
        prev = cdp.ev("(()=>{const s=window.__obs.S.scenes.find(x=>x.id===window.__obs.S.previewId);return s?s.name:'?'})()")
        try:
            first = ocall("GetSceneItemList", {"sceneName": prev})["sceneItems"][0]["sourceName"]
        except Exception:
            first = "PLAYOUT_A"
        ok = cdp.wait_for("document.getElementById('dock-sources').textContent.indexOf(%r) >= 0" % first, 30)
        check("sources listed follow preview", ok, prev + "/" + first)
        # eye toggle on Tech Diffs item (harmless scene)
        mdown_row(cdp, "#dock-scenes", "SMILE | Tech Diffs")
        time.sleep(2)
        # eye toggle on a row the dock REALLY shows (poll for stability first)
        mdown_row(cdp, "#dock-scenes", "SMILE | Starting")
        steady = cdp.wait_for(
            "(()=>{const r=[...document.querySelectorAll('#dock-sources .qlist-row')].map(e=>e.textContent.trim().slice(0,26)).join('|');"
            "return r.indexOf('starting.html')>=0;})()", 30)
        check("sources dock settles on Starting", steady)
        eye, now, uistate = "", None, ""
        label = "starting.html"
        sc = "SMILE | Starting"
        try:
            items = ocall("GetSceneItemList", {"sceneName": sc})["sceneItems"]
            was = [i for i in items if i["sourceName"] == label][0]["sceneItemEnabled"]
            iid = [i for i in items if i["sourceName"] == label][0]["sceneItemId"]
        except Exception as e:
            was, iid = None, None
        check("eye target resolves in OBS", iid is not None, str(label))
        if iid is not None:
            for _ in range(3):
                eye = cdp.ev("""(() => {
                  const rows = [...document.querySelectorAll('#dock-sources .qlist-row')];
                  const row = rows.find(e => e.textContent.indexOf('starting.html') >= 0);
                  if (!row) return 'norow';
                  const eye = row.querySelector('.row-vis');
                  if (eye) { eye.click(); return 'eye'; }
                  return 'noeye';
                })()""")
                time.sleep(3)
                now = [i for i in ocall("GetSceneItemList", {"sceneName": sc})["sceneItems"]
                       if i["sceneItemId"] == iid][0]["sceneItemEnabled"]
                uistate = cdp.ev("""(() => {
                  const rows = [...document.querySelectorAll('#dock-sources .qlist-row')];
                  const row = rows.find(e => e.textContent.indexOf('starting.html') >= 0);
                  const eye = row && row.querySelector('.row-vis');
                  return eye ? eye.className : 'norow';
                })()""")
                if now != was:
                    break
            check("eye toggle flips in OBS", now != was, "%s ui=%s was=%s now=%s" % (eye, uistate, was, now))
            try:
                OBS._call("SetSceneItemEnabled",
                          {"sceneName": sc, "sceneItemId": iid, "sceneItemEnabled": was})
            except Exception:
                pass
        mdown_row(cdp, "#dock-scenes", "SMILE | Meet")
        time.sleep(1)
        # mixer mute + volume on Music Bed (real, harmless, restored after)
        mv = ocall("GetInputMute", {"inputName": "Music Bed"})
        cdp.ev("""(() => {
          const leaf = [...document.querySelectorAll('#dock-mixer *')].find(e => e.children.length === 0 && e.textContent.trim() === 'Music Bed');
          if (!leaf) return 'noch';
          let n = leaf;
          while (n && !n.querySelector('.mx-speaker')) n = n.parentElement;
          if (!n) return 'nospeaker';
          n.querySelector('.mx-speaker').click(); return 'muted';
        })()""")
        time.sleep(2)
        check("mixer mute flips in OBS",
              ocall("GetInputMute", {"inputName": "Music Bed"})["inputMuted"] != mv["inputMuted"])
        vv = ocall("GetInputVolume", {"inputName": "Music Bed"})["inputVolumeDb"]
        cdp.ev("""(() => {
          const leaf = [...document.querySelectorAll('#dock-mixer *')].find(e => e.children.length === 0 && e.textContent.trim() === 'Music Bed');
          if (!leaf) return 'noch';
          let n = leaf;
          while (n && !n.querySelector('input.obs-range')) n = n.parentElement;
          if (!n) return 'noslider';
          const sl = n.querySelector('input.obs-range');
          const desc = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
          desc.set.call(sl, -10);
          sl.dispatchEvent(new Event('input', {bubbles: true})); sl.dispatchEvent(new Event('change', {bubbles: true}));
          return 'set-10';
        })()""")
        time.sleep(2)
        nv = ocall("GetInputVolume", {"inputName": "Music Bed"})["inputVolumeDb"]
        check("mixer fader moves volume in OBS", abs(nv - vv) > 0.5, "was=%s now=%s" % (vv, nv))
        OBS._call("SetInputVolume", {"inputName": "Music Bed", "inputVolumeDb": vv})
        OBS._call("SetInputMute", {"inputName": "Music Bed", "inputMuted": mv["inputMuted"]})
        # transitions on Fade (Cut carries no duration server-side)
        click_text(cdp, "#dock-transitions", "Fade")
        time.sleep(1)
        dur = 0
        engdur = None
        for _ in range(3):
            cdp.ev("""(() => {
              const n = [...document.querySelectorAll('#dock-transitions input[type=number]')].find(e => e.offsetParent);
              if (!n) return 'nonum';
              const desc = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
              desc.set.call(n, 400);
              n.dispatchEvent(new Event('input', {bubbles: true})); n.dispatchEvent(new Event('change', {bubbles: true}));
              return 'dur400';
            })()""")
            time.sleep(1)  # tight window: the daemon rewrites duration (750) on every deck advance
            uival = cdp.ev("([...document.querySelectorAll('#dock-transitions input[type=number]')].find(e => e.offsetParent) || {}).value")
            engdur = cdp.ev("window.__obs.S.transitionDur")
            dur = ocall("GetCurrentSceneTransition").get("transitionDuration", 0)
            if dur == 400:
                break
            time.sleep(2)
        check("transition duration 400 on Fade", dur == 400, "ui=%s eng=%s obs=%s" % (uival, engdur, dur))
        cdp.ev("""(() => {
          const n = [...document.querySelectorAll('#dock-transitions input[type=number]')].find(e => e.offsetParent);
          const desc = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
          desc.set.call(n, 300);
          n.dispatchEvent(new Event('input', {bubbles: true})); n.dispatchEvent(new Event('change', {bubbles: true}));
          return 'dur300';
        })()""")
        time.sleep(1)
        # studio mode via View menu, preview, transition, restore
        click_text(cdp, "#menubar", "View")
        time.sleep(1)
        click_text(cdp, ".qmenu", "Studio Mode")
        time.sleep(2)
        check("studio mode on", ocall("GetStudioModeEnabled")["studioModeEnabled"] is True)
        mdown_row(cdp, "#dock-scenes", "SMILE | End Credits")
        time.sleep(2)
        check("preview follows in studio",
              ocall("GetCurrentPreviewScene")["currentPreviewSceneName"] == "SMILE | End Credits")
        cdp.ev("""(() => {
          const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Transition' && x.offsetParent);
          if (b) b.click(); return !!b;
        })()""")
        time.sleep(3)
        check("studio transition cuts program", obs_program() == "SMILE | End Credits")
    finally:
        cleanup_scratch()
        try:
            print("applog:", cdp.ev("(window.__obs._logFeed || []).slice(-8).map(l => l.level + ':' + String(l.msg).slice(0,80)).join(' || ')"), flush=True)
        except Exception as e:
            print("applog: unreadable", flush=True)
        try:
            OBS._call("SetStudioModeEnabled", {"studioModeEnabled": False})
        except Exception:
            pass
        try:
            OBS._call("SetCurrentProgramScene", {"sceneName": "SMILE | Meet"})
        except Exception:
            pass
        chrome.kill()


def click_text(cdp, scope, text):
    try:
        return cdp.ev("(%s)(%r, %r)" % (CLICK_LEAF, scope, text))
    except Exception as e:
        return "error:%s" % e


def click_tip(cdp, scope, tip):
    try:
        return cdp.ev("(%s)(%r, %r)" % (CLICK_TIP, scope, tip))
    except Exception as e:
        return "error:%s" % e


def mdown_row(cdp, scope, text):
    try:
        return cdp.ev("(%s)(%r, %r)" % (MDOWN_ROW, scope, text))
    except Exception as e:
        return "error:%s" % e


# --------------------------------------------------------------- part 2 ---
def part2():
    chrome, cdp = boot(port=9232)
    try:
        check("boot-2: connected", wait_connected(cdp, 90))
        if not RESULTS[-1]:
            return
        # properties dialog for existing browser source, cancel out
        mdown_row(cdp, "#dock-scenes", "SMILE | Tech Diffs")
        time.sleep(2)
        cdp.ev("""(() => {
          const r = document.querySelector('#dock-sources .qlist-row');
          if (!r) return 'norow';
          r.dispatchEvent(new MouseEvent('dblclick', {bubbles: true})); return 'dbl';
        })()""")
        time.sleep(2)
        check("properties dialog opens",
              cdp.wait_for("document.body.innerText.indexOf('Properties') >= 0", 10))
        dlg_close(cdp)
        time.sleep(1)
        # filters dialog via toolbar on a Meet deck item
        mdown_row(cdp, "#dock-scenes", "SMILE | Meet")
        time.sleep(2)
        cdp.ev("""(() => {
          const r = document.querySelector('#dock-sources .qlist-row');
          if (r) r.dispatchEvent(new MouseEvent('mousedown', {button: 0, bubbles: true}));
          return !!r;
        })()""")
        time.sleep(1)
        fr = click_tip(cdp, "#dock-sources", "Filters")
        time.sleep(2)
        check("filters dialog opens",
              cdp.wait_for("document.body.innerText.indexOf('Filters') >= 0", 10), str(fr))
        dlg_close(cdp)
        # settings modal opens and closes untouched
        click_text(cdp, "#dock-controls", "Settings")
        time.sleep(2)
        check("settings modal opens",
              cdp.wait_for("document.body.innerText.indexOf('General') >= 0", 10))
        dlg_close(cdp)
        # add text source through the real flow, then remove it
        mdown_row(cdp, "#dock-scenes", "SMILE | Tech Diffs")
        time.sleep(1)
        add = click_tip(cdp, "#dock-sources", "Add")
        time.sleep(1.5)
        kind = cdp.ev("""(() => {
          const items = [...document.querySelectorAll('*')].filter(e => e.children.length === 0 && e.offsetParent).map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 48);
          const el = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && e.offsetParent && /text/i.test(e.textContent || ''));
          if (el) el.click();
          return (el ? 'picked:' + el.textContent.trim() : 'nokind') + ' || visible:' + JSON.stringify(items.slice(0, 60));
        })()""")
        time.sleep(1.5)
        dlg_fill_ok(cdp, "CONFORM_UI_SRC")
        time.sleep(3)
        inps = [i["inputName"] for i in ocall("GetInputList")["inputs"]]
        created = "CONFORM_UI_SRC" in inps
        check("source created in OBS via UI flow", created, str(kind)[:120])
        if not created:
            check("source removed in OBS via UI flow", False, "blocked: create did not land")
        else:
            cdp.ev("""(() => {
              const ok = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'OK' && b.offsetParent);
              if (ok) ok.click(); return 'ok2';
            })()""")
            time.sleep(1)
            cdp.ev("""(() => {
              const rows = [...document.querySelectorAll('#dock-sources .qlist-row')];
              const el = rows.find(e => e.textContent.indexOf('CONFORM_UI_SRC') >= 0);
              if (el) el.dispatchEvent(new MouseEvent('mousedown', {button: 0, bubbles: true}));
              return !!el;
            })()""")
            time.sleep(1)
            click_tip(cdp, "#dock-sources", "Remove")
            time.sleep(1.5)
            cdp.ev("""(() => {
              const wins = [...document.querySelectorAll('div.qwin')].filter(w => w.offsetParent);
              const win = wins[wins.length - 1];
              const scope = win || document;
              const ok = [...scope.querySelectorAll('button')].find(b => ['OK', 'Remove', 'Yes', 'Delete'].indexOf(b.textContent.trim()) >= 0 && b.offsetParent);
              if (ok) ok.click(); return !!ok;
            })()""")
            time.sleep(2)
            inps = [i["inputName"] for i in ocall("GetInputList")["inputs"]]
            check("source removed in OBS via UI flow", "CONFORM_UI_SRC" not in inps)
        mdown_row(cdp, "#dock-scenes", "SMILE | Meet")
        time.sleep(1)
        # menus open with items
        for m in ["File", "Edit", "View", "Docks", "Profile", "Scene Collection", "Tools", "Help"]:
            r = click_text(cdp, "#menubar", m)
            time.sleep(1)
            n = cdp.ev("document.querySelectorAll('.qmenu *, .context-menu *, [role=menu] *').length")
            check("menu %s opens with items" % m, (n or 0) > 3, "%s items=%s" % (r, n))
            cdp.ev("document.body.click()")
            time.sleep(0.5)
        # outputs: stream fails safe (no key), record round-trips, vcam flips
        click_text(cdp, "#dock-controls", "Start Streaming")
        time.sleep(3)
        check("stream without key stays inactive",
              ocall("GetStreamStatus")["outputActive"] is False)
        recs = set(os.listdir(os.path.join(os.getcwd(), "broadcast", "recordings")))
        click_text(cdp, "#dock-controls", "Start Recording")
        time.sleep(5)
        started = ocall("GetRecordStatus")["outputActive"]
        click_text(cdp, "#dock-controls", "Stop Recording")
        time.sleep(2)
        stopped = ocall("GetRecordStatus")["outputActive"] is False
        newfiles = set(os.listdir(os.path.join(os.getcwd(), "broadcast", "recordings"))) - recs
        check("record round-trips file", started and stopped and len(newfiles) > 0,
              str(sorted(newfiles))[:80])
        for f in newfiles:
            try:
                os.remove(os.path.join(os.getcwd(), "broadcast", "recordings", f))
            except OSError:
                pass
        try:
            vc0 = ocall("GetVirtualCamStatus")
            vcam_available = True
        except Exception as e:
            vcam_available = False
        if not vcam_available:
            check("virtual cam flips", False, "ENV-SKIP: VirtualCam unavailable on this box")
        else:
            click_text(cdp, "#dock-controls", "Start Virtual Camera")
            time.sleep(2)
            von = ocall("GetVirtualCamStatus")["outputActive"]
            click_text(cdp, "#dock-controls", "Stop Virtual Camera")
            time.sleep(2)
            voff = ocall("GetVirtualCamStatus")["outputActive"] is False
            check("virtual cam flips", von and voff)
        a = cdp.ev("document.body.innerText.match(/CPU[^\\n]{0,24}/) ? document.body.innerText.match(/CPU[^\\n]{0,24}/)[0] : ''")
        check("status bar live", bool(a), str(a)[:40])
    finally:
        cleanup_scratch()
        try:
            print("applog:", cdp.ev("(window.__obs._logFeed || []).slice(-8).map(l => l.level + ':' + String(l.msg).slice(0,80)).join(' || ')"), flush=True)
        except Exception:
            print("applog: unreadable", flush=True)
        try:
            OBS._call("SetCurrentProgramScene", {"sceneName": "SMILE | Meet"})
        except Exception:
            pass
        chrome.kill()


def dlg_close(cdp):
    cdp.ev("""(() => {
      const b = [...document.querySelectorAll('button')].find(x => ['Cancel', 'Close', 'Done'].indexOf(x.textContent.trim()) >= 0 && x.offsetParent);
      if (b) b.click(); return !!b;
    })()""")


if __name__ == "__main__":
    part = sys.argv[sys.argv.index("--part") + 1] if "--part" in sys.argv else "1"
    try:
        os.environ["OBS_TIMEOUT"] = "8"
        daemon.OBSRenderer()._call("GetVersion")
    except Exception as e:
        print("PREFLIGHT FAIL: render plane unreachable (%s). Start OBS first." % e, flush=True)
        sys.exit(2)
    (part1 if part == "1" else part2)()
    bad = [i for i, r in enumerate(RESULTS) if not r]
    print("----\n%d/%d passed" % (len(RESULTS) - len(bad), len(RESULTS)), flush=True)
    sys.exit(1 if bad else 0)
