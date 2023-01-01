import datetime
import json
import os.path
import sqlite3
import time
import traceback
from urllib.parse import quote
import pymysql

from modules.musics import idtoname
from modules.mysql_config import *
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import matplotlib
import pytz
import requests
import yaml
from matplotlib import pyplot as plt, ticker
from matplotlib.font_manager import FontProperties

from modules.config import apiurl, predicturl, proxies, ispredict, enapiurl, twapiurl, krapiurl, piccacheurl

rankline = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 100, 200, 300, 400, 500, 1000, 2000, 3000, 4000, 5000,
            10000, 20000, 30000, 40000, 50000, 100000, 100000000]
predictline = [100, 200, 300, 400, 500, 1000, 2000, 3000, 4000, 5000, 10000, 20000, 30000, 40000, 50000, 100000, 100000000]




def timeremain(time, second=True):
    if time < 60:
        return f'{int(time)}秒' if second else '0分'
    elif time < 60*60:
        return f'{int(time / 60)}分{int(time % 60)}秒' if second else f'{int(time / 60)}分'
    elif time < 60*60*24:
        hours = int(time / 60 / 60)
        remain = time - 3600 * hours
        return f'{int(time / 60 / 60)}小时{int(remain / 60)}分{int(remain % 60)}秒' if second else f'{int(time / 60 / 60)}小时{int(remain / 60)}分'
    else:
        days = int(time / 3600 / 24)
        remain = time - 3600 * 24 * days
        return f'{int(days)}天{timeremain(remain)}' if second else f'{int(days)}天{timeremain(remain, False)}'


