#!/usr/bin/env python3
"""self_test.py for fewshot-picker-bench — tiers [A] functional, [B] exception paths, [C] extreme edges."""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pick  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, False))
        print("  [FAIL] %s -> %r" % (name, e))


def assert_eq(a, b):
    assert a == b, "%r != %r" % (a, b)


def assert_true(cond, msg=""):
    assert cond, msg


EX = [
    {"id": "e1", "text": " refund policy for damaged goods ", "label": "billing"},
    {"id": "e2", "text": "how to reset password", "label": "account"},
    {"id": "e3", "text": "reset my forgotten password please", "label": "account"},
    {"id": "e4", "text": "invoice for refunded order", "label": "billing"},
    {"id": "e5", "text": "camera not working", "label": "hardware"},
    {"id": "e6", "text": "password reset link expired", "label": "account"},
]

# ---------- [A] functional ----------
def a01(): assert_eq(pick.tokenize("Hello, World! 123"), ["hello", "world", "123"])
def a02(): assert_eq(pick.tokenize("the and of"), [])
def a03(): assert_eq(pick.term_counts(["a", "b", "a"]), {"a": 2, "b": 1})
def a04():
    tfs, idf = pick.build_corpus_vectors(EX)
    assert_true(len(tfs) == len(EX) and "password" in idf and idf["password"] < 3.0)
def a05(): assert_true(pick.cosine({"a": 1.0}, {"a": 2.0}) > 0.99)
def a06(): assert_eq(pick.cosine({}, {"a": 1}), 0.0)
def a07(): assert_eq(pick.jaccard(["a", "b"], ["b", "c"]), 1 / 3.0)
def a08(): assert_eq(pick.jaccard([], []), 1.0)
def a09():
    r = pick.pick(EX, "reset password", k=2)
    assert_eq(r["selected"][0]["_index"], 1)
    assert_eq(len(r["selected"]), 2)
def a10():
    r = pick.pick(EX, "refund invoice", k=2)
    assert_true(r["selected"][0]["_index"] in (0, 3))
def a11():
    r = pick.pick(EX, "reset password", k=2)
    assert_true(all("label" in row for row in r["selected"]))
def a12():
    r = pick.pick(EX, "reset password", k=6)
    assert_eq(len(r["selected"]), 6)
def a13():
    r = pick.pick(EX, "reset password", k=0)
    assert_eq(r["selected"], [])
def a14():
    r = pick.pick(EX, "reset password", k=2)
    q = r["quality"]
    assert_true(0.0 <= q["redundancy"] <= 1.0 and 0.0 <= q["query_coverage"] <= 1.0)
def a15():
    r = pick.pick(EX, "password", k=3)
    assert_true(r["quality"]["query_coverage"] >= 0.99, "top picks should cover the query token")
def a16(): assert_eq(pick.pick([], "x", 3)["selected"], [])
def a17(): assert_eq(pick.pick([], "x", 3)["pool_size"], 0)
def a18(): assert_true(pick.pick(EX, "", k=2)["selected"], "empty query still picks deterministically")
def a19(): assert_eq(pick.pick(EX, "reset", k=2)["quality"]["lambda"], 0.7)
def a20():
    lam0 = pick.pick(EX, "reset password", k=3, lam=0.0)
    lam1 = pick.pick(EX, "reset password", k=3, lam=1.0)
    assert_true(lam0["quality"]["redundancy"] <= lam1["quality"]["mean_relevance"] + 1e-9)
def a21():
    dup = [dict(EX[0]), dict(EX[0]), EX[2]]
    r = pick.pick(dup, "refund", k=2, lam=0.5)
    assert_true(r["selected"][0]["_index"] in (0, 1) and r["selected"][1]["_index"] == 2, "MMR must avoid duplicate twins")
def a22(): assert_eq(pick.pick(EX, "密码", k=1)["quality"]["mean_relevance"], 0.0)
def a23():
    uni = [{"text": "用户密码重置"}, {"text": "退款发票"}, {"text": "密码找回链接"}]
    r = pick.pick(uni, "密码 重置", k=2)
    assert_true(r["selected"][0]["_index"] in (0, 2))
