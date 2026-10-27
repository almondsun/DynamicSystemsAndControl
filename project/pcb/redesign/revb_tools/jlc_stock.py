"""Record JLCPCB assembly stock for every LCSC code of a BOM (public parts search, no login).

    python3 -I jlc_stock.py <bom_jlcpcb.csv> <out.json>
stockCount is JLCPCB's assembly warehouse quantity; it is a snapshot, not a reservation.
"""
import csv
import datetime
import json
import sys
import time
import urllib.request

URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"


def query(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 10}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json",
                                                         "User-Agent": "Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=40).read())
    for it in ((data.get("data") or {}).get("componentPageInfo") or {}).get("list") or []:
        if it["componentCode"] == code:
            return {"mpn": it["componentModelEn"], "brand": it["componentBrandEn"],
                    "package": it["componentSpecificationEn"], "library": it["componentLibraryType"],
                    "stock": it["stockCount"], "buyable": it.get("isBuyComponent"),
                    "min_purchase": it.get("minPurchaseNum")}
    return None


def main() -> None:
    rows = list(csv.DictReader(open(sys.argv[1], newline="", encoding="utf-8")))
    out = {"checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "source": URL, "parts": []}
    for r in rows:
        code = r["LCSC Part #"]
        qty_per_board = len(r["Designator"].split(","))
        try:
            info = query(code)
        except Exception as exc:  # recorded, never hidden
            info = {"error": f"{type(exc).__name__}: {exc}"}
        out["parts"].append({"lcsc": code, "designators": r["Designator"], "qty_per_board": qty_per_board,
                             "bom_mpn": r.get("MPN", ""), **(info or {"error": "code not found"})})
        time.sleep(0.5)
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for p in out["parts"]:
        flag = "OK" if isinstance(p.get("stock"), int) and p["stock"] >= 5 * p["qty_per_board"] else "CHECK"
        print(flag, p["lcsc"], p.get("mpn"), p.get("library"), "stock", p.get("stock"), "need5", 5 * p["qty_per_board"],
              p.get("error", ""))


if __name__ == "__main__":
    main()