def currentevent(server):
    if server == 'jp':
        with open('masterdata/events.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif server == 'tw':
        with open('../twapi/masterdata/events.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif server == 'en':
        with open('../enapi/masterdata/events.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif server == 'kr':
        with open('../krapi/masterdata/events.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    for i in range(0, len(data)):
        startAt = data[i]['startAt']
        endAt = data[i]['closedAt']
        assetbundleName = data[i]['assetbundleName']
        now = int(round(time.time() * 1000))
        remain = ''
        if not startAt < now < endAt:
            continue
        if data[i]['startAt'] < now < data[i]['aggregateAt']:
            status = 'going'
            remain = timeremain((data[i]['aggregateAt'] - now) / 1000)
        elif data[i]['aggregateAt'] < now < data[i]['aggregateAt'] + 600000:
            status = 'counting'
        else:
            status = 'end'
        return {'id': data[i]['id'], 'status': status, 'remain': remain, 'assetbundleName': assetbundleName}


def eventtrack():
    twurl = 'http://127.0.0.1:5004/tw/api'
    now = int(time.time())
    time_printer('开始抓取冲榜查询id')
    event = currentevent('jp')
    if event['status'] == 'going':
        eventid = event['id']
        if not os.path.exists(f'yamls/event/{eventid}'):
            os.makedirs(f'yamls/event/{eventid}')
        try:
            conn = sqlite3.connect('data/events.db')
            c = conn.cursor()
            resp = requests.get(f'{apiurl}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank=1&lowerLimit=99', timeout=10)
            ranking = json.loads(resp.content)
            for rank in ranking['rankings']:
                targetid = rank['userId']
                score = rank['score']
                name= rank['name']
                try:
                    c.execute(f'insert into "{eventid}" (time, score, userid) values(?, ?, ?)', (now, score, str(targetid)))
                except sqlite3.OperationalError:
                    c.execute(f'''CREATE TABLE "{eventid}"
                               ("time"   INTEGER,
                                "score"  INTEGER,
                                "userid" TEXT);''')
                    c.execute(f'insert into "{eventid}" (time, score, userid) values(?, ?, ?)',
                              (now, score, str(targetid)))

                try:
                    c.execute(f'insert into names (userid, name) values(?, ?)', (str(targetid), name))
                except sqlite3.IntegrityError:
                    c.execute(f'update names set name=? where userid=?', (name, str(targetid)))

            resp = requests.get(f'{apiurl}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank=101&lowerLimit=99', timeout=10)
            ranking = json.loads(resp.content)
            for rank in ranking['rankings']:
                targetid = rank['userId']
                score = rank['score']
                name = rank['name']
                c.execute(f'insert into "{eventid}" (time, score, userid) values(?, ?, ?)', (now, score, str(targetid)))
                try:
                    c.execute(f'insert into names (userid, name) values(?, ?)', (str(targetid), name))
                except sqlite3.IntegrityError:
                    c.execute(f'update names set name=? where userid=?', (name, str(targetid)))

            conn.commit()
            conn.close()
            time_printer('抓取完成')
        except:
            traceback.print_exc()
    else:
        time_printer('无正在进行的活动')


    time_printer('开始抓取台服冲榜查询id')
    event = currentevent('tw')
    if event['status'] == 'going':
        eventid = event['id']
        if not os.path.exists(f'yamls/event/tw{eventid}'):
            os.makedirs(f'yamls/event/tw{eventid}')
        try:
            conn = sqlite3.connect('data/events.db')
            c = conn.cursor()
            resp = requests.get(f'{twurl}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank=1&lowerLimit=99', timeout=10)
            ranking = json.loads(resp.content)
            for rank in ranking['rankings']:
                targetid = rank['userId']
                score = rank['score']
                name= rank['name']
                try:
                    c.execute(f'insert into "tw{eventid}" (time, score, userid) values(?, ?, ?)', (now, score, str(targetid)))
                except sqlite3.OperationalError:
                    c.execute(f'''CREATE TABLE "tw{eventid}"
                               ("time"   INTEGER,
                                "score"  INTEGER,
                                "userid" TEXT);''')
                    c.execute(f'insert into "tw{eventid}" (time, score, userid) values(?, ?, ?)',
                              (now, score, str(targetid)))

                try:
                    c.execute(f'insert into names (userid, name) values(?, ?)', (str(targetid), name))
                except sqlite3.IntegrityError:
                    c.execute(f'update names set name=? where userid=?', (name, str(targetid)))

            resp = requests.get(f'{twurl}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank=101&lowerLimit=99', timeout=10)
            ranking = json.loads(resp.content)
            for rank in ranking['rankings']:
                targetid = rank['userId']
                score = rank['score']
                name = rank['name']
                c.execute(f'insert into "tw{eventid}" (time, score, userid) values(?, ?, ?)', (now, score, str(targetid)))
                try:
                    c.execute(f'insert into names (userid, name) values(?, ?)', (str(targetid), name))
                except sqlite3.IntegrityError:
                    c.execute(f'update names set name=? where userid=?', (name, str(targetid)))

            conn.commit()
            conn.close()
            time_printer('抓取完成')
        except:
            traceback.print_exc()
    else:
        time_printer('台服无正在进行的活动')


class Error(Exception):
   pass

class cheaterFound(Error):
   pass

class maintenanceIn(Error):
   pass


def recordname(qqnum, userid, name, userMusicResults=None, masterscore=None, server='jp'):
    try:
        mydb = pymysql.connect(host=host, port=port, user='username', password=password,
                            database='username', charset='utf8mb4')
    except pymysql.err.OperationalError:
        return True
    mycursor = mydb.cursor()

    # 审核游戏昵称
    mycursor.execute('SELECT * from examresult where name=%s', (name,))
    data = mycursor.fetchone()
    if data is not None:
        if data[2]:
            result = True
        else:
            result = False
    else:
        try:
            resp = requests.get(f'http://127.0.0.1:5000/exam/{quote(name.replace("/", " "), "utf-8")}')
            sql_add = 'insert into examresult (name, result) values(%s, %s)'
            result = resp.json()['conclusion']
        except:
            traceback.print_exc()
            result = True
        if result:
            mycursor.execute(sql_add, (name, 1))
        else:
            mycursor.execute(sql_add, (name, 0))

    # 记录游戏昵称
    mycursor.execute('SELECT * from names where qqnum=%s and userid=%s and name=%s', (str(qqnum), str(userid), name))
    data = mycursor.fetchone()
    if data is None:
        sql_add = f'insert into names (userid, name, qqnum, result) values(%s, %s, %s, %s)'
        text = '合规' if result else '不合规'
        mycursor.execute(sql_add, (str(userid), name, str(qqnum), text))

    qqnum = getIdOwner(userid, server)
    if userMusicResults is not None:
        # 判断是否有36+FC/AP
        if masterscore[36][0] + masterscore[36][1] + masterscore[37][0] + masterscore[37][1] != 0:
            mycursor.execute('SELECT * from suspicious where qqnum=%s and userid=%s', (str(qqnum), str(userid)))
            data = mycursor.fetchone()
            if data is None:
                sql_add = f'insert into suspicious (userid, name, qqnum, reason) values(%s, %s, %s, %s)'
                mycursor.execute(sql_add, (str(userid), name, str(qqnum), '36+FC/AP'))
        alltext = ''
        # 判断是否有33+初见FC/AP
        for result in userMusicResults:
            if result["musicDifficulty"] == 'master' and result["musicId"] in masterscore['33+musicId']:
                if result["fullComboFlg"] or result["fullPerfectFlg"]:
                    if result["updatedAt"] == result["createdAt"]:
                        reason = idtoname(result["musicId"]) + ' ' + result['playType'] + ' 初见' \
                                 + ('AP' if result["fullPerfectFlg"] else 'FC')
                        alltext += reason + '，'
                        mycursor.execute('SELECT * from suspicious where qqnum=%s and userid=%s and reason=%s',
                                         (str(qqnum), str(userid), reason))
                        data = mycursor.fetchone()
                        if data is None:
                            sql_add = f'insert into suspicious (userid, name, qqnum, reason) values(%s, %s, %s, %s)'
                            mycursor.execute(sql_add, (str(userid), name, str(qqnum), reason))
                        if data is not None:
                            if data[6] == 'whitelist':
                                mydb.commit()
                                mycursor.close()
                                mydb.close()
                                return result
        if alltext != '':
            mydb.commit()
            mycursor.close()
            mydb.close()
            raise cheaterFound(alltext)
    mydb.commit()
    mycursor.close()
    mydb.close()
    return result


def chafang(targetid=None, targetrank=None, private=False, server='jp'):
    if server == 'jp':
        url = apiurl
        prefix = ''
    elif server == 'en':
        url = enapiurl
        prefix = 'en'
    elif server == 'tw':
        url = twapiurl
        prefix = 'tw'
    event = currentevent(server)
    eventid = event['id']
    if targetid is None:
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={targetrank}', timeout=10)
        ranking = json.loads(resp.content)
        targetid = ranking['rankings'][0]['userId']
        private = True
    if event['status'] == 'going':
        conn = sqlite3.connect('data/events.db')
        c = conn.cursor()
        cursor = c.execute(f'SELECT * from "{prefix}{eventid}" where userid=?', (targetid,))
        userscores = {}
        for raw in cursor:
            userscores[raw[0]] = raw[1]
        if userscores == {}:
            conn.close()
            return '你要查询的玩家未进入前200，暂无数据'
        lasttime = 0
        twentybefore = 0
        hourbefore = 0
        cursor = c.execute(f'SELECT * from names where userid=?', (targetid,))
        for raw in cursor:
            username = raw[1]
        conn.close()
        if private:
            text = f'{username}\n'
        else:
            text = f'{username} - {targetid}\n'
        for times in userscores:
            lasttime = times
        for times in userscores:
            if -10 < times - (lasttime - 20 * 60) < 10:
                twentybefore = times
        for times in userscores:
            if -10 < times - (lasttime - 60 * 60) < 10:
                hourbefore = times
        lastupdate = 0
        count = 0
        hourcount = 0
        pts = []
        for times in userscores:
            count += 1
            if count == 1:
                lastupdate = userscores[times]
            else:
                if userscores[times] != lastupdate:
                    if hourbefore != 0 and times > hourbefore:
                        hourcount += 1
                        # print(hourcount, datetime.datetime.fromtimestamp(times,
                        #                                       pytz.timezone('Asia/Shanghai')).strftime('%H:%M'))
                    pts.append(userscores[times]-lastupdate)
                    lastupdate = userscores[times]
        if len(pts) >= 10:
            ptsum = 0
            for i in range(len(pts)-10, len(pts)):
                ptsum += pts[i]
            text += f'近10次平均pt：{(ptsum / 10)/10000}W\n'
        if hourbefore != 0:
            text += f'时速: {(userscores[lasttime] - userscores[hourbefore])/10000}W\n'
        if twentybefore != 0:
            text += f'20min*3时速: {((userscores[lasttime] - userscores[twentybefore])*3)/10000}W\n'
        if hourcount != 0:
            text += f'本小时周回数: {hourcount}\n'
        stop = getstoptime(targetid, None, True, server=server)
        if len(stop) != 0:
            if stop[len(stop)]['end'] != 0:
                text += '周回中\n'
                text += f"连续周回时间: {timeremain(int(time.time()) - stop[len(stop)]['end'])}\n"
            else:
                text += '停车中\n'
                text += f"已停车: {timeremain(int(time.time()) - stop[len(stop)]['start'])}\n"
        else:
            for times in userscores:
                if times == 'name':
                    continue
                firsttime = times
                break
            text += '周回中\n'
            text += f"连续周回时间: {timeremain(int(time.time()) - firsttime)}\n"
            updatetime = datetime.datetime.fromtimestamp(lasttime,
                                       pytz.timezone('Asia/Shanghai')).strftime('%m/%d %H:%M')
            text += f"仅记录在200名以内时的数据，数据更新于{updatetime}"
        return text
    else:
        return '当前没有正在进行的活动'

def drawscoreline(targetid=None, targetrank=None, targetrank2=None, starttime=0, server='jp'):
    x = []
    x2 = []
    k = []
    k2 = []
    if server == 'jp':
        url = apiurl
        prefix = ''
    elif server == 'en':
        url = enapiurl
        prefix = 'en'
    elif server == 'tw':
        url = twapiurl
        prefix = 'tw'
    event = currentevent(server)
    eventid = event['id']
    if targetid is None:
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={targetrank}', timeout=10)
        ranking = json.loads(resp.content)
        targetid = ranking['rankings'][0]['userId']

    conn = sqlite3.connect('data/events.db')
    c = conn.cursor()
    cursor = c.execute(f'SELECT * from "{prefix}{eventid}" where userid=?', (targetid,))
    userscores = {}
    for raw in cursor:
        userscores[raw[0]] = raw[1]
    if userscores == {}:
        conn.close()
        return False
    cursor = c.execute(f'SELECT * from names where userid=?', (targetid,))
    for raw in cursor:
        name = raw[1]
    if targetrank2 is not None:
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={targetrank2}', timeout=10)
        ranking = json.loads(resp.content)
        targetid2 = ranking['rankings'][0]['userId']
        cursor = c.execute(f'SELECT * from "{prefix}{eventid}" where userid=?', (targetid2,))
        userscores2 = {}
        for raw in cursor:
            userscores2[raw[0]] = raw[1]
        cursor = c.execute(f'SELECT * from names where userid=?', (targetid2,))
        for raw in cursor:
            name2 = raw[1]
        conn.close()
        for times in userscores:
            if times > starttime:
                try:
                    k2.append(userscores2[times] / 10000)
                except:
                    k2.append(0)
    else:
        conn.close()

    for times in userscores:
        if times > starttime:
            x.append(times)
            k.append(userscores[times] / 10000)
    for timestamp in x:
        timeArray = time.localtime(timestamp)
        otherStyleTime = time.strftime("%m-%d %H:%M", timeArray)
        x2.append(otherStyleTime)
    fig, ax = plt.subplots(1, 1)

    font = FontProperties(fname="fonts/FOT-RodinNTLGPro-DB.ttf")
    plt.plot(x2, k, color='r', label=name)
    if targetrank2 is not None:
        matplotlib.rcParams['font.sans-serif'] = ['SimHei']
        plt.plot(x2, k2, color='b', label=name2)
        plt.title(f"{name}(Red) vs {name2}(Blue)", fontproperties=font)
        targetid = str(targetid) + str(targetid2)
        plt.legend()
    else:
        plt.title(name, fontproperties=font)
    plt.xlabel("時間", fontproperties=font)  # 横坐标名字
    plt.ylabel("スコア / 万", fontproperties=font)  # 纵坐标名字
    ax.xaxis.set_major_locator(ticker.MultipleLocator(len(x) / 4.5))
    plt.text(x2[int(len(x2)*0.7)], k[0], 'Generated by Unibot', fontproperties=font)
    plt.savefig(f'piccache/{targetid}.png')
    return f'piccache/{targetid}.png'

def time_printer(str):
    timeArray = time.localtime(time.time())
    Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    print(Time, str)

def getstoptime(targetid=None, targetrank=None, returnjson=False, private=False, server='jp'):
    event = currentevent(server)
    eventid = event['id']
    if server == 'jp':
        url = apiurl
        prefix = ''
    elif server == 'en':
        url = enapiurl
        prefix = 'en'
    elif server == 'tw':
        url = twapiurl
        prefix = 'tw'
    if not returnjson:
        if targetid is None:
            resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={targetrank}', timeout=10)
            ranking = json.loads(resp.content)
            targetid = ranking['rankings'][0]['userId']
            private = True
    conn = sqlite3.connect('data/events.db')
    c = conn.cursor()
    cursor = c.execute(f'SELECT * from "{prefix}{eventid}" where userid=?', (targetid,))
    userscores = {}
    for raw in cursor:
        userscores[raw[0]] = raw[1]
    if userscores == {}:
        conn.close()
        if returnjson:
            return {}
        return False
    cursor = c.execute(f'SELECT * from names where userid=?', (targetid,))
    for raw in cursor:
        username = raw[1]
    conn.close()
    lastupdate = 0
    count = 0
    stop = {}
    stopcount = 0
    stopping = False
    stoplength = 0
    for times in userscores:
        count += 1
        if count == 1:
            lastupdate = times
        else:
            if userscores[times] == userscores[lastupdate]:
                if times - lastupdate > 5 * 60:
                    if not stopping:
                        stopcount += 1
                        stopping = True
                        stop[stopcount] = {'start': 0, 'end': 0}
                        stop[stopcount]['start'] = lastupdate
            else:
                lastupdate = times
                if stopping:
                    stop[stopcount]['end'] = times
                    stopping = False

    if private:
        text = f'{username}\n停车时间段:\n'
    else:
        text = f'{username} - {targetid}\n停车时间段:\n'
    if returnjson:
        return stop
    if len(stop) != 0:
        for count in stop:
            start = stop[count]['start']
            starttime = datetime.datetime.fromtimestamp(start,
                                       pytz.timezone('Asia/Shanghai')).strftime('%m/%d %H:%M')
            end = stop[count]['end']
            endtime = datetime.datetime.fromtimestamp(end,
                                       pytz.timezone('Asia/Shanghai')).strftime('%m/%d %H:%M')
            if end == 0:
                endtime = ''
                end = int(time.time())
            stoplength += end - start
            text += f'{count}. {starttime} ~ {endtime} ({timeremain(end - start, False)})\n'
        text += f'总停车时间：{timeremain(stoplength, False)}\n'
        text += f"仅记录在200名以内时的数据"
        return text
    else:
        if returnjson:
            return stop
        return text + '未停车' + "\n仅记录在200名以内时的数据"

def getranks():
    time_printer('抓取时速')
    event = currentevent('jp')
    if event['status'] == 'going':
        eventid = event['id']
        if not os.path.exists(f'yamls/event/{eventid}'):
            os.makedirs(f'yamls/event/{eventid}')
        try:
            with open(f'yamls/event/{eventid}/ss.yaml') as f:
                ss = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            ss = {}
        now = int(time.time())
        ss[now] = {}
        for rank in rankline:
            if rank != 100000000:
                try:
                    resp = requests.get(f'{apiurl}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={rank}', timeout=10)
                    ranking = json.loads(resp.content)
                    ss[now][rank] = ranking['rankings'][0]['score']
                except:
                    traceback.print_exc()
                    ss[now][rank] = 0
        with open(f'yamls/event/{eventid}/ss.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(ss, f)
        time_printer('时速抓取完成')
    else:
        time_printer('无正在进行的活动')

def ss():
    event = currentevent('jp')
    eventid = event['id']
    if event['status'] == 'going':
        try:
            with open(f'yamls/event/{eventid}/ss.yaml') as f:
                ss = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            return '暂无数据'
        text = ''
        hourago = 0
        for times in ss:
            lasttime = times
        for times in ss:
            if -120 < times - (lasttime - 60 * 60) < 120:
                hourago = times
                break
        if hourago != 0:
            for rank in rankline:
                if rank != 100000000:
                    speed = ss[lasttime][rank] - ss[hourago][rank]
                    text += f'{rank}: {speed/10000}W\n'
            Time = datetime.datetime.fromtimestamp(lasttime,
                                                   pytz.timezone('Asia/Shanghai')).strftime('%m/%d %H:%M:%S')
            return '一小时内实时时速\n' + text + '数据更新时间\n' + Time
        else:
            return '暂无数据'
    else:
        return '活动未开始'

def gettime(userid, server='jp'):
    if server == 'jp' or server == 'en':
        try:
            passtime = int(userid[:-3]) / 1024 / 4096
        except ValueError:
            return 0
        return 1600218000 + int(passtime)
    elif server == 'tw' or server == 'kr':
        try:
            passtime = int(userid) / 1024 / 1024 / 4096
        except ValueError:
            return 0
        return int(passtime)


def verifyid(userid, server='jp'):
    registertime = gettime(userid, server)
    now = int(time.time())
    if registertime <= 1601438400 or registertime >= now:
        return False
    else:
        return True


def ssyc(targetrank, eventid):
    try:
        with open('data/ssyc.yaml') as f:
            cachedata = yaml.load(f, Loader=yaml.FullLoader)
        cachetime = cachedata['cachetime']
        now = int(time.time())
        timepass = now - cachetime
        if timepass < 60 * 30 + 10:
            return cachedata[targetrank]
    except FileNotFoundError:
        cachedata = {}
    predict = json.loads(requests.get(predicturl, proxies=proxies).content)
    if predict['data']['eventId'] != eventid:
        now = int(time.time())
        cachedata['cachetime'] = now
        for i in range(0, 16):
            cachedata[predictline[i]] = 0
        with open('data/ssyc.yaml', 'w') as f:
            yaml.dump(cachedata, f)
        return 0
    cachedata['cachetime'] = int(predict['data']['ts'] / 1000)
    for i in range(0, 16):
        cachedata[predictline[i]] = predict['data'][str(predictline[i])]
    with open('data/ssyc.yaml', 'w') as f:
        yaml.dump(cachedata, f)
    return predict['data'][str(targetrank)]

def skyc():
    text = ''
    event = currentevent('jp')
    eventid = event['id']
    if event['status'] != 'going':
        return '预测暂时不可用'
    try:
        with open('data/ssyc.yaml') as f:
            cachedata = yaml.load(f, Loader=yaml.FullLoader)
        if cachedata[100] == 0:
            return '预测暂时不可用'
        cachetime = cachedata['cachetime']
        now = int(time.time())
        timepass = now - cachetime
        if timepass < 60 * 30 + 10:
            for i in range(0, len(predictline)-1):
                text = text + f'{predictline[i]}名预测：{cachedata[predictline[i]]}\n'
            timeArray = time.localtime(cachetime)
            text = text + '\n预测线来自xfl03(3-3.dev)\n预测生成时间为' + time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            return text
    except FileNotFoundError:
        cachedata = {}
    predict = json.loads(requests.get(predicturl, proxies=proxies).content)
    if predict['data']['eventId'] != eventid:
        now = int(time.time())
        cachedata['cachetime'] = now
        for i in range(0, 16):
            cachedata[predictline[i]] = 0
        with open('data/ssyc.yaml', 'w') as f:
            yaml.dump(cachedata, f)
        return '预测暂时不可用'
    cachedata['cachetime'] = int(predict['data']['ts'] / 1000)
    for i in range(0, 16):
        cachedata[predictline[i]] = predict['data'][str(predictline[i])]
    with open('data/ssyc.yaml', 'w') as f:
        yaml.dump(cachedata, f)

    for i in range(0, len(predictline) - 1):
        text = text + f'{predictline[i]}名预测：{cachedata[predictline[i]]}\n'
    timeArray = time.localtime(cachedata['cachetime'])
    text = text + '\n预测线来自xfl03(3-3.dev)\n预测生成时间为' + time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return text

def oldsk(targetid=None, targetrank=None, secret=False, server='jp', simple=False, qqnum='未知'):
    event = currentevent(server)
    eventid = event['id']
    if event['status'] == 'counting':
        return '活动分数统计中，不要着急哦！'
    if server == 'jp':
        url = apiurl
        masterdatadir = 'masterdata'
    elif server == 'en':
        url = enapiurl
        masterdatadir = '../enapi/masterdata'
    elif server == 'tw':
        url = twapiurl
        masterdatadir = '../twapi/masterdata'
    if targetid is not None:
        if not verifyid(targetid, server):
            bind = getqqbind(targetid, server)
            if bind is None:
                return '查不到捏'
            elif bind[2]:
                return '查不到捏，可能是不给看'
            else:
                targetid = bind[1]
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetUserId={targetid}', timeout=10)
    else:
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={targetrank}', timeout=10)
    ranking = json.loads(resp.content)
    try:
        name = ranking['rankings'][0]['name']
        rank = ranking['rankings'][0]['rank']
        score = ranking['rankings'][0]['score']
        userId = str(ranking['rankings'][0]['userId'])
        if not recordname(qqnum, userId, name):
            name = ''
    except IndexError:
        return '查不到数据捏，可能这期活动没打'
    try:
        TeamId = ranking['rankings'][0]['userCheerfulCarnival']['cheerfulCarnivalTeamId']
        with open(f'{masterdatadir}/cheerfulCarnivalTeams.json', 'r', encoding='utf-8') as f:
            Teams = json.load(f)
        with open('yamls/translate.yaml', encoding='utf-8') as f:
            trans = yaml.load(f, Loader=yaml.FullLoader)
        try:
            translate = f"({trans['cheerfulCarnivalTeams'][TeamId]})"
        except KeyError:
            translate = ''
        if server == 'tw':
            translate = ''
        for i in Teams:
            if i['id'] == TeamId:
                teamname = '队伍为' + i['teamName'] + translate + "，"
                break
    except KeyError:
        teamname = ''
    if not secret:
        userId = ' - ' + userId
    else:
        userId = ''
    msg = f'{name}{userId}\n{teamname}分数{score / 10000}W，排名{rank}'
    if simple:
        return msg
    for i in range(0, 31):
        if rank < rankline[i]:
            break
    if rank > 1:
        if rank == rankline[i - 1]:
            upper = rankline[i - 2]
        else:
            upper = rankline[i - 1]
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={upper}', timeout=10)
        ranking = json.loads(resp.content)
        linescore = ranking['rankings'][0]['score']
        deviation = (linescore - score) / 10000
        msg = msg + f'\n上一档排名{upper}的分数为{linescore/10000}W，相差{deviation}W'
    if rank < 100000:
        if rank == rankline[i]:
            lower = rankline[i + 1]
        else:
            lower = rankline[i]
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={lower}', timeout=10)
        ranking = json.loads(resp.content)
        linescore = ranking['rankings'][0]['score']
        deviation = (score - linescore) / 10000
        msg = msg + f'\n下一档排名{lower}的分数为{linescore/10000}W，相差{deviation}W'

    if event['status'] == 'going' and ispredict and server == 'jp':
        for i in range(0, 17):
            if rank < predictline[i]:
                break
        linescore = 0
        if rank > 100:
            upper = predictline[i - 1]
            linescore = ssyc(upper, eventid)
            if linescore != 0:
                msg = msg + f'\n\n{upper}名预测{linescore/10000}W'
        if rank < 100000:
            if rank == predictline[i]:
                lower = predictline[i + 1]
            else:
                lower = predictline[i]
            linescore = ssyc(lower, eventid)
            if linescore != 0:
                msg = msg + f'\n{lower}名预测{linescore/10000}W'
    if event['status'] == 'going':
        msg = msg + '\n活动还剩' + event['remain']
    return msg

def sk(targetid=None, targetrank=None, secret=False, server='jp', simple=False, qqnum='未知', ismain=False):
    event = currentevent(server)
    eventid = event['id']
    if event['status'] == 'counting':
        return '活动分数统计中，不要着急哦！'
    if server == 'jp':
        url = apiurl
        masterdatadir = 'masterdata'
    elif server == 'en':
        url = enapiurl
        masterdatadir = '../enapi/masterdata'
    elif server == 'tw':
        url = twapiurl
        masterdatadir = '../twapi/masterdata'
    elif server == 'kr':
        url = krapiurl
        masterdatadir = '../krapi/masterdata'
    if targetid is not None:
        if not verifyid(targetid, server):
            bind = getqqbind(targetid, server)
            if bind is None:
                return '查不到捏'
            elif bind[2]:
                return '查不到捏，可能是不给看'
            else:
                targetid = bind[1]
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetUserId={targetid}', timeout=10)
    else:
        resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={targetrank}', timeout=10)
    ranking = json.loads(resp.content)
    if ranking == {'status': 'maintenance_in'}:
        raise maintenanceIn
    try:
        name = ranking['rankings'][0]['name']
        rank = ranking['rankings'][0]['rank']
        score = ranking['rankings'][0]['score']
        userId = str(ranking['rankings'][0]['userId'])
        targetid = userId
        if not recordname(qqnum, userId, name):
            name = ''
    except IndexError:
        return '查不到数据捏，可能这期活动没打'
    try:
        TeamId = ranking['rankings'][0]['userCheerfulCarnival']['cheerfulCarnivalTeamId']
        with open(f'{masterdatadir}/cheerfulCarnivalTeams.json', 'r', encoding='utf-8') as f:
            Teams = json.load(f)
        with open('yamls/translate.yaml', encoding='utf-8') as f:
            trans = yaml.load(f, Loader=yaml.FullLoader)
        try:
            translate = f"({trans['cheerfulCarnivalTeams'][TeamId]})"
        except KeyError:
            translate = ''
        if server == 'tw' or server == 'kr':
            translate = ''
        for i in Teams:
            if i['id'] == TeamId:
                teamname = i['teamName'] + translate
                assetbundleName = i['assetbundleName']
                break
    except KeyError:
        teamname = ''
        assetbundleName = ''
    img = Image.new('RGB', (600, 600), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    if server == 'kr':
        font = ImageFont.truetype('fonts/SourceHanSansKR-Medium.otf', 25)
    else:
        font = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 25)
    if not secret:
        userId = ' - ' + userId
    else:
        userId = ''
    pos = 20
    draw.text((20, pos), name + userId, '#000000', font)
    pos += 35
    if teamname != '':
        if server != 'kr':
            team = Image.open('data/assets/sekai/assetbundle/resources/ondemand/event/'
                            f'{event["assetbundleName"]}/team_image/{assetbundleName}.png')
            team = team.resize((45, 45))
            r, g, b ,mask = team.split()
            img.paste(team, (20, 63), mask)
            draw.text((70, 65), teamname, '#000000', font)
        else:  # 韩服添加了5v5队伍，使得编号与日服不一致
            draw.text((20, 65), teamname, '#000000', font)
            font = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 25)
        pos += 50
    msg = f'{name}{userId}\n{teamname}分数{score / 10000}W，排名{rank}'
    font2 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 38)
    draw.text((20, pos), f'分数{score / 10000}W，排名{rank}', '#000000', font2)
    pos += 60
    if simple:
        return msg
    for i in range(0, 31):
        if rank < rankline[i]:
            break

    if rank > 1:
        if rank == rankline[i - 1]:
            upper = rankline[i - 2]
        else:
            upper = rankline[i - 1]
        try:
            resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={upper}', timeout=10)
            ranking = json.loads(resp.content)
            linescore = ranking['rankings'][0]['score']
        except IndexError:
            linescore = 0
        deviation = (linescore - score) / 10000
        draw.text((20, pos), f'{upper}名分数 {linescore/10000}W  ↑{deviation}W', '#000000', font)
        pos += 38
    if rank < 100000:
        if rank == rankline[i]:
            lower = rankline[i + 1]
        else:
            lower = rankline[i]
        try:
            resp = requests.get(f'{url}/user/%7Buser_id%7D/event/{eventid}/ranking?targetRank={lower}', timeout=10)
            ranking = json.loads(resp.content)
            linescore = ranking['rankings'][0]['score']
        except IndexError:
            linescore = 0
        deviation = (score - linescore) / 10000
        draw.text((20, pos), f'{lower}名分数 {linescore / 10000}W  ↓{deviation}W', '#000000', font)
        pos += 38
    pos += 10
    if event['status'] == 'going' and ispredict and server == 'jp':
        for i in range(0, 17):
            if rank < predictline[i]:
                break
        linescore = 0
        if rank > 100:
            upper = predictline[i - 1]
            linescore = ssyc(upper, eventid)
            if linescore != 0:
                draw.text((20, pos), f'{upper}名 预测{linescore/10000}W', '#000000', font)
                pos += 38
        if rank < 100000:
            if rank == predictline[i]:
                lower = predictline[i + 1]
            else:
                lower = predictline[i]
            linescore = ssyc(lower, eventid)
            if linescore != 0:
                draw.text((20, pos), f'{lower}名 预测{linescore/10000}W', '#000000', font)
                pos += 38
        pos += 10
        font3 = ImageFont.truetype('fonts/SourceHanSansCN-Medium.otf', 16)
        draw.text((400, pos - 5), '预测线来自33（3-3.dev）\n     Generated by Unibot', (150, 150, 150), font3)
    if event['status'] == 'going':
        draw.text((20, pos), '活动还剩' + event['remain'], '#000000', font)
        pos += 38
    img = img.crop((0, 0, 600, pos + 20))
    img.save(f"piccache/{targetid}sk.png")
    if ismain:
        return f"piccache/{targetid}sk.png"
    else:
        return f"[CQ:image,file={piccacheurl}{targetid}sk.png,cache=0]"

def teamcount(server='jp'):
    if server == 'jp':
        url = apiurl
        masterdatadir = 'masterdata'
    elif server == 'en':
        url = enapiurl
        masterdatadir = '../enapi/masterdata'
    elif server == 'tw':
        url = twapiurl
        masterdatadir = '../twapi/masterdata'
    elif server == 'kr':
        url = krapiurl
        masterdatadir = '../krapi/masterdata'
    event = currentevent(server)
    eventid = event['id']
    resp = requests.get(f'{url}/cheerful-carnival-team-count/{eventid}', timeout=10)
    data = json.loads(resp.content)

    with open(f'{masterdatadir}/cheerfulCarnivalTeams.json', 'r', encoding='utf-8') as f:
        Teams = json.load(f)
    with open('yamls/translate.yaml', encoding='utf-8') as f:
        trans = yaml.load(f, Loader=yaml.FullLoader)
    text = ''
    for Counts in data['cheerfulCarnivalTeamMemberCounts']:
        TeamId = Counts['cheerfulCarnivalTeamId']
        memberCount = Counts['memberCount']
        try:
            translate = f"({trans['cheerfulCarnivalTeams'][TeamId]})"
        except KeyError:
            translate = ''
        for i in Teams:
            if i['id'] == TeamId:
                text += i['teamName'] + translate + " " + str(memberCount)+ '人\n'
                break
    return text if text != '' else '没有5v5捏'

def getqqbind(qqnum, server):
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    if server == 'jp':
        mycursor.execute('SELECT * from bind where qqnum=%s', (qqnum,))
    elif server == 'tw':
        mycursor.execute('SELECT * from twbind where qqnum=%s', (qqnum,))
    elif server == 'en':
        mycursor.execute('SELECT * from enbind where qqnum=%s', (qqnum,))
    elif server == 'kr':
        mycursor.execute('SELECT * from krbind where qqnum=%s', (qqnum,))
    mycursor.close()
    mydb.close()
    data = mycursor.fetchone()
    try:
        return data[1:]
    except:
        return None

def getIdOwner(userid, server):
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    if server == 'jp':
        mycursor.execute('SELECT * from bind where userid=%s', (userid,))
    elif server == 'tw':
        mycursor.execute('SELECT * from twbind where userid=%s', (userid,))
    elif server == 'en':
        mycursor.execute('SELECT * from enbind where userid=%s', (userid,))
    elif server == 'kr':
        mycursor.execute('SELECT * from krbind where userid=%s', (userid,))
    mycursor.close()
    mydb.close()
    data = mycursor.fetchall()
    if data is not None:
        return ','.join([raw[1] for raw in data])
    return ''


def bindid(qqnum, userid, server):
    if not verifyid(userid, server):
        return '你这ID有问题啊'
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
        database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()

    if server == 'jp':
        sqlname = 'bind'
    elif server == 'tw':
        sqlname = 'twbind'
    elif server == 'en':
        sqlname = 'enbind'
    elif server == 'kr':
        sqlname = 'krbind'

    sql = f"insert into {sqlname} (qqnum, userid, isprivate) values (%s, %s, %s) " \
          f"on duplicate key update userid=%s"
    val = (str(qqnum), str(userid), 0, str(userid))
    mycursor.execute(sql, val)
    mydb.commit()
    mycursor.close()
    mydb.close()
    return "绑定成功！\n请不要以任何目的绑定挂哥账号，这可能导致你的qq被bot拉黑（如果你在正常绑定自己的账号请忽略该提示）"

def setprivate(qqnum, isprivate, server):
    if server == 'jp':
        server = ''
    mydb = pymysql.connect(host=host, port=port, user='pjsk', password=password,
                           database='pjsk', charset='utf8mb4')
    mycursor = mydb.cursor()
    mycursor.execute(f'UPDATE {server}bind SET isprivate=%s WHERE qqnum=%s', (isprivate, qqnum))
    mydb.commit()
    mycursor.close()
    mydb.close()
    return True
