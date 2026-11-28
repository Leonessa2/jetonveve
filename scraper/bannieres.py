"""Bannieres de l'accueil de www.veve.me -> release `bannieres` (CONTRAT.md v2).

Decision de Preda (28/11/2026) : les bannieres servent de decor, sans suivi.
`bannieres.csv` = seulement les bannieres affichees sur l'accueil AU MOMENT de
la collecte, remplace a chaque collecte. Colonnes : position, image_ordinateur,
image_mobile, lien. `bannieres.json` porte la date de collecte.

⛔ Page illisible ou aucune banniere -> rien n'est ecrit, sortie en erreur :
la release garde la liste d'avant et le filet donne l'alerte.

D'ou viennent les donnees (mesure du 28/11, sonde-bannieres.yml de
scrapeur-veve) : l'accueil est une page Next.js ; le carrousel y est embarque
dans le flux `self.__next_f.push(...)`, objets `MarketingWindow` (id, position,
isBackup, url, desktopMedia.url, mobileMedia.url, startDate, endDate...).
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
from typing import Dict, List
from urllib.parse import urljoin

import requests

ACCUEIL = "https://www.veve.me/"
UA = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36",
      "accept-language": "en-US,en;q=0.9"}
COLONNES = ["position", "image_ordinateur", "image_mobile", "lien"]
_PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')


def flux_next(html: str) -> str:
    morceaux = []
    for m in _PUSH.findall(html):
        try:
            morceaux.append(json.loads('"' + m + '"'))
        except ValueError:
            morceaux.append(m)
    return "".join(morceaux)


def _absolue(u) -> str:
    u = str(u or "").strip()
    if not u:
        return ""
    return urljoin(ACCUEIL, u)


def extraire(html: str) -> List[Dict[str, str]]:
    """Les bannieres affichees : celles qui ne sont pas « secours » ; s'il n'y en
    a aucune, les bannieres de secours (c'est alors elles que VeVe montre)."""
    texte = flux_next(html) + "\n" + html
    dec = json.JSONDecoder()
    vues: Dict[str, dict] = {}
    for m in re.finditer(r'\{\s*"id"\s*:\s*"', texte):
        try:
            obj, _ = dec.raw_decode(texte, m.start())
        except ValueError:
            continue
        if not isinstance(obj, dict) or "desktopMedia" not in obj or "mobileMedia" not in obj:
            continue
        vues.setdefault(str(obj.get("id")), obj)
    normales = [b for b in vues.values() if not b.get("isBackup")]
    choisies = normales or list(vues.values())
    out = []
    for b in choisies:
        im_o = _absolue((b.get("desktopMedia") or {}).get("url"))
        im_m = _absolue((b.get("mobileMedia") or {}).get("url"))
        if not (im_o or im_m):
            continue
        out.append({"position": b.get("position"), "image_ordinateur": im_o,
                    "image_mobile": im_m, "lien": _absolue(b.get("url"))})
    out.sort(key=lambda r: (r["position"] is None, r["position"] if isinstance(r["position"], (int, float)) else 0))
    for i, r in enumerate(out, 1):
        r["position"] = int(r["position"]) if isinstance(r["position"], (int, float)) else i
    return out


def ecrire(bannieres: List[Dict[str, str]], collecte: dt.datetime, dossier: str = ".") -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLONNES, lineterminator="\n")
    w.writeheader()
    w.writerows(bannieres)
    donnees = buf.getvalue().encode("utf-8")
    with open(f"{dossier}/bannieres.csv", "wb") as f:
        f.write(donnees)
    meta = {"collecte": collecte.strftime("%Y-%m-%dT%H:%M:%SZ"), "lignes": len(bannieres),
            "sha256": hashlib.sha256(donnees).hexdigest(), "source": ACCUEIL}
    with open(f"{dossier}/bannieres.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return meta["sha256"]


def main() -> int:
    collecte = dt.datetime.now(dt.timezone.utc)
    try:
        r = requests.get(ACCUEIL, headers=UA, timeout=60)
    except requests.RequestException as e:
        print(f"[bannieres] ⛔ accueil injoignable : {e} — rien publie, la liste d'avant reste.")
        return 1
    if r.status_code != 200:
        print(f"[bannieres] ⛔ accueil HTTP {r.status_code} — rien publie, la liste d'avant reste.")
        return 1
    b = extraire(r.text)
    if not b:
        print("[bannieres] ⛔ aucune bannière lue sur l'accueil — rien publie, la liste d'avant reste.")
        return 1
    ecrire(b, collecte)
    print(f"[bannieres] {len(b)} bannières, collecte {collecte:%Y-%m-%d %H:%M} UTC")
    for x in b:
        print(f"[bannieres]   {x['position']} | {x['lien']} | {x['image_ordinateur']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