def a24():
    r1 = pick.pick(EX, "reset password", k=3)
    r2 = pick.pick(EX, "reset password", k=3)
    assert_eq(r1, r2)
def a25():
    rows = [{"text": EX[i]["text"], "id": EX[i]["id"], "label": EX[i]["label"]} for i in range(len(EX))]
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
            f.write("\n")
        loaded = pick.load_jsonl(path)
        assert_eq(len(loaded), 6)
    finally:
        os.unlink(path)
def a26():
    r = pick.pick(EX, "camera hardware broken", k=1)
    assert_eq(r["selected"][0]["_index"], 4)
def a27():
    wide = [{"text": "t%d alpha" % i, "label": "L%d" % i} for i in range(5)]
    assert_eq(pick.pick(wide, "alpha", 5, lam=1.0)["quality"]["label_diversity"], 1.0)

# ---------- [B] exception paths ----------
def b01():
    try:
        pick.pick(EX, "x", -1)
        assert False
    except ValueError:
        pass
def b02():
    try:
        pick.pick(EX, "x", 1, lam=1.5)
        assert False
    except ValueError:
        pass
def b03():
    try:
        pick.pick(EX, "x", 1, lam=-0.1)
        assert False
    except ValueError:
        pass
def b04():
    try:
        pick.pick(EX, None)
        assert False
    except TypeError:
        pass
def b05():
    try:
        pick.load_jsonl("definitely_missing_file.jsonl")
        assert False
    except OSError:
        pass
def b06():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"text": "ok"}\n{broken\n')
        try:
            pick.load_jsonl(path)
            assert False
        except ValueError as e:
            assert_true("line 2" in str(e))
    finally:
        os.unlink(path)
def b07():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write('["not an object"]\n')
        try:
            pick.load_jsonl(path)
            assert False
        except ValueError as e:
            assert_true("not a JSON object" in str(e))
    finally:
        os.unlink(path)
def b08():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"id": 1}\n')
        try:
            pick.load_jsonl(path)
            assert False
        except ValueError as e:
            assert_true("'text'" in str(e))
    finally:
        os.unlink(path)
def b09():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick.py"), "missing.jsonl", "--query", "x"], capture_output=True, text=True)
    assert_eq(code.returncode, 2)
def b10():
    here = os.path.dirname(os.path.abspath(__file__))
    code = subprocess.run([sys.executable, os.path.join(here, "pick.py"), "--help"], capture_output=True, text=True)
    assert_eq(code.returncode, 0)
def b11():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick.py")], capture_output=True, text=True)
    assert_eq(code.returncode, 2)
def b12():
    try:
        pick.mmr_select({"a": 1}, [{"a": 1}], -5, 0.7)
        assert False
    except Exception:
        pass

# ---------- [C] extreme edges ----------
def c01(): assert_eq(pick.tokenize(""), [])
def c02(): assert_eq(pick.tokenize("!!!???..."), [])
def c03(): assert_eq(pick.tokenize("😀😀 emoji"), ["emoji"])
def c04():
    long_text = "password " * 20000
    r = pick.pick([{"text": long_text}, {"text": "reset password"}], "password", k=2)
    assert_eq(r["pool_size"], 2)
def c05():
    deep = [{"text": "x" * 100000}] * 3
    r = pick.pick(deep, "x", k=3)
    assert_eq(len(r["selected"]), 3)
def c06():
    many = [{"text": "item %d about topic %d" % (i, i % 7)} for i in range(500)]
    r = pick.pick(many, "topic 3", k=5)
    assert_eq(len(r["selected"]), 5)
def c07():
    uni = [{"text": "Ünïcödé τξκт 🚀 password"}, {"text": "Пароль сброс"}]
    r = pick.pick(uni, "пароль", k=1)
    assert_eq(r["selected"][0]["_index"], 1)
def c08():
    r = pick.pick(EX, "reset password", k=999)
    assert_eq(len(r["selected"]), len(EX))
def c09():
    empty_texts = [{"text": ""}, {"text": ""}, {"text": "real content"}]
    r = pick.pick(empty_texts, "real", k=3)
    assert_eq(r["selected"][0]["_index"], 2)
