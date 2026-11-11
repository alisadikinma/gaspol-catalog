"""Prompt manifest -> slide images through an external image generator (image MCP client)."""
import inspect
import json
import os
import re
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from .prompts import prompt_body, prompt_sha

ENV_CLIENT = "DECKKIT_IMAGE_CLIENT"
NO_CLIENT = "no image client: set image_client in the house standard or DECKKIT_IMAGE_CLIENT"
NO_MODEL = "no model: pass --model or set image_model in the house standard"
_LOCAL = re.compile(r"(?:^|\s)local: (.+?)\s*$", re.M)
_UUID = re.compile(r"uuid[:=]\s*([0-9A-Za-z][0-9A-Za-z-]{2,})")
NO_RESEND = "not resubmitted"
# A job the server marked failed (History status 3). It will never finish, so it is not
# PENDING: the record is cleared so the next run submits a fresh job (2026-11-05).
_SERVER_FAILED = re.compile(r"GeminiGen job \S+ failed: *(.*)")


ENV_REEXEC = "DECKKIT_REEXEC"


def client_python(client_dir):
    """The image client's own interpreter (``<client>/.venv/bin/python``), or None.

    The client's dependencies (its MCP package) usually live only in its own venv, not in the
    venv that runs deckkit, so ``gen`` re-runs itself there when the import fails.
    """
    if not client_dir:
        return None
    py = os.path.join(str(client_dir), ".venv", "bin", "python")
    return py if os.path.isfile(py) and os.access(py, os.X_OK) else None


def load_generator(client_dir=None):
    """The image client's ``generate_image`` callable (FastMCP wrapper unwrapped)."""
    client_dir = client_dir or os.environ.get(ENV_CLIENT)
    if not client_dir:
        raise RuntimeError(NO_CLIENT)
    sys.path.insert(0, str(client_dir))
    try:
        import mcp_image_server as m
    except ImportError as exc:
        raise RuntimeError(f"cannot import mcp_image_server from {client_dir}: {exc}")
    return getattr(m.generate_image, "fn", m.generate_image)


def load_fetcher(client_dir=None):
    """The image client's ``fetch_image(uuid, ...)`` callable, or None if the client has none."""
    client_dir = client_dir or os.environ.get(ENV_CLIENT)
    if not client_dir:
        return None
    sys.path.insert(0, str(client_dir))
    try:
        import mcp_image_server as m
    except ImportError:
        return None
    f = getattr(m, "fetch_image", None)
    return getattr(f, "fn", f) if f else None


class _EventWaiter:
    """Waits on the shared receiver's local event file for one job; binds nothing."""

    def __init__(self, events):
        self._ev = events

    def wait(self, uuid, timeout):
        return self._ev.wait_event(uuid, timeout)

    def close(self):
        pass


def load_notifier(client_dir=None):
    """A waiter on the image client's shared webhook receiver, or None (gen then polls).

    snapgen posts every job of the account to the ONE URL registered in Service
    Integration. One always-on receiver (``scripts.webhook_events``, run as a
    login service) writes each event to a local file; this waits on that file. 2026-11-01: a per-run quick tunnel got no event and gen sat 15 min a slide."""
    client_dir = client_dir or os.environ.get(ENV_CLIENT)
    if not client_dir:
        return None
    sys.path.insert(0, str(client_dir))
    try:
        from scripts import webhook_events
    except ImportError:
        return None
    if not webhook_events.receiver_alive():
        print("webhook off: receiver not running (start: python -m scripts.webhook_events in the image client); "
              "polling the History API", file=sys.stderr)
        return None
    print(f"webhook on: waiting on {webhook_events.events_dir()}", file=sys.stderr)
    return _EventWaiter(webhook_events)


WEBHOOK_WAIT = 900   # seconds to sleep on the webhook before one History check


def _accepts(fn, name):
    try:
        return name in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def _accepts_style(generator):
    try:
        return "style" in inspect.signature(generator).parameters
    except (TypeError, ValueError):
        return False


ASPECT = 16 / 9
ASPECT_TOL = 0.02


