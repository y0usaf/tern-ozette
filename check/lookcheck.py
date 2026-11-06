"""lookcheck: render every look x theme x transparency in a private headless Tern and fail on
low text contrast, changed pixels and CSS over budget. Prints one JSON report; exit 1 on failure.

usage: lookcheck [--static] [--update [LOOK ...]] [--only LOOK ...] [--out DIR]
"""

import argparse, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONF = json.loads((HERE / "looks.json").read_text())
BUDGET = json.loads((HERE / "budget.json").read_text())
STOCK = Path(CONF["stock_css"]).expanduser()
TERN_CFG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "tern"
THEMES = ["light", "dark"]
TRANSPARENCY = ["opaque", "transparent"]
HIDE_TEXT = """*, *::before, *::after, *::marker, *::placeholder {
  color: transparent !important; -webkit-text-fill-color: transparent !important;
  text-shadow: none !important; caret-color: transparent !important;
  text-decoration-color: transparent !important; transition: none !important; }"""


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def selectors(css):
    """Selector preludes of style rules (nested or not)."""
    out = []
    for m in re.finditer(r"([^{};]+)\{", strip_comments(css)):
        pre = m.group(1).strip()
        if pre and not pre.startswith("@") and not re.match(r"^(from|to|[\d.]+%)(\s*,\s*(from|to|[\d.]+%))*$", pre):
            out.append(pre)
    return out


def tokens(sel):
    """Classes and ids a selector needs to match, ignoring :not(...) arguments."""
    while True:
        s = re.sub(r":not\((?:[^()]|\([^()]*\))*\)", "", sel)
        if s == sel:
            break
        sel = s
    sel = re.sub(r"\[[^\]]*\]|'[^']*'|\"[^\"]*\"", "", sel)
    return set(re.findall(r"[.#]-?[_a-zA-Z][\w-]*", sel))


def known_tokens():
    """Classes and ids stock Tern's CSS styles, plus every name in the code of the plugins that draw their own DOM."""
    known = set()
    for f in STOCK.rglob("*.css"):
        for s in selectors(f.read_text()):
            known |= tokens(s)
    for root in [plugin_path(p) for p in CONF["selector_sources"]]:
        for f in root.rglob("*"):
            if f.is_file() and f.stat().st_size < 2 << 20 and ".git" not in f.parts:
                for w in re.findall(r"[_a-zA-Z][\w-]*", f.read_text(errors="replace")):
                    known.update({"." + w, "#" + w})
    return known


def look_files(look):
    files = [REPO / f for f in CONF["base"]] if look == "base" else []
    files += [REPO / f for f in CONF["looks"].get(look, {}).values() if not f.startswith("@")]
    return files


def static(failures):
    known = known_tokens()
    report = {}
    for look in ["base"] + list(CONF["looks"]):
        css = "".join(strip_comments(f.read_text()) for f in look_files(look))
        anim = re.findall(r"animation(?:-iteration-count)?\s*:[^;}]*", css)
        counts = {
            "important": len(re.findall(r"!\s*important", css)),
            "vars": len(re.findall(r"(?<![\w-])--[\w-]+\s*:", css)),
            "infinite": sum("infinite" in a for a in anim),
        }
        used = {f.name: {t for s in selectors(f.read_text()) for t in tokens(s)} for f in look_files(look)}
        unknown = sorted(set().union(*used.values()) - known)
        report[look] = dict(counts, unknown=unknown)
        budget = BUDGET.get(look, {})
        for k, v in counts.items():
            if v > budget.get(k, 0):
                failures.append({"check": "budget", "look": look, "rule": k, "count": v, "budget": budget.get(k, 0)})
        for t in unknown:
            if not any(re.search(p, t) for p in budget.get("unknown", [])):
                failures.append({"check": "selector", "look": look, "token": t, "files": sorted(f for f, ts in used.items() if t in ts)})
    return report


def plugin_path(name):
    link = TERN_CFG / "plugins" / (name + ".path")
    return Path(link.read_text().strip()) if link.exists() else TERN_CFG / "plugins" / name


def plugin_dirs():
    return {name: plugin_path(name) for name in ["ui-menu"] + CONF["plugins"]}


