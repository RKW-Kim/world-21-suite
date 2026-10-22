#!/usr/bin/env python3
"""Station config sync: OBS <-> repo, 1:1 machine portability.

CONFIG (committed under station/config/): scenes + items (transforms,
visibility, locks), inputs (settings, volumes, mutes, filters), video
canvas/output/fps, stream service, transition, encoder file verbatim.
LIVE RUNTIME (never committed, machine-local): playlist queue, playout
position, caches, media bytes, secrets.

The split is deliberate: config migrates between machines, live state does
not (the VPS keeps playing; a fresh box starts from the seed playlist).

  python3 station/sync.py capture [--out station/config]   # OBS -> repo files
  python3 station/sync.py diff                              # repo vs live drift
  python3 station/sync.py apply [--restart] [--profile NAME]
      # repo -> OBS: profile files + live RPCs; --restart bounces obs
      # (needed for collection file + encoder changes; video/service/transition apply live)

Secrets: secret-shaped values are stored as {"$secret": "NAME"} and filled
from broadcast/secrets.env on apply, which REFUSES to proceed with gaps
(loud list, no placeholders written anywhere). After redaction, capture
scans the output for every known secret value and aborts if one leaked.

Machine independence: absolute media paths under the media dir become
"media:<rel>", overlay http(s)://host:7070/... URLs become "overlay:/...".
Apply resolves both against the LOCAL machine. Media BYTES travel via
intake/scp (operator job) — config without bytes is a loud, explicit gap.

Env: BROADCAST_ROOT (default ./broadcast), OVERLAY_URL (default
http://127.0.0.1:7070), STATION_PROFILE (default CONFORM_Y).
"""

import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import daemon

CONFIG_DIR = os.path.join(HERE, "config")
# Same resolution as the daemon: the broadcast root moves on the VPS.
BROADCAST_ROOT = os.environ.get(
    "BROADCAST_ROOT", os.path.join(os.getcwd(), "broadcast"))

SECRET_EXACT = {"password", "passwd", "key", "token", "secret", "auth",
                "bearer", "api_key", "apikey", "stream_key", "private_key"}
SECRET_SUFFIX = ("_password", "_passwd", "_token", "_secret", "_key")
AUDIO_KINDS = {"wasapi_input_capture", "wasapi_output_capture",
               "pulse_input_capture", "pulse_output_capture",
               "coreaudio_input_capture", "coreaudio_output_capture",
               "ffmpeg_source", "vlc_source", "browser_source"}


def secret_name(scope, key):
    if scope == "service" and key == "key":
        return "YOUTUBE_STREAM_KEY"  # house convention, see setup.sh template
    clean = "".join(c if (c.isalnum() or c == "_") else "_" for c in
                    ("%s_%s" % (scope, key)).upper())
    while "__" in clean:
        clean = clean.replace("__", "_")
    return clean.strip("_")


def is_secret_key(key):
    k = key.lower()
    return k in SECRET_EXACT or k.endswith(SECRET_SUFFIX)


def overlay_base():
    return os.environ.get("OVERLAY_URL", "http://127.0.0.1:7070").rstrip("/")


def norm_str(s, media):
    if not isinstance(s, str):
        return s
    low = s.lower()
    for scheme in ("https://", "http://"):
        if low.startswith(scheme):
            rest = s[len(scheme):]
            host, _, path = rest.partition("/")
            if host.endswith(":7070"):
                return "overlay:/" + path
    if media and os.path.isabs(s) and s.startswith(media + os.sep):
        return "media:" + s[len(media) + 1:]
    # A deck input's file is RUNTIME state: the daemon points it at the
    # item it is about to play, which is a spool file with a transient
    # name. The capture must not commit that -- the fail-safe template
    # goes in instead, exactly as the hand-made capture did.
    spool_dir = getattr(getattr(daemon, "spool", None), "SPDIR", "")
    if spool_dir and os.path.isabs(s) and s.startswith(spool_dir + os.sep):
        return "media:" + daemon.FALLBACK_DEFAULT[1]
    return s


