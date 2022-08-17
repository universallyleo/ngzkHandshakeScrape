import sys
import re
from rich import print
from rich.prompt import Prompt
from pathlib import Path
import requests

# from io import BytesIO
from io import open as iopen  # to make sure we are not using File.open
from bs4 import BeautifulSoup
import json

# copy your cookies data after logged in to forTUNE
# this only has two key-value pairs
cookies = {"": "", "": ""}

# copy your headers data after logged in to forTUNE
headers = {}


BASEFOLDER = Path("")  # path where you want your scrapped data to be saved at
SITEURL = "https://fortunemusic.jp"
BASEURL = "https://fortunemusic.jp/nogizaka_202208/"  # change this depending on which page to scrape
MBDATAFILE = Path(
    "ngzkHandshakeTable/src/lib/data/member.json"
)  # this is the $lib/data/member.json file from ngzkHandshakeTable
RECORDFILE = Path(
    "ngzkHandshakeTable/src/lib/data/data.json"
)  # this is the $lib/data/data.json file from ngzkHandshakeTable
QUICKRUN = True

#############################
# input format e.g.: 2022年8月11日（木・祝）東京都・ベルサール高田馬場
# output format: "2022-08-11"
#############################
def findDate(text):
    a = re.split(r"\D+", text)[0:3]
    if len(a[1]) < 2:
        a[1] = "0" + a[1]
    if len(a[2]) < 2:
        a[2] = "0" + a[2]
    return "-".join(a)


#############################
# Iterator that get all participating member (tested with jupyter)
#############################
def mbListCrawler(start, threshold=12):
    marker = start.next_sibling.next_sibling
    while len(marker) < threshold and len(marker) > 0:
        yield marker.replace("\n", "")
        marker = marker.next_sibling.next_sibling


def mbListScrapeFromTable(soup):  # not tested!!!
    lst = soup.select("form div.tgl02")
    res = {}
    for itm in lst:
        # if itm.find("button", class_="tglHook") is not None:
        for x in itm.select("th.rowHead"):
            res[x.contents[0].stripped_strings[0]] = []
    return res


#############################
# Find tables to scrape
# in: link = url to page containing slots table
#     mblist=JSON object with keys=member's jp name, values=things to scrape
#     mblist will be updated after running this
#############################
def ScrapeTables(link, mblist, namesDict):
    link = SITEURL + link
    scrappage = requests.get(link, cookies=cookies, headers=headers)
    if scrappage.status_code != 200:
        print("[red]Error[/red]:")
        print(scrappage.status_code)
        print(f"Page ([blue]{link}[/blue]) request failed")
        sys.exit()
    soup = BeautifulSoup(scrappage.text, "html.parser")

    if len(soup.select("form.login_form")) > 0:
        print("Need login")
        sys.exit()

    # if len(mblist) == 0:  # scrape member info from table
    #     mblist = mbListScrapeFromTable(soup)
    #     print("Member list scrapped from table")
    #     for k in mblist.keys():
    #         print(f"  {k}")

    lst = soup.select("form div.tgl02")
    for itm in lst:
        if itm.find("span", string="受付終了") is not None:
            date = findDate(itm.find("div", class_="tglHook").string)
            print(f"Reception ended: {date}")
            continue
        else:
            date = findDate(itm.find("button", class_="tglHook").string)
            print(f"Scrape day: {date}")
            for target in itm.select("table tbody tr"):
                scrappedName = target.find("th").string

                # TODO: check this handles all types of N/A slots correctly

                temp = [x for x in target.select("td")]
                row = []
                for x in temp:
                    if x.find("select") is not None:
                        row.append("")
                    elif len(x.select("span.textType01")) > 0:
                        row.append("SOLD")
                    elif len(x.contents) == 1:
                        if next(x.stripped_strings) != "---":
                            print(
                                f"Scraping Contents (len={len(x.contents)}) from {scrappedName}: {x.contents[0]}"
                            )
                        else:
                            row.append("x")
                    else:
                        print(
                            f"Scraping Contents (len={len(x.contents)}) from {scrappedName}: {x.contents[0]}"
                        )
                # print(f"{scrappedName}: {row}")
                mblist[namesDict[scrappedName]].append({"date": date, "soldout": row})
    return mblist


####################################################
# Merge new data with old.  Input var "old" will be modified
####################################################
def updateMBTable(old, new, newentry):
    for day in new:
        for day2 in old:
            if day["date"] == day2["date"]:
                day2["soldout"] = [
                    newentry if x[1] == "" and x[0] != "" else x[1]
                    for x in zip(day["soldout"], day2["soldout"])
                ]
    return old


