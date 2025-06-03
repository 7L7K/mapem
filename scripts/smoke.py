import requests, json, sys
BASE = "http://localhost:5050/api"
tid  = sys.argv[1] if len(sys.argv) > 1 else "3"

for ep in [
    "/trees",
    f"/trees/{tid}/counts",
    f"/people/{tid}?limit=3",
    f"/events?tree_id={tid}&limit=3",
    f"/trees/{tid}/visible-counts?filters=" + json.dumps({
         "yearRange":[1800,1950],
         "eventTypes":{"birth":True,"death":True,"residence":True},
         "relations":{"self":True,"parents":True,"siblings":True},
         "sources":{"gedcom":True,"census":True,"manual":True},
         "vague":False
     })
]:
    r = requests.get(BASE+ep)
    print(ep, r.status_code, r.json() if r.ok else r.text[:200])