def redact(obj, scope, media, secrets_map):
    """Walk settings; secret keys -> {"$secret": NAME}, paths/URLs -> tokens."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if is_secret_key(k) and isinstance(v, str) and v:
                name = secret_name(scope, k)
                secrets_map.setdefault(name, "")
                out[k] = {"$secret": name}
            else:
                out[k] = redact(v, scope, media, secrets_map)
        return out
    if isinstance(obj, list):
        return [redact(v, scope, media, secrets_map) for v in obj]
    if isinstance(obj, str):
        return norm_str(obj, media)
    return obj


def fill(obj, secrets):
    """Reverse redaction/tokens. Raises KeyError listing gaps (loud)."""
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$secret"}:
            name = obj["$secret"]
            if not secrets.get(name):
                raise KeyError(name)
            return secrets[name]
        return {k: fill(v, secrets) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fill(v, secrets) for v in obj]
    if isinstance(obj, str):
        if obj.startswith("overlay:/"):
            return overlay_base() + "/" + obj[len("overlay:/"):]
        if obj.startswith("media:"):
            return os.path.join(daemon.MEDIA, obj[len("media:"):])
    return obj


def load_secrets():
    daemon.load_secrets()
    out, path = {}, os.path.join(daemon.ROOT, "secrets.env")
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def check_no_leak(text, secrets):
    for name, val in secrets.items():
        if val and len(val) >= 4 and val in text:
            raise SystemExit("capture ABORTED: secret %s would be committed verbatim. "
                             "Widen redaction, never commit." % name)


def rpc():
    daemon.load_secrets()
    return daemon.OBSRenderer()


# ---------------------------------------------------------------- capture ---
def capture(out_dir):
    r = rpc()
    media = daemon.MEDIA
    secrets_map = {}
    col = {"name": None, "scenes": []}
    scene_list = r._call("GetSceneList")
    for sc in scene_list.get("scenes", []):
        name = sc["sceneName"]
        try:
            sil = r._call("GetSceneItemList", {"sceneName": name})
        except Exception as e:
            print("capture: %s items unreadable (%s); scene kept empty" % (name, e))
            sil = {"sceneItems": []}
        items = []
        for it in sil.get("sceneItems", []):
            items.append({
                "id": it.get("sceneItemId"),
                "source": it.get("sourceName"),
                "transform": it.get("sceneItemTransform") or {},
                "sourceWidth": it.get("sourceWidth"),
                "sourceHeight": it.get("sourceHeight"),
                "enabled": it.get("sceneItemEnabled", True),
                "locked": bool(it.get("sceneItemLocked")),
            })
        col["scenes"].append({"name": name, "items": items})
    col["program"] = scene_list.get("currentProgramSceneName")
    col["preview"] = scene_list.get("currentPreviewSceneName")

    inputs = []
    for inp in r._call("GetInputList").get("inputs", []):
        name, kind = inp["inputName"], inp.get("inputKind", "")
        try:
            settings = r._call("GetInputSettings",
                               {"inputName": name}).get("inputSettings", {})
        except Exception as e:
            print("capture: %s settings unreadable (%s)" % (name, e))
            settings = {}
        entry = {"name": name, "kind": kind,
                 "settings": redact(settings, name, media, secrets_map)}
        if kind in AUDIO_KINDS:
            try:
                entry["volumeDb"] = r._call(
                    "GetInputVolume", {"inputName": name}).get("inputVolumeDb", 0.0)
            except Exception:
                entry["volumeDb"] = 0.0
            try:
                entry["muted"] = bool(r._call(
                    "GetInputMute", {"inputName": name}).get("inputMuted", False))
            except Exception:
                entry["muted"] = False
        try:
            fl = r._call("GetSourceFilterList", {"sourceName": name}).get("filters", [])
        except Exception:
            fl = []
        filters = []
        for f in fl:
            fs = f.get("filterSettings")
            if fs is None:
                try:
                    fs = r._call("GetSourceFilterSettings",
                                 {"sourceName": name,
                                  "filterName": f["filterName"]}).get("filterSettings", {})
                except Exception:
                    fs = {}
            filters.append({"name": f["filterName"], "kind": f.get("filterKind", ""),
                            "enabled": f.get("filterEnabled", True),
                            "index": f.get("filterIndex", 0),
                            "settings": redact(fs, name, media, secrets_map)})
        entry["filters"] = filters
        inputs.append(entry)
    col["inputs"] = inputs

    try:
        video = r._call("GetVideoSettings")
    except Exception as e:
        print("capture: video unreadable (%s)" % e)
        video = {}
    try:
        svc = r._call("GetStreamServiceSettings")
        service = {"type": svc.get("streamServiceType", ""),
                   "settings": redact(svc.get("streamServiceSettings", {}),
                                      "service", media, secrets_map)}
    except Exception as e:
        print("capture: service unreadable (%s)" % e)
        service = {"type": "", "settings": {}}
    try:
        tr = r._call("GetCurrentSceneTransition")
        transition = {"name": tr.get("transitionName", "Cut")}
        try:
            transition["duration"] = r._call(
                "GetCurrentSceneTransitionDuration").get("transitionDuration", 300)
        except Exception:
            transition["duration"] = 300
    except Exception as e:
        print("capture: transition unreadable (%s)" % e)
        transition = {"name": "Cut", "duration": 300}

    encoder = None
    for cand in ("streamEncoder.json", "recordEncoder.json"):
        p = os.path.join(obs_profile_dir(), cand)
        if os.path.isfile(p):
            try:
                encoder = {cand: json.load(open(p))}
                break
            except ValueError:
                pass
    meta = {"canvas": {"w": video.get("baseWidth", 1920),
                       "h": video.get("baseHeight", 1080)},
            "captured_from": "%s:%s" % (os.environ.get("OBS_HOST", "127.0.0.1"),
                                        os.environ.get("OBS_PORT", "4455"))}

    os.makedirs(out_dir, exist_ok=True)
    files = {
        "collection.json": col,
        "video.json": video,
        "service.json": service,
        "transition.json": transition,
        "meta.json": meta,
    }
    if encoder:
        files["encoder.json"] = encoder
    rendered = {fn: json.dumps(obj, indent=2, sort_keys=True) + "\n"
                for fn, obj in files.items()}
    # Leak check BEFORE any byte hits disk: a failed check must not leave
    # secret-bearing files sitting in station/config ready to be committed.
    check_no_leak("\n".join(rendered.values()), load_secrets())
    for fn, text in rendered.items():
        with open(os.path.join(out_dir, fn), "w") as f:
            f.write(text)
    if secrets_map:
        print("capture: redacted secrets: %s (fill broadcast/secrets.env; never commit values)"
              % ", ".join(sorted(secrets_map)))
    print("capture: wrote %d files to %s" % (len(files), out_dir))
    return files


def obs_config_dir():
    return os.path.join(os.path.expanduser("~"), ".var", "app",
                        "com.obsproject.Studio", "config", "obs-studio")


def obs_profile_dir(profile=None):
    profile = profile or os.environ.get("STATION_PROFILE", "CONFORM_Y")
    return os.path.join(obs_config_dir(), "basic", "profiles", profile)


def collection_path(name=None):
    name = name or os.environ.get("STATION_COLLECTION", "SMILE-Station")
    return os.path.join(obs_config_dir(), "basic", "scenes", name + ".json")


# ------------------------------------------------------------------- diff ---
VOLATILE_TOP = {"program", "preview"}


def deck_sources():
    # The daemon owns A/B deck visibility (flips every advance). It is
    # runtime state, not config: diff skips it, apply never writes it.
    try:
        return {daemon.DECK_A, daemon.DECK_B}
    except AttributeError:
        return {"PLAYOUT_A", "PLAYOUT_B"}


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in sorted(obj.items()):
            if not prefix and k in VOLATILE_TOP:
                continue  # runtime pointers (current program/preview cut),
                          # not config — the loop moves them constantly
            yield from flatten(v, "%s.%s" % (prefix, k) if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from flatten(v, "%s[%d]" % (prefix, i))
    else:
        yield prefix, obj


def diff_live(files):
    """Compare repo files against a fresh capture (in memory)."""
    live = capture_to_memory()
    problems = []
    for fn, want in files.items():
        got = live.get(fn)
        if got is None:
            problems.append("%s: missing live (capture failed?)" % fn)
            continue
        w = dict(flatten(want))
        g = dict(flatten(got))
        for k in sorted(set(w) | set(g)):
            if "uuid" in k.lower().split(".")[-1:]:
                continue
            if w.get(k) != g.get(k):
                problems.append("%s %s: repo=%r live=%r" % (fn, k, w.get(k), g.get(k)))
                if len(problems) > 60:
                    problems.append("... (truncated at 60)")
                    return problems
    # A media source's local_file is runtime state too: the deck points
    # at whatever is playing. Diffing it produced a permanent, noisy
    # diff that trains the operator to ignore real drift.
    kept = []
    for p in problems:
        if "local_file" in p:
            continue
        kept.append(p)
    problems = kept
    # Deck eye states are daemon runtime (flips every advance), not config.
    try:
        deck = deck_sources()
        scenes = {s["name"]: s for s in files.get("collection.json", {}).get("scenes", [])}
        import re as _re
        kept = []
        for p in problems:
            m = _re.match(r"collection\.json scenes\[(\d+)\]\.items\[(\d+)\]\.enabled: ", p)
            if m:
                sc = files["collection.json"]["scenes"][int(m.group(1))]
                it = sc["items"][int(m.group(2))]
                if it.get("source") in deck:
                    continue
            kept.append(p)
        problems = kept
    except Exception:
        pass
    return problems


def capture_to_memory():
    import io
    import tempfile
    tmp = tempfile.mkdtemp(prefix="station-capture-")
    try:
        return capture(tmp)
    finally:
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ apply ---
BOUNDS_INT = {"OBS_BOUNDS_NONE": 0, "OBS_BOUNDS_STRETCH": 1,
              "OBS_BOUNDS_SCALE_INNER": 2, "OBS_BOUNDS_SCALE_OUTER": 3,
              "OBS_BOUNDS_SCALE_TO_WIDTH": 4, "OBS_BOUNDS_SCALE_TO_HEIGHT": 5,
              "OBS_BOUNDS_MAX_ONLY": 6}


def rpc_transform_to_file(t):
    """obs-websocket transform -> scene-collection file item fields."""
    return {
        "pos": {"x": float(t.get("positionX", 0)), "y": float(t.get("positionY", 0))},
        "scale": {"x": float(t.get("scaleX", 1)), "y": float(t.get("scaleY", 1))},
        "rot": float(t.get("rotation", 0)),
        "align": int(t.get("alignment", 5)),
        "bounds_type": BOUNDS_INT.get(t.get("boundsType"), 0),
        "bounds_align": int(t.get("boundsAlignment", 0)),
        "bounds": {"x": float(t.get("boundsWidth", 0)), "y": float(t.get("boundsHeight", 0))},
        "crop_left": int(t.get("cropLeft", 0)),
        "crop_top": int(t.get("cropTop", 0)),
        "crop_right": int(t.get("cropRight", 0)),
        "crop_bottom": int(t.get("cropBottom", 0)),
    }


def apply_geometry_to_file(col_path, col, changed, skip_visible=()):
    """Merge repo geometry into the live collection FILE.

    SetSceneItemTransform is broken server-side (correct payloads rejected
    with 'missing sceneItemTransform'; matches upstream issue #1299), so
    geometry travels by file + obs restart, like everything else that only
    the file owns. Only _rel/* computed caches are left for OBS to rebuild
    on load (verified: it recomputes them; absolute pos/scale rule).
    """
    with open(col_path) as f:
        live = json.load(f)
    file_scenes = {s.get("name"): s for s in live.get("sources", [])
                   if s.get("id") == "scene"}
    for sc in col["scenes"]:
        fs = file_scenes.get(sc["name"])
        if not fs:
            continue
        # match config items to file rows by source, ordinal within source
        rows = {}
        for it in fs.get("settings", {}).get("items", []):
            rows.setdefault(it.get("name"), []).append(it)
        for want in sc["items"]:
            cands = rows.get(want["source"], [])
            row = cands.pop(0) if cands else None
            if row is None:
                continue  # created live above; OBS wrote its own row
            new = rpc_transform_to_file(want.get("transform", {}))
            cur = {k: row.get(k) for k in new}
            want_vis = row.get("visible", True) if want["source"] in skip_visible else want.get("enabled", True)
            if cur != new or row.get("visible", True) != want_vis \
                    or row.get("locked", False) != bool(want.get("locked", False)):
                row.update(new)
                row["visible"] = want_vis
                row["locked"] = bool(want.get("locked", False))
                # Drop computed relative caches: on load OBS trusts stale
                # _rel over fresh absolute pos (seen live: file said 10.0,
                # plane rendered 0.0). The template ships without them and
                # fresh boots render correctly, so absence is safe.
                for rk in ("pos_rel", "scale_rel", "bounds_rel"):
                    row.pop(rk, None)
                changed.append("%s/%s" % (sc["name"], want["source"]))
    if not changed:
        return False
    tmp = col_path + ".new"
    with open(tmp, "w") as f:
        json.dump(live, f, indent=2)
        f.write("\n")
    os.replace(tmp, col_path)
    return True


def deep_merge(base, over):
    """Recursive dict merge (over wins); lists/scalars replace."""
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = deep_merge(out[k], v) if k in out else v
        return out
    return copy.deepcopy(over)


def load_local_overrides(repo_dir):
    """Per-machine deltas (gitignored local.json): e.g. the VPS stream
    server differs from lab's, and captures from elsewhere must not
    clobber it. Deep-merged over repo config on apply; never committed."""
    try:
        with open(os.path.join(repo_dir, "local.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def apply_all(repo_dir, do_restart, profile=None, collection=None):
    secrets = load_secrets()
    gaps = []

    def need_secret(name):
        if not secrets.get(name):
            gaps.append(name)
        return secrets.get(name, "")

    def fill_strict(obj):
        try:
            return fill(obj, secrets)
        except KeyError as e:
            gaps.append(str(e))
            raise SystemExit("apply ABORTED: secrets.env lacks %s. Fill it, never commit it."
                             % ", ".join(sorted(set(gaps))))

    def load(fn):
        with open(os.path.join(repo_dir, fn)) as f:
            return json.load(f)

    col = load("collection.json")
    video = load("video.json")
    service = load("service.json")
    transition = load("transition.json")
    try:
        encoder = load("encoder.json")
    except OSError:
        encoder = None

    local = load_local_overrides(repo_dir)
    if local.get("service"):
        service = deep_merge(service, local["service"])
        print("apply: local.json overrides service (per-machine, uncommitted)")
    if local.get("video"):
        video = deep_merge(video, local["video"])
        print("apply: local.json overrides video (per-machine, uncommitted)")
    if local.get("transition"):
        transition = deep_merge(transition, local["transition"])
        print("apply: local.json overrides transition (per-machine, uncommitted)")

    # sanity: no placeholders or raw secrets may reach OBS or disk
    for obj in (col, video, service, transition):
        if "$secret" in json.dumps(obj):
            fill_strict(obj)  # raises with the loud list if anything is missing

    # SKEW GUARD, before any OBS call. The capture in git can be older
    # than the plane (a scene was renamed on the live side -- "SMILE |
    # Meet" became "SMILE | Program"). Applying it would CREATE the old
    # name as a duplicate, orphan the live scene, and leave the daemon
    # driving a scene with no deck in it. The capture must contain every
    # scene the daemon drives.
    required = {daemon.SCENE_STARTING, daemon.SCENE_PROGRAM,
                daemon.SCENE_LIVE, daemon.SCENE_TECHDIFF,
                daemon.SCENE_OFFAIR, daemon.SCENE_END}
    have = {sc["name"] for sc in col["scenes"]}
    missing = required - have
    if missing:
        print("apply: REFUSING -- the capture is stale (it has no %s)."
              % ", ".join(sorted(missing)))
        print("apply: re-capture from the live plane first:")
        print("apply:   python3 station/sync.py capture")
        print("apply: (a rename on the plane is not a config change; applying")
        print("apply:  the old capture would duplicate the scene.)")
        return 1

    r = rpc()
    names = [s["sceneName"] for s in r._call("GetSceneList").get("scenes", [])]
    for sc in col["scenes"]:
        if sc["name"] not in names:
            r._call("CreateScene", {"sceneName": sc["name"]})
            print("apply: created scene %s" % sc["name"])
    known_inputs = {i["inputName"] for i in r._call("GetInputList").get("inputs", [])}
    for inp in col.get("inputs", []):
        settings = fill_strict(inp.get("settings", {}))
        if inp["name"] not in known_inputs:
            host_scene = next((s["name"] for s in col["scenes"]
                               if any(it["source"] == inp["name"] for it in s["items"])), None)
            if not host_scene:
                print("apply: SKIP orphan input %s (in no scene)" % inp["name"])
                continue
            r._call("CreateInput", {"sceneName": host_scene, "inputName": inp["name"],
                                    "inputKind": inp["kind"], "inputSettings": settings})
            print("apply: created input %s (%s)" % (inp["name"], inp["kind"]))
            known_inputs.add(inp["name"])
        else:
            cur = r._call("GetInputSettings", {"inputName": inp["name"]}).get("inputSettings", {})
            merged = dict(cur)
            merged.update(settings)
            if merged != cur:
                r._call("SetInputSettings", {"inputName": inp["name"],
                                             "inputSettings": settings, "overlay": True})
        if "volumeDb" in inp:
            r._call("SetInputVolume", {"inputName": inp["name"],
                                       "inputVolumeDb": inp["volumeDb"]})
        if "muted" in inp:
            r._call("SetInputMute", {"inputName": inp["name"],
                                     "inputMuted": bool(inp["muted"])})
        try:
            live_filters = {f["filterName"]: f for f in r._call(
                "GetSourceFilterList", {"sourceName": inp["name"]}).get("filters", [])}
        except Exception:
            live_filters = {}
        for f in inp.get("filters", []):
            fs = fill_strict(f.get("settings", {}))
            if f["name"] not in live_filters:
                r._call("CreateSourceFilter", {"sourceName": inp["name"],
                                               "filterName": f["name"],
                                               "filterKind": f["kind"],
                                               "filterSettings": fs})
                print("apply: filter %s on %s" % (f["name"], inp["name"]))
            else:
                r._call("SetSourceFilterSettings", {"sourceName": inp["name"],
                                                    "filterName": f["name"],
                                                    "filterSettings": fs})
    for sc in col["scenes"]:
        try:
            live_items = r._call("GetSceneItemList", {"sceneName": sc["name"]}).get("sceneItems", [])
        except Exception as e:
            print("apply: SKIP scene %s (%s)" % (sc["name"], e))
            continue
        by_src = {}
        for it in live_items:
            by_src.setdefault(it["sourceName"], []).append(it)
        # Deck eye states belong to the running loop, not to config: never
        # write them (a mid-show apply could invert the visible deck until
        # the next advance). Everything else mirrors repo truth.
        deck = deck_sources()
        failures = []
        for want in sc["items"]:
            try:
                cands = by_src.get(want["source"], [])
                hit = cands.pop(0) if cands else None
                if hit is None:
                    nid = r._call("CreateSceneItem", {"sceneName": sc["name"],
                                                      "sourceName": want["source"]}).get("sceneItemId")
                    # Geometry lands via the collection file below
                    # (SetSceneItemTransform is broken server-side).
                    if want["source"] not in deck:
                        r._call("SetSceneItemEnabled",
                                {"sceneName": sc["name"], "sceneItemId": nid,
                                 "sceneItemEnabled": want.get("enabled", True)})
                    if want.get("locked"):
                        r._call("SetSceneItemLocked",
                                {"sceneName": sc["name"], "sceneItemId": nid,
                                 "sceneItemLocked": True})
                    print("apply: +%s in %s (geometry follows via file)" % (want["source"], sc["name"]))
                else:
                    iid = hit["sceneItemId"]
                    if want["source"] not in deck:
                        r._call("SetSceneItemEnabled",
                                {"sceneName": sc["name"], "sceneItemId": iid,
                                 "sceneItemEnabled": want.get("enabled", True)})
                    r._call("SetSceneItemLocked",
                            {"sceneName": sc["name"], "sceneItemId": iid,
                             "sceneItemLocked": bool(want.get("locked", False))})
            except Exception as e:
                failures.append("%s/%s: %s" % (sc["name"], want.get("source"), e))
        for f in failures:
            print("apply ITEM-FAIL: %s" % f)
        if failures:
            raise SystemExit("apply aborted with %d item failures (listed above)" % len(failures))
    # Geometry travels by collection FILE, merged while obs is DEAD in the
    # --restart block below (SetSceneItemTransform is broken server-side;
    # and a running OBS autosaves its in-memory collection over the file,
    # eating the merge). Without --restart, geometry stays repo-side only.
    geo_changed, col_path = [], collection_path(collection)
    if video:
        try:
            cur = r._call("GetVideoSettings")
        except Exception:
            cur = {}
        want = {
            "baseWidth": video.get("baseWidth", 1920),
            "baseHeight": video.get("baseHeight", 1080),
            "outputWidth": video.get("outputWidth", 1280),
            "outputHeight": video.get("outputHeight", 720),
            "fpsNumerator": video.get("fpsNumerator", 30),
            "fpsDenominator": video.get("fpsDenominator", 1)}
        if all(cur.get(k) == v for k, v in want.items()):
            print("apply: video already matches (no-op)")
        else:
            r._call("SetVideoSettings", want)
            print("apply: video live (canvas/output/fps)")
    if service.get("type"):
        filled = fill_strict(service.get("settings", {}))
        try:
            cur = r._call("GetStreamServiceSettings")
        except Exception:
            cur = {}
        if (cur.get("streamServiceType") == service["type"]
                and cur.get("streamServiceSettings", {}) == filled):
            print("apply: stream service already matches (no-op)")
        else:
            r._call("SetStreamServiceSettings",
                    {"streamServiceType": service["type"],
                     "streamServiceSettings": filled})
            print("apply: stream service live (%s)" % service["type"])
    if transition.get("name"):
        r._call("SetCurrentSceneTransition", {"transitionName": transition["name"]})
        if transition.get("duration"):
            try:
                r._call("SetCurrentSceneTransitionDuration",
                        {"transitionDuration": transition["duration"]})
            except Exception:
                pass
        print("apply: transition live (%s)" % transition["name"])

    # Profile files: collection content is OBS-canonical on disk already;
    # video/service/encoder land here for the NEXT boot (live RPCs above
    # covered this boot). streamEncoder.json always needs a restart.
    prof = obs_profile_dir(profile)
    os.makedirs(prof, exist_ok=True)
    with open(os.path.join(prof, "service.json"), "w") as f:
        json.dump({"type": service.get("type", ""),
                   "settings": fill_strict(service.get("settings", {}))}, f, indent=2)
    with open(os.path.join(prof, "basic.ini"), "w") as f:
        v = video or {}
        f.write("[General]\nName=%s\n\n[Video]\nBaseCX=%d\nBaseCY=%d\n"
                "OutputCX=%d\nOutputCY=%d\nFPSType=0\nFPSCommon=%d\n"
                % (profile or os.environ.get("STATION_PROFILE", "CONFORM_Y"),
                   v.get("baseWidth", 1920), v.get("baseHeight", 1080),
                   v.get("outputWidth", 1280), v.get("outputHeight", 720),
                   round(v.get("fpsNumerator", 30) / max(1, v.get("fpsDenominator", 1)))))
    wrote_encoder = False
    if encoder:
        for fn, obj in encoder.items():
            body = json.dumps(obj, indent=2, sort_keys=True) + "\n"
            dest = os.path.join(prof, fn)
            try:
                with open(dest) as f:
                    same = (json.load(f) == obj)
            except (OSError, ValueError):
                same = False
            if not same:
                with open(dest, "w") as f:
                    f.write(body)
                wrote_encoder = True
    print("apply: profile files written to %s" % prof)
    if wrote_encoder:
        print("apply: encoder file changed — restart obs for it to take effect")
    if not do_restart:
        print("apply: geometry/encoder file changes need `sync.py apply --restart`")
        return
    # Restart path (the ONLY way geometry/encoder changes load): stop obs
    # hard first (SIGKILL leaves no save-on-exit to clobber the merge —
    # a running OBS autosaves its in-memory collection over the file),
    # merge geometry while dead, then start. systemctl restart alone is
    # not enough: stop does not reap flatpak/bwrap reliably (seen live).
    import subprocess as _sp
    import time as _time

    def _run(*args):
        # Honest exit codes: a silently failed systemctl step is how a
        # root install went dark with a green apply. rc is returned (0
        # ok) and every failure prints, callers decide what is fatal.
        try:
            p = _sp.run(list(args), timeout=120,
                        stdout=_sp.PIPE, stderr=_sp.PIPE, text=True)
        except Exception as e:
            print("apply: restart step %s failed: %s" % (args[-1], e))
            return 1
        if p.returncode != 0:
            tail = (p.stderr or p.stdout or "").strip().splitlines()
            print("apply: restart step %r failed rc=%d: %s"
                  % (" ".join(args), p.returncode,
                     tail[-1] if tail else "(no output)"))
        return p.returncode

    def _pids():
        out = []
        try:
            ps = _sp.run(["ps", "-eo", "pid,comm"], capture_output=True,
                         timeout=10, text=True)
            for line in ps.stdout.splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[1] in ("obs", "bwrap"):
                    out.append(parts[0])
        except Exception:
            pass
        return out

    print("apply: stopping obs for geometry/encoder load ...")
    # Park the watchdog first: a timer firing mid-apply used to "revive"
    # the daemon while the collection was being merged under it. The park
    # is lifted in the finally below — on success and on every abort —
    # so only an apply killed outright leaves a stale park, which the
    # watchdog self-heals after its TTL. (The old code said "removed in
    # the finally below" but never removed it: every apply fenced the
    # watchdog for the full TTL, revive-free, including the plane.)
    park = os.path.join(BROADCAST_ROOT, ".watchdog-park")
    parked = False
    try:
        os.makedirs(BROADCAST_ROOT, exist_ok=True)
        with open(park, "w") as _pf:
            _pf.write(_time.strftime("%Y-%m-%dT%H:%M:%S"))
        parked = True
    except OSError as e:
        park = None
        print("apply WARNING: could not write the watchdog park (%s); "
              "the watchdog may race this restart" % e)
    # Park the daemon too: its self-heal restarts the plane when it
    # looks dead, which would fight this restart over the singleton lock.
    # Same scope the installer used: a root install uses plain systemctl,
    # a user install uses systemctl --user. The old hardcoded --user
    # silently no-opped on a system install, and the daemon was then
    # running while the collection was merged under it.
    scope = ["systemctl"] if os.geteuid() == 0 else ["systemctl", "--user"]
    try:
        _run(*(scope + ["stop", "station-daemon"]))
        _run(*(scope + ["stop", "station-obs"]))
        _time.sleep(3)
        for _ in range(3):
            left = _pids()
            if not left:
                break
            _sp.run(["kill", "-9"] + left, stdout=_sp.DEVNULL,
                    stderr=_sp.DEVNULL)
            _time.sleep(2)
        if _pids():
            raise SystemExit("apply ABORTED: obs tree would not die; refusing to merge under a live writer")
        try:
            if apply_geometry_to_file(col_path, col, geo_changed, skip_visible=deck_sources()):
                print("apply: geometry merged into %s (%d rows)" % (col_path, len(geo_changed)))
            else:
                print("apply: geometry already matches file (no-op)")
        except OSError as e:
            raise SystemExit("apply ABORTED: geometry merge failed (%s)" % e)
        if _run(*(scope + ["start", "station-obs"])) != 0:
            print("apply WARNING: station-obs start failed; the :4455 probe below will confirm")
        print("apply: obs restarted (daemon rides it out via wait_ready; restart the monitor stream)")
        # Wait for the socket, then bring the loop back — an apply that leaves
        # the station dark is a failed apply.
        import socket as _s
        for _ in range(36):
            try:
                probe = _s.create_connection(("127.0.0.1", 4455), timeout=2)
                probe.close()
                break
            except OSError:
                _time.sleep(5)
        else:
            print("apply WARNING: :4455 never came back; starting daemon anyway")
        if _run(*(scope + ["start", "station-daemon"])) != 0:
            raise SystemExit(
                "apply FAILED: the daemon did not start — the watchdog is "
                "unparked below and will retry; check the journal for "
                "station-daemon")
        print("apply: daemon restarted")
    finally:
        if parked and park:
            try:
                os.remove(park)
            except OSError:
                pass


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture", help="OBS -> repo files")
    c.add_argument("--out", default=CONFIG_DIR)
    d = sub.add_parser("diff", help="repo vs live drift")
    d.add_argument("--dir", default=CONFIG_DIR)
    a = sub.add_parser("apply", help="repo -> OBS")
    a.add_argument("--dir", default=CONFIG_DIR)
    a.add_argument("--restart", action="store_true")
    a.add_argument("--profile", default=None)
    a.add_argument("--collection", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "capture":
        capture(args.out)
    elif args.cmd == "diff":
        files = {}
        for fn in ("collection.json", "video.json", "service.json", "transition.json"):
            with open(os.path.join(args.dir, fn)) as f:
                files[fn] = json.load(f)
        problems = diff_live(files)
        if problems:
            print("%d drift line(s):" % len(problems))
            for p in problems:
                print("  " + p)
            return 1
        print("diff: repo matches live (no drift)")
    elif args.cmd == "apply":
        apply_all(args.dir, args.restart, args.profile, args.collection)


if __name__ == "__main__":
    sys.exit(main() or 0)