def _install(src, dest):
    """Verify ``src`` is a whole, 16:9 image and write it to ``dest`` as PNG (converting if needed).
    Raises ValueError/OSError for anything else, so the caller counts it as a failed attempt."""
    with Image.open(src) as im:
        im.verify()
    with Image.open(src) as im:
        im.load()
        w, h = im.size
        if not h or abs(w / h - ASPECT) > ASPECT * ASPECT_TOL:
            raise ValueError(f"{w}x{h} is not 16:9")
        part = dest.with_name(dest.name + ".part")
        try:
            if im.format == "PNG":
                shutil.copyfile(src, part)
            else:
                im.save(part, "PNG")
            os.replace(part, dest)
        finally:
            part.unlink(missing_ok=True)


STALE = ("stale: prompt changed since render — move the old render to prompts/_rejected/ "
         "(named for the defect) or use a new --ver")


def _sidecar(dest):
    return dest.with_name(dest.name + ".sha")


def _existing_status(dest, item, pf):
    """'exists' or STALE for a render already on disk.

    The sidecar records the sha of the prompt actually sent, so it is compared with the prompt
    file on disk (a revision edits that file, hard rule 7), never with the manifest sha, which a
    hand edit leaves behind. A render with no sidecar is STALE when the manifest carries a sha
    (it cannot be tied to this prompt), else 'exists' (a manifest from before sha tracking)."""
    side = _sidecar(dest)
    if not side.is_file():
        return STALE if item.get("sha") else "exists"
    if not pf.is_file():
        return f"FAIL missing prompt {pf}"
    rendered = side.read_text(encoding="utf-8").strip()
    return "exists" if rendered == prompt_sha(pf.read_text(encoding="utf-8")) else STALE


class _Jobs:
    """Ledger of submitted jobs, ``<raw_dir>/jobs.json``: {"<ver>/<n>": {"uuid", "sha"}}.

    A job is charged the moment the server accepts it, whether or not this
    process lives to download it. Recording its uuid lets the next run collect
    it instead of paying for it again (2026-10-31: ~94 jobs for 13 slides)."""

    def __init__(self, path):
        self.path, self._lock = path, threading.Lock()
        try:
            self.data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}

    def get(self, key, sha):
        e = self.data.get(key)
        return e["uuid"] if e and e.get("sha") == sha else None

    def put(self, key, sha, uuid):
        with self._lock:
            self.data[key] = {"uuid": uuid, "sha": sha}
            self.path.write_text(json.dumps(self.data, indent=1), encoding="utf-8")

    def drop(self, key):
        with self._lock:
            if self.data.pop(key, None) is not None:
                self.path.write_text(json.dumps(self.data, indent=1), encoding="utf-8")


