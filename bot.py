import json
import os
import time
import urllib.parse
import urllib.request

NTFY_KANAL = os.environ["NTFY_KANAL"]
LISTA_URL = "https://www.mitthem.se/rentalobject/Liststudentapartment/published"
SEDDA_FIL = "seen.json"


def hamta_lagenheter():
    url = LISTA_URL + "?" + urllib.parse.urlencode(
        {"sortOrder": "NEWEST", "timestamp": int(time.time() * 1000)}
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (privat bevakning)"}
    )
    with urllib.request.urlopen(req, timeout=30) as svar:
        yttre = json.loads(svar.read().decode("utf-8"))
    if yttre.get("status") != "success":
        raise RuntimeError("Oväntat svar: " + str(yttre)[:200])
    data = yttre["data"]
    return json.loads(data) if isinstance(data, str) else data


def skicka_notis(text, lank):
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_KANAL}",
        data=text.encode("utf-8"),
        headers={
            "Title": "Ny studentlagenhet pa Mitthem",
            "Click": lank,
            "User-Agent": "mitthem-bot",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    try:
        lagenheter = hamta_lagenheter()
    except Exception as fel:
        print("Kunde inte hämta listan:", fel)
        raise SystemExit(1)

    nuvarande = {l["Id"]: l for l in lagenheter}

    sedda = set()
    if os.path.exists(SEDDA_FIL):
        with open(SEDDA_FIL) as f:
            sedda = set(json.load(f))

    for id_, l in nuvarande.items():
        if id_ not in sedda:
            text = (
                f"{l['Adress1'].strip()}, {l['NoOfRooms']} rum, {l['Size']} m², "
                f"{l['Cost']} kr/mån. Ledig från {l['AvailableDate'][:10]}."
            )
            skicka_notis(text, "https://www.mitthem.se" + l["DetailsUrl"])
            print("Notis skickad:", text)

    with open(SEDDA_FIL, "w") as f:
        json.dump(sorted(nuvarande), f)

    print(f"Klar. {len(nuvarande)} lägenhet(er) just nu.")


main()
