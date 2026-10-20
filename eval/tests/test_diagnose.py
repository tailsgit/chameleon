"""Diagnosis tooling: CV folds keep each design in one fold, the metrics, and the tag server's save / reload."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import eval.tag_server as ts
from eval.critic_cv import folds, metrics


def _row(file, sample, label, n):
    return {"file": file, "sample": sample, "label": label, "case": f"{sample}__t", "output": {"n": n}}


def test_a_design_in_two_files_lands_in_one_fold():
    rows = [_row("a", "d1", 0, 1), _row("a", "d1", 2, 2), _row("b", "d1", 0, 3), _row("b", "d2", 2, 4)]
    fs = folds(rows)
    assert fs == {"a": [0, 1, 2], "b": [3]}


def test_within_design_and_top1():
    rows = [_row("a", "d1", 0, 1), _row("a", "d1", 2, 2), _row("a", "d2", 0, 3), _row("a", "d2", 1, 4)]
    m = metrics([1.0, 2.0, 5.0, 3.0], rows, [90, 90, 90, 80])
    assert m["within_pairs"] == 2 and m["within_pair"] == 0.5 and m["within_mean"] == 0.5
    assert m["top1_bad"] == 0.5 and m["band_n"] == 3


def test_tags_save_and_reload(tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "RESULTS", tmp_path)
    monkeypatch.setattr(ts, "TAGS", {"failure": tmp_path / "failure_tags.json", "recall": tmp_path / "recall_tags.json"})
    server = ThreadingHTTPServer(("127.0.0.1", 0), ts.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/api/tags/failure"
    try:
        assert json.loads(urllib.request.urlopen(url).read()) == {}
        body = json.dumps({"x": {"tag": "other", "note": "n"}}).encode()
        urllib.request.urlopen(urllib.request.Request(url, body, {"Content-Type": "application/json"}))
        assert json.loads(urllib.request.urlopen(url).read()) == {"x": {"tag": "other", "note": "n"}}
    finally:
        server.shutdown()
