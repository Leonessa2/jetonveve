"""CONTRAT.md section 2 dans price_history : offres vides, historique compris."""
import csv, gzip

from scraper import price_history as P


def _cat(tmp, rows):
    p = tmp / "catalogue.csv.gz"
    with gzip.open(p, "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["uuid", "release_date", "floor", "listings"])
        w.writeheader(); w.writerows(rows)
    return str(p)


def _store(tmp, rows):
    p = tmp / "prices.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(P.STORE_HEADER); w.writerows(rows)
    return str(p)


def test_append_ne_compare_que_le_floor(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTRAT_OFFRES_VIDES", "1")
    store = _store(tmp_path, [("a", "2026-11-27T07:00:00.000Z", "10", "4"),
                              ("b", "2026-11-27T07:00:00.000Z", "5", "1")])
    cat = _cat(tmp_path, [{"uuid": "a", "floor": "10", "listings": ""},
                          {"uuid": "b", "floor": "6", "listings": ""}])
    P.run_append(cat, store, store)
    lignes = list(csv.reader(open(store)))[1:]
    assert len(lignes) == 3 and lignes[-1][0] == "b" and lignes[-1][3] == ""


def test_append_eteint_inchange(tmp_path, monkeypatch):
    monkeypatch.delenv("CONTRAT_OFFRES_VIDES", raising=False)
    store = _store(tmp_path, [("a", "2026-11-27T07:00:00.000Z", "10", "4")])
    cat = _cat(tmp_path, [{"uuid": "a", "floor": "10", "listings": "5"}])
    P.run_append(cat, store, store)
    assert len(list(csv.reader(open(store)))) == 3


def test_publish_vide_tout_l_historique(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTRAT_OFFRES_VIDES", "1")
    store = _store(tmp_path, [("a", "2026-11-26T07:00:00.000Z", "10", "4"),
                              ("a", "2026-11-27T07:00:00.000Z", "10", "0")])
    pq, cs = str(tmp_path / "p.parquet"), str(tmp_path / "p.csv.gz")
    P.run_publish(store, pq, cs)
    rows = list(csv.DictReader(gzip.open(cs, "rt")))
    assert len(rows) == 2 and all(r["listings"] == "" for r in rows)