def find_omp():
    """The omp binary; finix's omp-box wrapper names the one it runs."""
    omp = shutil.which("omp")
    if not omp:
        sys.exit("lookcheck: omp is not on PATH")
    head = Path(omp).read_bytes()[:65536]
    if not head.startswith(b"\x7fELF"):
        m = re.search(rb"/nix/store/[a-z0-9]{32}-omp-[^/\s\"']+/bin/omp", head)
        omp = m.group(0).decode() if m else omp
    return omp


class Tern:
    def __init__(self, d):
        self.d = d
        self.sock = d / "ctl.sock"
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("TERN_", "WAYLAND", "DISPLAY", "DBUS_SESSION"))}
        self.env.update(HOME=str(d / "home"), TERN_CONFIG_DIR=str(d / "cfg"), TERN_DAEMON_SOCKET=str(d / "daemon.sock"),
                        XDG_RUNTIME_DIR=str(d / "run"), XDG_STATE_HOME=str(d / "state"), XDG_CACHE_HOME=str(d / "cache"),
                        XDG_CONFIG_HOME=str(d / "xdgcfg"), XDG_DATA_HOME=str(d / "data"), TMPDIR=str(d / "tmp"),
                        STENCIL_LOG_DIR=str(d / "logs"), STENCIL_FIXTURE_ROOT=str(d / "fx/tern"),
                        DBUS_SESSION_BUS_ADDRESS="disabled:", SHELL=shutil.which("bash") or "/bin/sh")

    def setup(self):
        """Private state: copies of the installed settings and plugins (Tern reads plugin files only as regular files)."""
        d = self.d
        for sub in ["home", "cfg/plugin-data/ui-menu", "run", "state", "cache", "xdgcfg", "data", "tmp", "logs",
                    "fx/tern", "fx/plugins/fixtures", "shots", "css"]:
            (d / sub).mkdir(parents=True, exist_ok=True)
        os.chmod(d / "run", 0o700)
        settings = json.loads((TERN_CFG / "settings.json").read_text())
        for k in ("carly", "keybinds"):
            settings.pop(k, None)
        (d / "cfg/settings.json").write_text(json.dumps(settings))
        (d / "cfg/plugin-data/ui-menu/kv.json").write_text(json.dumps({"on": CONF["tweaks"], "mode": "rail"}))
        for name, src in plugin_dirs().items():
            shutil.copytree(src, d / "fx/plugins/fixtures" / name, symlinks=False)
            subprocess.run(["chmod", "-R", "u+w", d / "fx/plugins/fixtures" / name], check=True)
        shutil.copy(HERE / "chat.jsonl", d / "chat.jsonl")
        (d / "css/empty.css").write_text("")
        (d / "css/hide.css").write_text(HIDE_TEXT)

    def c(self, *args, check=True):
        p = subprocess.run(["tern", "ctl", "--control", str(self.sock), *args], env=self.env, capture_output=True, text=True, timeout=120)
        lines = p.stdout.strip().splitlines()
        try:
            j = json.loads(lines[-1].removeprefix("< ")) if lines else {}
        except ValueError:
            j = {"raw": p.stdout}
        if check and not j.get("ok"):
            raise RuntimeError(f"tern ctl {' '.join(args)}: {p.stdout.strip()[-300:]} {p.stderr.strip()[-300:]}")
        return j

    def until(self, what, test, tries=150):
        for _ in range(tries):
            try:
                if test():
                    return
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
            time.sleep(0.2)
        self.c("shot", "stuck", check=False)
        raise RuntimeError(f"Tern: {what} (see {self.d}/tern.log, {self.d}/shots/serve/stuck.png)")

    def start(self, omp):
        d = self.d
        with open(d / "tern.log", "w") as log:
            self.proc = subprocess.Popen(["tern", "serve", "--control", str(self.sock), "--out", str(d / "shots")],
                                         cwd=d / "home", env=self.env, stdout=log, stderr=log, start_new_session=True)
        self.until("did not start", lambda: self.c("state", check=False).get("ok"))
        self.c("plugins", "fixtures")
        self.c("size", *map(str, CONF["size"]), "1")
        self.material()
        sheets = self.c("css")["sheets"]
        base = next(s["name"] for s in sheets if s["name"].endswith("ui-menu-base"))
        self.slot = base[: -len("base")]
        (d / "omp.yml").write_text("startup:\n  quiet: true\n  checkUpdate: false\n  setupWizard: false\n")
        (d / "scene.txt").write_text(f'ready\nrun "{omp} --config {d}/omp.yml --resume {d}/chat.jsonl"\n')
        self.c("--file", str(d / "scene.txt"))
        self.until("the demo chat did not open", lambda: self.c("tree", ".sf-chat-reader").get("count", 0) > 0
                   and self.c("state")["tabs"][0]["title"] == "omp")

    def material(self, solid=False):
        """A headless window ignores the configured material: replay it (solid: stock Tern's opaque one)."""
        settings = json.loads((self.d / "cfg/settings.json").read_text())
        self.c("style", "solid" if solid else settings.get("material", "Clear").lower())
        if not solid and settings.get("material") == "Glass":
            self.c("glass", str(settings.get("opacity", 60)))

    def sheet(self, slot, path):
        self.c("css", self.slot + slot, str(path))

    def stop(self):
        """Quit Tern and end what it left running, sparing this checker and its parents, whose arguments name the directory."""
        try:
            self.c("quit", check=False)
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()
        mine, pid = set(), os.getpid()
        while pid > 1:
            mine.add(pid)
            pid = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])
        left = subprocess.run(["pgrep", "-f", str(self.d)], capture_output=True, text=True).stdout.split()
        for pid in {int(p) for p in left} - mine:
            try:
                os.kill(pid, 15)
            except ProcessLookupError:
                pass

    def snippet(self, f):
        return self.d / "fx/plugins/fixtures/ui-menu/snippets" / f[1:] if f.startswith("@") else REPO / f

    def wear(self, look, transparency):
        combo = self.d / "css/base.css"
        combo.write_text("".join((REPO / f).read_text() for f in CONF["base"]))
        self.sheet("base", combo)
        slots = {s for v in CONF["looks"].values() for s in v}
        for s in sorted(slots):
            f = CONF["looks"][look].get(s)
            self.sheet(s, self.snippet(f) if f else self.d / "css/empty.css")
        self.sheet("transparent", self.snippet(CONF["transparent"]) if transparency == "transparent" else self.d / "css/empty.css")

    def shoot(self, name):
        """Shot of a still frame (every animation at its start), and of the same frame with every glyph made transparent."""
        self.c("thaw")
        self.c("wait", str(CONF["settle_ms"]))
        self.c("motion-at", "0")
        text = self.c("shot", name)
        self.c("css", "lookcheck-hide", str(self.d / "css/hide.css"))
        self.c("wait", "50")
        bare = self.c("shot", name + "-bare")
        self.c("css", "lookcheck-hide")
        self.c("thaw")
        return text["png"], bare["png"], json.loads(Path(text["layout"]).read_text())


