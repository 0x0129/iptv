import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import strict_rfc3339


sourceTvboxIptv = "https://raw.githubusercontent.com/gaotianliuyun/gao/master/list.txt"
sourceIcon51ZMT = "http://epg.51zmt.top:8000"
sourceChengduMulticast = "http://epg.51zmt.top:8000/sctvmulticast.html"
homeLanAddress = "http://192.168.100.1:7088"

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

def checkChannelExist(listIptv, channel):
    return any(isIn(k, channel) for k in listIptv)

def appendOnlineIptvFromTvbox(listIptv):
    onlineIptv = requests.get(sourceTvboxIptv).content
    lines = onlineIptv.splitlines()
    
    group = None  # Keeps track of current group
    for line in lines:
        line = line.decode('utf-8')
        groupMatch = re.search(r'(.+),#genre#', line)
        if groupMatch:
            group = groupMatch.group(1)
            listIptv.setdefault(group, [])
            continue
        if group == "YouTube":
            continue

        v = line.split(',')
        if checkChannelExist(listIptv, v[0]):
            listIptv[group].append({"id": getID(), "name": v[0], "address": v[1], "dup": True})
        else:
            listIptv[group].append({"id": getID(), "name": v[0], "address": v[1]})

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

def generateM3U8(filename, m):
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
                    line2 = f'{homeLanAddress}/rtp/{c["address"]}\n'
                else:
                    line = f'#EXTINF:-1 tvg-id="{getID()}" tvg-name="{c["name"]}" group-title="{k}",{c["name"]}\n'
                    line2 = f'{c["address"]}\n'
                file.write(line)
                file.write(line2)

    print("Build m3u8 success.")

def generateHome(m):
    generateM3U8("./iptv/iptv.m3u8", m)

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

        name = re.sub(r'超高清|高清|-', '', name).strip()  # Combined string cleaning
        group = filterCategory(name)
        icon = findIcon(mIcons, name)

        m.setdefault(group, []).append({"id": td[0].string, "name": name, "address": td[2].string, "ct": True, "icon": icon})

    appendOnlineIptvFromTvbox(m)
    generateHome(m)

if __name__ == "__main__":
    main()
