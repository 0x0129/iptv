import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import strict_rfc3339

sourceIcon51ZMT = "http://epg.51zmt.top:8000"
sourceChengduMulticast = "http://epg.51zmt.top:8000/sctvmulticast.html"
homeLanAddress = "http://192.168.100.1:7088"
homeWanAddress = "http://china-telecom.ie.cx:7099"

groupCCTV = ["CCTV", "CETV", "CGTN"]
groupWS = ["卫视"]
groupSC = ["SCTV", "四川", "CDTV", "熊猫", "峨眉", "成都"]
listUnused = ["单音轨", "画中画", "热门", "直播室", "爱", "92"]

index = 1

def getID():
    global index
    index += 1
    return index - 1

def setID(i):
    global index
    if i >= index:
        index = i + 1
    return index

def isIn(items, v):
    return any(item in v for item in items)

def filterCategory(v):
    if isIn(groupCCTV, v):
        return "CCTV"
    elif isIn(groupWS, v):
        return "卫视"
    elif isIn(groupSC, v):
        return "四川"
    return "其他"

def findIcon(m, channel_name):
    return next((urljoin(sourceIcon51ZMT, v["icon"]) for v in m if v["name"] == channel_name), "")

def loadIcon():
    res = requests.get(sourceIcon51ZMT).content
    soup = BeautifulSoup(res, 'lxml')
    m = []

    for tr in soup.find_all('tr'):
        td = tr.find_all('td')
        if len(td) < 4:
            continue

        href = next((a["href"] for a in td[0].find_all('a', href=True) if a["href"] != "#"), "")
        if href:
            m.append({"id": td[3].string, "name": td[2].string, "icon": href})
    
    return m

def generateM3U8(filename, m, homeAddress):
    with open(filename, "w") as file:
        name = f'成都电信 IPTV - {strict_rfc3339.now_to_rfc3339_utcoffset()}'
        title = f'#EXTM3U name="{name}" url-tvg="http://epg.51zmt.top:8000/e.xml,https://epg.112114.xyz/pp.xml"\n\n'
        file.write(title)

        for k, channels in m.items():
            for c in channels:
                if "dup" in c:
                    continue
                if "ct" in c:
                    line = f'#EXTINF:-1 tvg-logo="{c["icon"]}" tvg-id="{c["id"]}" tvg-name="{c["name"]}" group-title="{k}",{c["name"]}\n'
                    line2 = f'{homeAddress}/rtp/{c["address"]}\n'
                else:
                    line = f'#EXTINF:-1 tvg-id="{getID()}" tvg-name="{c["name"]}" group-title="{k}",{c["name"]}\n'
                    line2 = f'{c["address"]}\n'
                file.write(line)
                file.write(line2)

    print(f"Build {filename} success.")

def generateHome(m):
    generateM3U8("./playlist/iptv-lan.m3u8", m, homeLanAddress)
    generateM3U8("./playlist/iptv-wan.m3u8", m, homeWanAddress)

def main():
    mIcons = loadIcon()

    res = requests.get(sourceChengduMulticast).content
    soup = BeautifulSoup(res, 'lxml')
    m = {}

    for tr in soup.find_all('tr'):
        td = tr.find_all('td')
        if td[0].string == "序号":
            continue

        name = td[1].string.strip()
        if isIn(listUnused, name):
            continue

        setID(int(td[0].string))

        name = re.sub(r'超高清|高清|-', '', name).strip()
        group = filterCategory(name)
        icon = findIcon(mIcons, name)

        m.setdefault(group, []).append({"id": td[0].string, "name": name, "address": td[2].string, "ct": True, "icon": icon})

    generateHome(m)

if __name__ == "__main__":
    main()