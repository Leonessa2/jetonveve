"""CONTRAT.md v2 : bannieres de l'accueil de veve.me."""
import csv, json

from scraper import bannieres as B


def _page(objets):
    flux = "10a:" + json.dumps({"state": {"queries": [{"state": {"data": objets}}]}})
    return "<html><script>self.__next_f.push([1," + json.dumps(flux) + "])</script></html>"


def _b(i, pos, backup=False, url="https://www.veve.me/collectibles/en/series/x"):
    return {"id": i, "title": None, "position": pos, "isBackup": backup, "url": url,
            "startDate": "2026-11-23T16:00:00.000Z", "endDate": "2026-12-05T08:00:00.000Z",
            "desktopMedia": {"url": f"https://d11unjture0ske.cloudfront.net/marketing_window_web.{i}.full.jpeg"},
            "mobileMedia": {"url": f"https://d11unjture0ske.cloudfront.net/marketing_window_mobile.{i}.full.jpeg"}}


def test_extraire_trie_et_ecarte_le_secours():
    r = B.extraire(_page([_b("b", 3), _b("a", 1), _b("s", 9, backup=True), _b("a", 1)]))
    assert [x["position"] for x in r] == [1, 3]
    assert r[0]["image_ordinateur"].startswith("https://") and r[0]["lien"].startswith("https://")


def test_secours_seul_est_affiche():
    r = B.extraire(_page([_b("s", 1, backup=True)]))
    assert len(r) == 1


def test_lien_relatif_rendu_complet():
    r = B.extraire(_page([_b("a", 1, url="/blog/news/x/")]))
    assert r[0]["lien"] == "https://www.veve.me/blog/news/x/"


def test_page_sans_banniere():
    assert B.extraire("<html>rien</html>") == []


def test_ecrire(tmp_path):
    import datetime as dt
    B.ecrire(B.extraire(_page([_b("a", 1)])), dt.datetime(2026, 11, 28, 5, 0, tzinfo=dt.timezone.utc), str(tmp_path))
    lignes = list(csv.reader(open(tmp_path / "bannieres.csv", encoding="utf-8")))
    assert lignes[0] == ["position", "image_ordinateur", "image_mobile", "lien"] and len(lignes) == 2
    meta = json.load(open(tmp_path / "bannieres.json"))
    assert meta["collecte"] == "2026-11-28T05:00:00Z" and meta["lignes"] == 1