####################################################
# Main Flow
####################################################
def mainPart(link):
    #############################
    # prepare mb data
    #############################
    print(f"Now loading member data")
    mbfile = (
        Prompt.ask(f"Confirm member data file:", default=str(MBDATAFILE))
        if not QUICKRUN
        else ""
    )
    if mbfile == "":
        mbfile = str(MBDATAFILE)
    # mbfile.encode("unicode escape")
    rawmbdata = json.load(iopen(mbfile, encoding="utf-8"))
    namesDict = {x["kanji"].replace(" ", ""): x["member"] for x in rawmbdata}
    print("Name dictionary loaded [green]✔[/green]")

    #############################
    # scrape participating mb
    #############################
    scrappage = requests.get(link)
    if scrappage.status_code != 200:
        print("[red]Error[/red]:")
        print(scrappage.status_code)
        sys.exit(f"Page ({link}) request failed")

    soup = BeautifulSoup(scrappage.text, "html.parser")
    anchor = soup.find("span", class_="bold", string="【参加メンバー】")
    if anchor is not None:
        participants = {namesDict[x]: [] for x in mbListCrawler(anchor) if len(x) > 0}
        print("Member list scraped [green]✔[/green]")
    else:
        print("Cannot find participant list.  Scrape from table. ❌")

    anchor = soup.find("a", string="お申込みはこちら")
    if anchor is not None:
        tablelink = anchor["href"]
        print(f"Found link to table [green]✔[/green]  [blue]{tablelink}[/blue]")
    else:
        print("Cannot find table to scrape.❌\nAbort process.")
        return

    tb = ScrapeTables(tablelink, participants, namesDict)

    if tb == 0:
        print("Something went wrong when scrapping table.❌\nAbort process.")
        return
    # else:
    #     print("[blue]********  Scrapped Data ******************[/blue]")
    #     print(tb)
    #     print("[blue]******** /Scrapped Data ******************[/blue]")

    print(f"Comparing old data 💦")
    datafile = (
        Prompt.ask("Confirm file", default=str(RECORDFILE)) if not QUICKRUN else ""
    )
    if datafile == "":
        datafile = str(RECORDFILE)
    # datafile.encode("unicode escape")
    #############################
    # read existed record and merge with new
    #############################
    rawdata = json.load(iopen(datafile, encoding="utf-8"))
    cd = rawdata[len(rawdata) - 1]
    print(
        f"CD data: [blue_violet]{cd['cd']['num']} {cd['cd']['type']}[/blue_violet] Previous Draw: {cd['lastDraw']}"
    )
    originaltb = cd["table"]
    dates = cd["meetDates"]
    cd["lastDraw"] += 1
    for mb in originaltb:
        old = [
            {
                "date": row[1],
                "soldout": [x for x in row[0].split("|")],
            }
            for row in zip(mb["slotsSold"], dates)
        ]
        if mb["member"] == "Sugawara Satsuki":
            print("Satsuki:")
            print("old:", old)
            print("new:", tb[mb["member"]])

        res = updateMBTable(
            old, tb[mb["member"]], str(cd["lastDraw"])
        )  # "old" will be updated too; res is just shallow copy of old
        res.sort(key=lambda x: x.get("date"))  # sort in ascending order of date
        mb["slotsSold"] = ["|".join(x["soldout"]) for x in res]
    # now originaltb=cd["table"] is updated

    print("[blue]******** JSON data as follows ******************[/blue]")
    print(cd)
    print("[blue]************************************************[/blue]")

    print(f"New record compiled, now writing to {str(BASEFOLDER / 'updated.json')}")
    #############################
    # Write new record to blank file
    #############################
    with iopen(str(BASEFOLDER / "updated.json"), "w") as outfile:
        json.dump(cd, outfile, indent=3)
    print(f"Write to file completed. 💮")


####################################################
###########   Main Program Starts Here   ###########
####################################################

while True:
    print("~~~~~~~~~ Run ~~~~~~~~~~")
    print("~~~ [blue_violet]NGZK Record scrapper[/blue_violet] ~~~")
    QUICKRUN = (
        False
        if Prompt.ask("🚀Quick run? (Press [orange1]n[/orange1] and enter if not)")
        == "n"
        else True
    )

    link = Prompt.ask("Input URL", default=BASEURL) if QUICKRUN else ""

    mainPart(BASEURL if link == "" else link)

    isRepeat = Prompt.ask(
        "Press [orange1]r[/orange1] to repeat; Press [orange1]ENTER[/orange1] to straight quit."
    )
    if isRepeat == "":
        print("👋 Byebye")
        quit()
