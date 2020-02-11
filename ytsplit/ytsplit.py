#!/usr/bin/env python3
import youtube_dl
from pydub import AudioSegment
import os
import sys
import re
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse


def songtimes(timestring, structure_string=None, killindex=True, delimiter="\n"):
    if structure_string is not None:
        parsf = parse_structure(structure_string)
        structure_dicts = [parsf(i) for i in timestring.split(delimiter)]
        titles = [d[r"\t"] for d in structure_dicts]
        timestamps = [
            (d.get("\\h", 0), d.get("\\m", 0), d.get("\\s", 0)) for d in structure_dicts
        ]
    else:
        timesep = (
            r"(?:\d{1,2}:)?(?:\d{1,2}):(?:\d{1,2})"  # Regex to split at (hh:)mm:ss
        )
        titles = [s.strip(" \n") for s in re.split(timesep, timestring) if s != ""]
        timestamps = [
            re.split(":", m.group()) for m in re.finditer(timesep, timestring)
        ]
    timestamps = [
        sum(int(t) * 1000 * 60 ** s for s, t in enumerate(reversed(times)))
        for times in timestamps
    ]
    times = zip(timestamps, timestamps[1:] + [None])
    # titles = filter(lambda x: x != "", re.split(timesep, timestring)) # you can tell
    # that I had just learned about map and filter :D
    # titles = list(map(lambda s: s.strip(" \n"), titles))
    if killindex:
        titles = [re.sub(r"\d{1,2}(\. | - |\))", "", title) for title in titles]
    times = [t for n, t in enumerate(times) if titles[n] != "!junk!"]
    titles = [t for n, t in enumerate(titles) if t != "!junk!"]
    return times, titles


structure_keys = {
    r"\h",  # hours
    r"\m",  # minutes
    r"\s",  # seconds
    r"\t",  # title
    r"\n",  # number
}

replace_rules = {
    r"\h": r"\d{1,3}",
    r"\m": r"\d{1,3}",
    r"\s": r"\d{1,3}",
    r"\t": r".*",
    r"\n": r"\d{1,3}",
}

key_pattern = "(" + "|".join(map(re.escape, structure_keys)) + ")"


def ids_positions(ipattern):
    return [i.span() for i in re.finditer(key_pattern, ipattern)]


def gap_positions(positions, start, end):
    inds = [(positions[i][1], positions[i + 1][0]) for i in range(len(positions) - 1)]
    if positions[0][0] > start:
        inds = [(start, positions[0][0])] + inds
    if positions[-1][1] < end:
        inds = inds + [(positions[-1][1], end)]
    return inds


def slice_with_list(inp, slist):
    return [inp[slice(*pos)] for pos in slist]


def parse_structure(ipattern):
    r"""
        Creates a function which gets a Title and timestamp from a string,
        given an input of a pattern like these:
        \n. \m:\s - \t$
        or
        \n) \h - \m - \s | \t$
        or just
        \t \m:\s$
    """
    id_pos = ids_positions(ipattern)
    gap_pos = gap_positions(id_pos, 0, len(ipattern))
    id_patterns = slice_with_list(ipattern, id_pos)
    gap_patterns = slice_with_list(ipattern, gap_pos)
    id_patterns_escaped = (r"({})".format(replace_rules[id_i]) for id_i in id_patterns)
    gap_patterns_escaped = (re.escape(s) for s in gap_patterns)
    pattern_number = len(id_patterns) + len(gap_patterns)
    ordered_patterns = []
    order = 0 if id_pos[0][0] == 0 else 1
    for i in range(pattern_number):
        if (i + order) % 2 == 0:
            ordered_patterns.append(next(id_patterns_escaped))
        else:
            ordered_patterns.append(next(gap_patterns_escaped))
    match_pattern = "".join(ordered_patterns)

    def sparser(istring):
        match = re.match(match_pattern, istring).groups()
        matchdict = {p: m for p, m in zip(id_patterns, match)}
        return matchdict

    return sparser


def splitytsong(
    mseclist,
    namelist,
    url,
    directory,
    artist="unknown",
    album="unknown",
    etags={},
    ftime=False,
):
    cwd = str(Path.cwd())
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
        foldername = directory + "/{}/{}/".format(artist, album)
        song = AudioSegment.from_mp3("splitsong.mp3")
        os.chdir(cwd)
    try:
        os.makedirs(foldername)
    except FileExistsError:
        pass
    tags = {"artist": artist, "album": album}
    tags.update(etags)
    for i, (time, title) in enumerate(zip(mseclist, namelist)):
        tags.update({"title": title, "track": str(i + 1)})
        song[time[0] : time[1]].export(
            foldername + str(i + 1) + ". " + title + ".mp3", format="mp3", tags=tags
        )


def main():

    parser = argparse.ArgumentParser(
        description="Downloads Youtube albums with YoutubeDL"
    )

    parser.add_argument("url", default=None, nargs="?", help="Url of the track")

    parser.add_argument(
        "-d", "--directory", default=str(Path.cwd()), help="Output directory"
    )
    parser.add_argument(
        "-i", "--interpret", default="Unkown", help="Interpret/Artist tag for the Album"
    )
    parser.add_argument("-a", "--album", default="Unkown", help="Album name")
    parser.add_argument("-f", "--file", default=None, help="Tracklist file")
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""Only gives times and songtitle from tracklist.
        Used to check for errors in parsing the tracklist""",
    )
    parser.add_argument(
        "-l",
        "--tracklist",
        default=None,
        help="Tracklist like popular on youtube. If not provided uses stdin",
    )
    parser.add_argument(
        "-x",
        "--delimiter",
        default="\n",
        help=r"Delimiter of the different tracks in the tracklist (defaults to newline)",
    )
    parser.add_argument(
        "-s",
        "--structure",
        default=None,
        help=r"""String that gives the structure of the tracklist
        It can have following identifiers:

        \h : hours
        \m : minutes
        \s : seconds
        \t : trackname
        \n : tracknumber

        Every identifier needs to be separated from
        the next one by a constant delimiter""",
    )

    args = parser.parse_args()

    if args.tracklist is None and args.file is None:
        tracklist = str.strip(sys.stdin.read())
        if not tracklist:
            print("No tracklist provided.")
            return 1
    elif args.file:
        with open(args.file, "r") as tlist:
            tracklist = tlist.read().strip()
    else:
        tracklist = args.tracklist

    mseclist, namelist = songtimes(
        tracklist, structure_string=args.structure, delimiter=args.delimiter
    )

    if args.test:
        print("\n".join(namelist))
        return 0
    elif args.url is None:
        print("Please provide url to download.")

    splitytsong(
        mseclist,
        namelist,
        args.url,
        str(Path(args.directory)),
        artist=args.interpret,
        album=args.album,
    )
    return 0