def flatten(png):
    im = np.asarray(Image.open(png).convert("RGBA"), dtype=np.float64)
    back = np.array([int(CONF["backdrop"][i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float64)
    a = im[..., 3:4] / 255
    return im[..., :3] * a + back * (1 - a)


def luminance(rgb):
    c = rgb / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722])


def hexcolor(rgb):
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in rgb)


def measure(text_png, bare_png, layout):
    """Contrast of each element's text: its glyph pixels (where the shot differs from the same frame with
    text hidden) against the pixels under them. A glyph pixel belongs to the smallest visible element
    around it; the element's ink is its 98th-percentile glyph pixel. Icons need 3:1, as WCAG asks of graphics."""
    text, bare = flatten(text_png), flatten(bare_png)
    ink = (np.abs(text - bare).max(axis=2) > 2) & ~live(layout, text.shape)
    h, w = ink.shape
    owner = np.full((h, w), -1)
    els = [(i, e) for i, e in enumerate(layout["elements"]) if e["visible"] and e["rect"][2] > 0 and e["rect"][3] > 0]
    for i, e in sorted(els, key=lambda ie: -ie[1]["rect"][2] * ie[1]["rect"][3]):
        x, y, ew, eh = e["rect"]
        owner[max(0, int(y)):min(h, int(np.ceil(y + eh))), max(0, int(x)):min(w, int(np.ceil(x + ew)))] = i
    lt, lb = luminance(text), luminance(bare)
    ratio = (np.maximum(lt, lb) + 0.05) / (np.minimum(lt, lb) + 0.05)
    out = {}
    for i in np.unique(owner[ink]):
        sel = ink & (owner == i)
        if i < 0 or sel.sum() < 12:
            continue
        e = layout["elements"][i]
        r = ratio[sel]
        got = float(np.percentile(r, 98))
        size, weight = float(e["fontSize"].rstrip("px") or 0), int(e["fontWeight"] or 400)
        k = int(np.argmin(np.abs(r - got)))
        ys, xs = np.nonzero(sel)
        out[e["nth"]] = {"element": e["path"], "rect": [round(v) for v in e["rect"]], "contrast": round(got, 2),
                         "need": 3.0 if size >= 24 or (size >= 18.66 and weight >= 700) or ">svg" in e["path"] else 4.5,
                         "ink": hexcolor(text[ys[k], xs[k]]), "behind": hexcolor(bare[ys[k], xs[k]])}
    return out