def _one(item, root, generator, out_dir, raw_dir, ver, tries, kw, with_style, fetcher=None, jobs=None,
         notifier=None):
    n = item["n"]
    dest = out_dir / ver / f"{n:02d}.png" if ver else out_dir / f"slide-{n:02d}.png"
    pf = Path(item["prompt_file"])
    pf = pf if pf.is_absolute() else root / pf
    if dest.exists():
        return n, _existing_status(dest, item, pf)
    if not pf.is_file():
        return n, f"FAIL missing prompt {pf}"
    text = pf.read_text(encoding="utf-8")
    sha = prompt_sha(text)
    key = f"{ver or ''}/{n}"
    prompt = prompt_body(text)
    extra = {"style": "None"} if with_style else {}

    def install(r):
        m = _LOCAL.search(r)
        if not (r.startswith("OK") and m and Path(m.group(1)).is_file()):
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        _install(m.group(1), dest)
        _sidecar(dest).write_text(sha + "\n", encoding="utf-8")
        if jobs:
            jobs.drop(key)
        return "OK"

    def server_failed(r):
        m = _SERVER_FAILED.search(r)
        if not m:
            return None
        if jobs:
            jobs.drop(key)
        return (f"FAIL job {uuid} failed on the server ({m.group(1).strip()[:120]}); "
                f"record cleared, rerun gen to submit a new job")

    uuid = jobs.get(key, sha) if jobs else None
    last = "no attempt"
    for _ in range(max(1, tries)):
        try:
            if uuid:
                # a job already exists for this exact prompt: collect it, never submit again
                if not fetcher:
                    return n, f"PENDING uuid {uuid}: job still on the server; collect it with fetch_image"
                r = str(fetcher(uuid=uuid, output_format="png", output_dir=str(raw_dir)))
            else:
                hook = {}
                if notifier is not None and fetcher and _accepts(generator, "wait"):
                    hook = {"wait": False}
                r = str(generator(prompt=prompt, aspect="16:9", output_format="png",
                                  output_dir=str(raw_dir), refs=item.get("refs") or None, **kw, **extra,
                                  **hook))
                found = _UUID.search(r)
                if hook and found and not r.startswith("OK"):
                    uuid = found.group(1)
                    if jobs:
                        jobs.put(key, sha, uuid)
                    # sleep until snapgen's webhook names this job, then collect once
                    notifier.wait(uuid, WEBHOOK_WAIT)
                    r = str(fetcher(uuid=uuid, output_format="png", output_dir=str(raw_dir)))
                    if (dead := server_failed(r)):
                        return n, dead
                    if install(r):
                        return n, "OK"
                    last = r
                    break
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
            if NO_RESEND in last:
                break
            continue
        if (dead := server_failed(r)):
            return n, dead
        try:
            if install(r):
                return n, "OK"
        except Exception as exc:
            last = f"bad image: {type(exc).__name__}: {exc}"
            continue
        last = r
        found = _UUID.search(r)
        if found:
            uuid = found.group(1)
            if jobs:
                jobs.put(key, sha, uuid)
        elif NO_RESEND in r:
            break
    if uuid:
        return n, f"PENDING uuid {uuid}: still rendering; rerun gen to collect it (no new job is made)"
    return n, f"FAIL {last[:200]}"


class _RunLock:
    """``<out>/<ver>/.gen.lock`` holding the pid: a second gen run on the same version
    would submit every slide again (2026-10-31). A lock left by a dead process is taken over."""

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                pid = int(self.path.read_text(encoding="utf-8").strip())
                os.kill(pid, 0)
                alive = True
            except (ValueError, ProcessLookupError):
                alive = False
            except PermissionError:
                alive = True
            if alive:
                raise RuntimeError(f"another gen run (pid {pid}) is already rendering {self.path.parent}; "
                                   "wait for it or stop it first")
        self.path.write_text(str(os.getpid()), encoding="utf-8")
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)
        return False


def run(manifest_path, generator, out_dir=None, raw_dir=None, ver=None, only=None,
        workers=4, tries=3, model=None, mode=None, resolution="2K", fetcher=None, notifier=None):
    """Render every manifest slide; returns [(n, 'OK' | 'exists' | 'FAIL ...')] in manifest order."""
    if not model:
        raise ValueError(NO_MODEL)
    manifest_path = Path(manifest_path).resolve()
    if ver is not None and (not str(ver).strip() or "/" in str(ver) or "\\" in str(ver) or str(ver) in (".", "..")):
        raise ValueError(f"ver {ver!r} must be a plain name, not a path")
    root = manifest_path.parent   # prompt_file entries resolve against the manifest's own directory
    project = root.parent
    out_dir = Path(out_dir) if out_dir else project / "renders"
    raw_dir = Path(raw_dir) if raw_dir else project / ".tmp" / "mentah"
    raw_dir.mkdir(parents=True, exist_ok=True)
    items = json.loads(manifest_path.read_text(encoding="utf-8"))
    if only:
        missing = [n for n in only if n not in {i["n"] for i in items}]
        if missing:
            raise ValueError(f"--only: no such slide n: {', '.join(str(n) for n in missing)}")
        items = [i for i in items if i["n"] in set(only)]
    kw = {"model": model, "mode": mode, "resolution": resolution}
    with_style = _accepts_style(generator)
    jobs = _Jobs(raw_dir / "jobs.json")
    lock_dir = out_dir / ver if ver else out_dir
    with _RunLock(lock_dir / ".gen.lock"), ThreadPoolExecutor(max(1, workers)) as ex:
        return list(ex.map(lambda i: _one(i, root, generator, out_dir, raw_dir, ver, tries, kw, with_style,
                                          fetcher, jobs, notifier), items))
