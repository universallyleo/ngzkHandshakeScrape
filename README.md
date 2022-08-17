# ngzkHandshakeScrape
Scrape handshake sold data from forTUNE for updating database of [ngzkHandshakeTable](https://github.com/universallyleo/ngzkHandshakeTable)

# Requirements
- Python 3.9+
- Python packages: prompt, pathlib, bs4, json

# To run
1. Install Python 3 and all required packages
2. Config your local data 
```python
BASEFOLDER = Path("")  # path where you want your scrapped data to be saved at
SITEURL = "https://fortunemusic.jp"
BASEURL = "https://fortunemusic.jp/nogizaka_202208/"  # change this depending on which page to scrape
MBDATAFILE = Path("ngzkHandshakeTable/src/lib/data/member.json")  # this is the $lib/data/member.json file from ngzkHandshakeTable
RECORDFILE = Path("ngzkHandshakeTable/src/lib/data/data.json")  # this is the $lib/data/member.json file from ngzkHandshakeTable
```
3. Login to forTUNE and get your cookies and header info.  For the case of Firefox:
   1. Login to forTUNE
   2. Press <kbd>F12</kbd>
   3. Go to Network tab
   4. Reload forTUNE at root page
   5. Under the File column look for "/"
   6. Right click Copy Value, then choose Copy as cURL (Windows)
   7. Choose your own tool to convert cURL to Python dictionary data
4. Open Terminal and run `python forTUNE-scrape.py`
   
# Change Log
- 2022-08-17: First commit