def contrast(combo, got, base, failures):
    """Below WCAG AA fails, unless stock Tern (no look, solid window) is already as low there."""
    n = 0
    for nth, m in got.items():
        b = base.get(nth)
        if m["contrast"] < m["need"] and (b is None or m["contrast"] < b["contrast"] * 0.95):
            failures.append(dict(check="contrast", combo=combo, stock=b and b["contrast"], **m))
            n += 1
    return n


def live(layout, shape):
    """Where elements showing live data (looks.json "mask") sit: neither pixels nor contrast are judged there."""
    pats = [re.compile(p) for p in CONF["mask"]]
    out = np.zeros(shape[:2], dtype=bool)
    for e in layout["elements"]:
        if e["visible"] and any(p.search(e["path"]) for p in pats):
            x, y, w, h = (int(round(v)) for v in e["rect"])
            out[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = True
    return out


def pixels(combo, text_png, layout, update, failures):
    ref = HERE / "ref" / (combo.replace("/", "-") + ".png")
    now = flatten(text_png).round().astype(np.uint8)
    if update or not ref.exists():
        Image.fromarray(now).save(ref, optimize=True)
        return "written"
    old = np.asarray(Image.open(ref).convert("RGB"))
    if old.shape != now.shape:
        failures.append({"check": "pixels", "combo": combo, "reference": str(ref.relative_to(REPO)), "size": [old.shape, now.shape]})
        return "size"
    diff = (np.abs(old.astype(int) - now.astype(int)).max(axis=2) > 0) & ~live(layout, now.shape)
    n = int(diff.sum())
    if n:
        ys, xs = np.nonzero(diff)
        failures.append({"check": "pixels", "combo": combo, "reference": str(ref.relative_to(REPO)), "changed": n,
                         "bbox": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]})
    return n


def main():
    ap = argparse.ArgumentParser(description="Check Tern looks: contrast, reference pixels, CSS budgets.")
    ap.add_argument("--static", action="store_true", help="only the CSS rules, no Tern")
    ap.add_argument("--update", nargs="*", metavar="LOOK", help="rewrite the reference shots of LOOKs (none named: all)")
    ap.add_argument("--only", nargs="+", metavar="LOOK", help="render only these looks")
    ap.add_argument("--out", type=Path, help="keep the private Tern's state and shots here")
    a = ap.parse_args()
    failures, report = [], {}
    report["static"] = static(failures)
    if not a.static:
        looks = a.only or list(CONF["looks"])
        update = set(CONF["looks"]) if a.update == [] else set(a.update or [])
        d = a.out or Path(tempfile.mkdtemp(prefix="lookcheck-", dir=os.environ.get("XDG_RUNTIME_DIR")))
        t = Tern(d.resolve())
        t.setup()
        report["renders"] = {}
        try:
            t.start(find_omp())
            for theme in THEMES:
                t.c("appearance", theme)
                t.material(solid=True)
                t.wear("none", "opaque")
                base = measure(*t.shoot("stock-" + theme))
                t.material()
                for tr in TRANSPARENCY:
                    for look in looks:
                        combo = f"{look}/{theme}/{tr}"
                        t.wear(look, tr)
                        text_png, bare_png, layout = t.shoot(combo.replace("/", "-"))
                        got = measure(text_png, bare_png, layout)
                        report["renders"][combo] = {
                            "contrast_failures": contrast(combo, got, base, failures),
                            "pixels_changed": pixels(combo, text_png, layout, look in update, failures)}
        finally:
            t.stop()
            if not a.out:
                shutil.rmtree(d, ignore_errors=True)
    report["ok"] = not failures
    report["failures"] = failures
    print(json.dumps(report, indent=1))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
