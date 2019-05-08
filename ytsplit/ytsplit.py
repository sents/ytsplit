#!/usr/bin/env python3
import youtube_dl
from pydub import AudioSegment
import os, sys, re
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse


def songtimes(timestring, structure_string=None, killindex=True):
    if structure_string is not None:
        timesep, strips = parse_structure(structure_string)
    else:
        timesep = (
            r"(?:\d{1,2}:)?(?:\d{1,2}):(?:\d{1,2})"
        )  # Regex to split at (hh:)mm:ss
    timestamps = [re.split(":", m.group()) for m in re.finditer(timesep, timestring)]
    timestamps = [
        sum(int(t) * 1000 * 60 ** s for s, t in enumerate(reversed(times)))
        for times in timestamps
    ]
    times = zip(timestamps, timestamps[1:] + [None])
    titles = filter(lambda x: x != "", re.split(timesep, timestring))
    titles = list(map(lambda s: s.strip(" \n"), titles))
    if killindex:
        titles = [re.sub(r"\d{1,2}(\. | - |\))", "", title) for title in titles]
    times = [t for n, t in enumerate(times) if titles[n] != "!junk!"]
    titles = [t for n, t in enumerate(titles) if t != "!junk!"]
    return times, titles


def splitytsong(
    tlist, url, directory, artist="unknown", album="unknown", etags={}, ftime=False
):
    cwd = str(Path.cwd())
    mseclist, namelist = songtimes(tlist)
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": "splitsong.%(ext)s",
    }
    with TemporaryDirectory() as tmp:
        os.chdir(tmp)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        foldername = directory + "/{} - {}/".format(artist, album)
        song = AudioSegment.from_mp3("splitsong.mp3")
        os.chdir(cwd)
    try:
        os.makedirs(foldername)
    except FileExistsError:
        pass
    tags = {"artist": artist, "album": album}
    tags.update(etags)
    for i, (time, title) in enumerate(zip(mseclist, namelist)):
        tags.update({"title": name, "track": str(i + 1)})
        song[time[0] : time[1]].export(
            foldername + str(i + 1) + ". " + name + ".mp3", format="mp3", tags=tags
        )


def main():

    parser = argparse.ArgumentParser(
        description="Downloads Youtube albums with YoutubeDL"
    )

    parser.add_argument("url", help="Url of the track")

    parser.add_argument(
        "-d", "--directory", default=str(Path.cwd()), help="Output directory"
    )
    parser.add_argument(
        "-i", "--interpret", default="Unkown", help="Interpret/Artist tag for the Album"
    )
    parser.add_argument("-a", "--album", default="Unkown", help="Album name")
    parser.add_argument("-f", "--file", default=None, help="Tracklist file")
    parser.add_argument(
        "-l",
        "--tracklist",
        default=None,
        help="Tracklist like popular on youtube. If not provided uses stdin",
    )

    args = parser.parse_args()
    if args.tracklist is None and args.file is None:
        tracklist = str.strip(sys.stdin.read())
    elif args.file:
        with open(args.file, "r") as tlist:
            tracklist = tlist.read().strip()
    else:
        tracklist = args.tracklist

    splitytsong(
        tracklist,
        args.url,
        str(Path(args.directory)),
        artist=args.interpret,
        album=args.album,
    )
    return 0
