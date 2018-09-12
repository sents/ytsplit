#!/usr/bin/env python3
import youtube_dl
from pydub import AudioSegment
import os,sys,re
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse



def songtimes(sstring,killindex=True):
    #Gets a Tracklist and tries to find the time and title for every Track
    titles=map(str.strip,(filter(lambda x:x!='',re.split(r"(?:\d{1,2}:)?(?:\d+):(?:\d\d)",sstring))))
    if killindex:
        titles=[re.sub(r"\d{1,2}(\. | - |\))",'',title) for title in titles]
    titles=[re.sub(r"(^-|-$)",'',title) for title in titles]
    titles=[re.sub(r"/",'-',title) for title in titles]
    titles=list(map(str.strip,titles))
    timegrab=re.findall(r"(\d{1,2}:)?(\d+):(\d\d)",sstring)
    times=[[int(''.join(filter(str.isdigit,i if i!='' else '0')))*1000*60**t for (t,i) in enumerate(reversed(q))] for q in timegrab]
    return list(map(sum,times)),titles

def splitytsong(tlist,url,artist='unknown',album='unknown',etags={},ftime=False,):
    cwd=str(Path.cwd())
    ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'}],
    'outtmpl':'splitsong.%(ext)s'}
    with TemporaryDirectory() as tmp:
        os.chdir(tmp)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        foldername=str(Path.home())+'/Musik/{} - {}/'.format(artist,album)
        mseclist,namelist=songtimes(tlist)
        mseclist.append(None)
        song=AudioSegment.from_mp3('splitsong.mp3')
        os.chdir(cwd)
    try:
        os.makedirs(foldername)
    except FileExistsError:
        pass
    tags={'artist':artist,'album':album}
    tags.update(etags)
    for i in range(len(namelist)):
        tags.update({'title':namelist[i],'track':str(i+1)})
        song[mseclist[i]:mseclist[i+1]].export(foldername+str(i+1)+'. '+namelist[i]+'.mp3',format='mp3',tags=tags)

def main():

    parser = argparse.ArgumentParser(description = "Downloads Youtube albums with YoutubeDL")

    parser.add_argument("tracklist", help="Tracklist like popular on youtube.com")

    parser.add_argument("-d", "--directory", default=str(Path.home())+'/Musik/', help="Folder in which to put the Tracks")

    parser.add_argument("-i", "--interpret", default="Unkown", help="Interpret/Artist tag for the Album")
    
    parser.add_argument("-a", "--album", default="Unkown", help="Album name")
    
    
    args = parser.parse_args() 

    tracklist=str.strip(sys.stdin.read())

    splitytsong(tracklist,*(sys.argv[1:]))
