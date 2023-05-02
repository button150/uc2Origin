import os
import json
import re
import urllib3
import requests
from shutil import copyfile
from PIL import Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, USLT ,TRCK
from mutagen.flac import FLAC, Picture
from itertools import count

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {'User-agent': 'Mozilla/5.0'}

#Edit the file path yourself
INPUTPATH = 'C:\\'
OUTPUTPATH = 'C:\\'

def getInfoFromWeb(id):
        dic = {}
        url = 'http://music.163.com/api/song/detail/?ids=[' + id + ']'
        res = requests.get(url, headers=headers).json()
        info = res['songs'][0]
        dic['artist'] = [info['artists'][0]['name']]
        dic['title'] = [info['name']]
        dic['trno'] = str(info['no'])
        dic['cover'] = info['album']['picUrl']
        dic['album'] = [info['album']['name']]
        return dic

def getLyric(id):
        url = 'http://music.163.com/api/song/lyric?id=' + id + '&lv=1&tv=-1'
        lrc = ''
        try:
            lyric = requests.get(url, headers=headers).json()
            lrc = lyric['lrc']['lyric']
            tlrc = lyric['tlyric']['lyric']
            dic = {}
            for i in lrc.splitlines():
                a = i.replace('[', ']').strip().split("]")
                dic[a[1].strip()+' '] = a[-1].strip()
            tdic = {}
            for m in tlrc.splitlines():
                n = m.replace('[', ']').strip().split(']')
                tdic[n[1].strip()] = n[-1].strip()
            dicCopy = dic.copy()
            dicCopy.update(tdic)
            lines = []
            for k, v in sorted(dicCopy.items(), key=lambda item: item[0]):
                lines.append("[%s]%s" % (k.strip(), v))
            lrc = "\n".join(lines)
        except Exception as e:
            pass
        return lrc

def mkdir(npath) :
    folder = os.path.exists(npath)
    if not folder:
        os.makedirs(npath)

counto = 0
list = os.listdir(INPUTPATH)
for fname in list:
    if fname.split('.')[-1] != 'uc':
        continue
    id = fname.split('-')[0]
    
    with open(INPUTPATH + fname, 'rb') as fi:
        b = fi.read()
    
    with open(INPUTPATH + re.sub(r'(\.uc)', '.info', fname)) as fi:
        mtype = json.loads(fi.read())['format']
 
    info = getInfoFromWeb(id)
    lyr = getLyric(id)
    art0 = str(info['artist']).replace("['",'').replace("']",'')
    art1 = str(info['album']).replace("['",'').replace("']",'')
    art2 = str(info['title']).replace("['",'').replace("']",'')
    art10 = art1
    for i in '\/:*?"<>|':
            art10 = art10.replace(i, '_')
    
    npath =  OUTPUTPATH + '\\' + art0 + ' - ' + art10 + '\\'
    mkdir(npath)

    ppath = npath + art0 + ' - ' + art1 + '.png'

    if os.path.exists(ppath) != True:
        cvdata = requests.get(info['cover'], stream=True,headers=headers).content
        with open(ppath,'wb') as wp:
            wp.write(cvdata)

    try :
        psize = os.path.getsize(ppath)
        if psize > 500000 :
            hppath = npath + art0 + ' - ' + art1 + '_Huge' +'.png'
            copyfile(ppath, hppath)
            img = Image.open(ppath)
            x = int(psize / 5000000)
            width = int((img.size[0]) / x)
            height = int((img.size[1]) / x)
            imgout = img.resize((width, height))
            imgout.save(ppath, 'png')
            print('Cover Size too huge ~ resize')
    except :
        print('An error occurred while resize Cover img .')

    if id :
        try :
            with open(npath + art0 + ' - ' + art2 + '_' + id + '.' + mtype, 'wb') as fo:
                for i in b:
                    fo.write((i ^ 0xa3).to_bytes(length=1, byteorder='little'))
            print(art0 + ' - ' + art2 + '_' + id + '.' + mtype)
        except:
            print('An error occurred while generating the file .')

    if mtype == 'mp3' :
        audio = ID3(npath + art0 + ' - ' + art2 + '_' + id + '.mp3')
        audio.add(TPE1(encoding=3, text=info['artist']))
        audio.add(TIT2(encoding=3, text=info['title']))
        audio.add(TALB(encoding=3, text=info['album']))
        audio.add(TRCK(encoding=3, text=info['trno']))
        audio.add(USLT(encoding=3, lang="eng", desc="", text=lyr))
        audio.add(APIC(encoding=3,
                        mime='image/png',
                        type=3, 
                        desc=u'Cover',
                        data=open(ppath ,'rb').read()
                        ) )
        audio.save()
        counto +=1
    elif mtype == 'flac' :
        audio = FLAC(npath + art0 + ' - ' + art2 + '_' + id + '.flac')
        audio['artist'] = info['artist']
        audio['title'] = info['title']
        audio['album'] = info['album']
        audio['tracknumber'] = info['trno']
        audio['lyrics'] = lyr        
        picture = Picture()
        picture.type = 3 
        picture.mime = "image/png"
        picture.desc = "front cover"
        with open(ppath,'rb') as rp:
             picture.data = rp.read()
        audio.add_picture(picture)
        audio.save()
        counto +=1
    else :
         print('null')
print('sucess: ' + str(counto))

   

    
