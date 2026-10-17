import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

import eval.review_server as rs

CSV = ("case,sample,format,width,height,passed,violations,total,overlap,small_text,headline,space,alignment,"
       "reading_order,contrast,rules,resize_ms,check_ms,score_ms,render_ms,error\n"
       "s__a,s,A,100,50,True,0,97.5,0,0.1,0,0,0,0,,,1,1,1,,\n"
       "s__b,s,B,50,100,False,1,80,0,0,0,0.5,0,0,,off_canvas:logo,1,1,1,,\n")


@pytest.fixture
def server(tmp_path, monkeypatch):
    (tmp_path / "renders").mkdir()
    (tmp_path / "outputs").mkdir()
    for case in ("s__a", "s__b"):
        (tmp_path / "outputs" / f"{case}.json").write_text(json.dumps({"canvas": {"width": 1, "height": 1}, "v": 1}))
    (tmp_path / "cases.csv").write_text(CSV)
    (tmp_path / "summary.md").write_text("Engine commit `abc123`, 2 cases")
    monkeypatch.setattr(rs, "RESULTS", tmp_path)
    monkeypatch.setattr(rs, "RENDERS", tmp_path / "renders")
    monkeypatch.setattr(rs, "LABELS", tmp_path / "labels.json")
    monkeypatch.setattr(rs, "OUTPUTS", tmp_path / "outputs")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), rs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", tmp_path
    srv.shutdown()


def post(url, body):
    req = urllib.request.Request(url + "/api/labels", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())


def test_cases_and_page(server):
    url, _ = server
    data = json.loads(urllib.request.urlopen(url + "/api/cases").read())
    assert data["commit"] == "abc123"
    assert [c["case"] for c in data["cases"]] == ["s__a", "s__b"]
    assert data["cases"][1]["violations"] == [{"rule": "off_canvas", "id": "logo"}]
    assert b"Chameleon Review" in urllib.request.urlopen(url + "/").read()


def test_verdicts_persist_and_clear(server):
    url, tmp = server
    post(url, {"case": "s__a", "verdict": "good"})
    post(url, {"case": "s__b", "verdict": "bad"})
    saved = json.loads((tmp / "labels.json").read_text())
    assert saved["s__a"]["verdict"] == "good" and saved["s__a"]["score"] == 97.5 and saved["s__a"]["engine"] == "abc123"
    assert saved["s__a"]["output"] == {"canvas": {"width": 1, "height": 1}, "v": 1}  # snapshot of what was judged
    page = json.loads(urllib.request.urlopen(url + "/api/labels").read())
    assert page["s__b"]["verdict"] == "bad" and page["s__b"]["current"] and "output" not in page["s__b"]
    post(url, {"case": "s__a", "verdict": None})
    assert "s__a" not in json.loads((tmp / "labels.json").read_text())


@pytest.mark.parametrize("body", [{"case": "nope", "verdict": "good"}, {"case": "s__a", "verdict": "great"}, {"x": 1}])
def test_rejects_bad_input(server, body):
    url, tmp = server
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url, body)
    assert e.value.code == 400 and not (tmp / "labels.json").exists()


def test_no_path_traversal(server):
    url, _ = server
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(url + "/renders/../cases.csv")
    assert e.value.code == 404


def test_new_output_keeps_the_old_verdict_in_history(server):
    url, tmp = server
    post(url, {"case": "s__a", "verdict": "bad"})
    (tmp / "outputs" / "s__a.json").write_text(json.dumps({"canvas": {"width": 1, "height": 1}, "v": 2}))
    assert not json.loads(urllib.request.urlopen(url + "/api/labels").read())["s__a"]["current"]  # page marks it stale
    post(url, {"case": "s__a", "verdict": "good"})
    post(url, {"case": "s__a", "verdict": "okay"})  # relabelling the same output replaces, no extra history
    saved = json.loads((tmp / "labels.json").read_text())["s__a"]
    assert saved["verdict"] == "okay" and saved["output"]["v"] == 2
    assert [(h["verdict"], h["output"]["v"]) for h in saved["history"]] == [("bad", 1)]
    post(url, {"case": "s__a", "verdict": None})  # clearing keeps the history
    assert json.loads((tmp / "labels.json").read_text())["s__a"] == {"history": saved["history"]}


def test_refuses_a_verdict_without_an_output_snapshot(server):
    url, tmp = server
    (tmp / "outputs" / "s__a.json").unlink()
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url, {"case": "s__a", "verdict": "good"})
    assert e.value.code == 409 and not (tmp / "labels.json").exists()
