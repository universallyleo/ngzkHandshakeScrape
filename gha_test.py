import sys
import requests
from io import open as iopen  # to make sure we are not using File.open
import json

src = "https://raw.githubusercontent.com/universallyleo/ngzkHandshakeTable/main/src/lib/data/data.json"

scrappage = requests.get(src)
if scrappage.status_code != 200:
    print(f"ERROR {scrappage.status_code}: Link ({src}) requset fail")
    sys.exit()

fromfile = str("./31st.json")
fromdata = json.load(iopen(fromfile, encoding="utf-8"))

date = str(sys.argv[1])
tofile = str(f".src/data_{date}.json")
todata = json.load(iopen(tofile, encoding="utf-8"))
todata.append(fromdata)

with iopen(str(f".src/data.json"), "w") as outfile:
    json.dump(todata, outfile, indent=3)

print("OK")