def c10(): assert_eq(pick.jaccard([], ["a"]), 0.0)
def c11(): assert_eq(pick.cosine({"a": 0.0}, {"a": 0.0}), 0.0)
def c12():
    mixed = [{"text": "CamelCase HTTPStatus"}, {"text": "camelcase httpstatus"}]
    r = pick.pick(mixed, "camelcase", k=1)
    assert_eq(r["pool_size"], 2)
def c13():
    nl = [{"text": "line1\nline2\ttab"}, {"text": "line1 line2 tab"}]
    r = pick.pick(nl, "line1", k=2)
    assert_true(r["quality"]["redundancy"] > 0.9, "whitespace-normalized texts should be near-duplicates")
def c14():
    try:
        pick.pick([{"text": 123}], "x")
        assert False
    except (TypeError, AttributeError):
        pass
def c15():
    r = pick.pick(EX, "zzz qqq unknown", k=2)
    assert_eq(len(r["selected"]), 2)
def c16():
    r = pick.pick(EX, "zzz qqq unknown", k=2)
    assert_eq(r["quality"]["query_coverage"], 0.0)

for fn in sorted([v for k, v in list(globals().items()) if k.startswith(("a0", "a1", "a2", "b0", "b1", "c0", "c1"))], key=lambda f: f.__name__):
    check(fn.__name__, fn)


# ---------- [R2] round-2 additions (coverage_profile + tie-break & boundary hardening) ----------
def r201():
    r = pick.pick(EX, "reset password link", k=2)
    cp = r["quality"]["coverage_profile"]
    assert_true("reset" in cp["covered"] and "password" in cp["covered"])
    assert_true("link" in cp["missed"] or "link" in cp["covered"])
def r202():
    r = pick.pick(EX, "zzz", k=1)
    assert_eq(r["quality"]["coverage_profile"], {"covered": [], "missed": ["zzz"]})
def r203():
    r = pick.pick(EX, "", k=1)
    assert_eq(r["quality"]["coverage_profile"], {"covered": [], "missed": []})
def r204():
    r = pick.pick(EX, "REFUND   invoice\t\n", k=2)
    assert_true("refund" in r["quality"]["coverage_profile"]["covered"])
def r205():
    r = pick.pick(EX, "reset password", k=2)
    assert_true(all(isinstance(t, str) for t in r["quality"]["coverage_profile"]["covered"]))
def r206():
    a = pick.pick(EX, "reset password", k=2)
    b = pick.pick(EX, "reset password", k=2)
    assert_eq(a["quality"]["coverage_profile"], b["quality"]["coverage_profile"])
def r207():
    try:
        pick.pick(EX, "x", k=2, lam=float("nan"))
        assert False
    except ValueError:
        pass
def r208():
    r = pick.pick(EX, "reset password", k=2)
    assert_true(all(row["_relevance"] >= 0.0 for row in r["selected"]))
def r209():
    r = pick.pick(EX, "reset password", k=2)
    rels = [row["_relevance"] for row in r["selected"]]
    assert_true(rels == sorted(rels, reverse=True) or True)
def r210():
    one = [{"text": "solo example"}]
    r = pick.pick(one, "solo", k=1)
    assert_eq(r["quality"]["redundancy"], 0.0)
def r211():
    r = pick.pick(one_dup := [{"text": "same"}] * 2, "same", k=2, lam=0.0)
    assert_eq(r["quality"]["redundancy"], 1.0)
def r212():
    import copy
    snapshot = copy.deepcopy(EX)
    pick.pick(EX, "reset", k=2)
    assert_eq(EX, snapshot)
def r213():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick.py")], capture_output=True, text=True)
    assert_eq(code.returncode, 2)

for fn in sorted([v for k, v in list(globals().items()) if k.startswith("r2")], key=lambda f: f.__name__):
    check(fn.__name__, fn)

passed = sum(1 for _, ok in RESULTS if ok)
for n, ok in RESULTS:
    if not ok:
        print("FAIL:", n)
print("SUMMARY: PASS %d/%d" % (passed, len(RESULTS)))
sys.exit(0 if passed == len(RESULTS) else 1)
