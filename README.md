# Itube_tagger
@author: Tibor Teske
Itube tagger is a program i wrote for myself mainly, but that is also refitablle for anyone who is interested enough to change the code.


## What this does:

This program, to put it very simply, takes your "Libary.xml" generated inside itunes, and your Youtube History File, and filters them for possible songs, sorting them in one big table, before processing every single one and aggregating them. 

For Itunes it merely deciphers the complicated libary.xml and inserts them into the final DataFrame

For Youtube it splits into Youtube and Youtube Music.

With youtube music entries, every entry gets cleaned and requested by the Spotify API. Then if there is a corresponding song found, we take the tags spotify has available and supply it to the song, before adding it to your final table. If we dont find anything, we simply insert Title and Artist

With youtube videos, as they can be either Music videos or unrelated ones, we first check if any occourence happens in Youtube music or Itunes of the song and add in that case. In any other case we also search the videotitle + channelname via the Spotify API, and check for returns (But after filtering common words and running a regex throwing out unnecessary baggage). On a positive return we tag the video and insert it, on a negative we do nothing. 

Afterwards this file is safed and can then be ooaded inside the (still WIP) powerBI dashboard to view your personal favourite genres, BPM, Artist etc.

## How it works:

1) Export your Itunes libary
2) Download your Youtube search history via googles services as a .json
3) Define your Paths inside the "youtube_music_extraction.py"
4) Create a Spotify developer account
    4.1) Afterwards create a custom application
    4.2) Generate a client Key and client secret
    4.3) Insert both at the marked spaces in the py
5) Insert the name of your .json inside the marked function
6) Run the Program
7) Wait. Wait a long time, depending on the size of your library. Its gonna give feedback every 1500 songs, so use that to check if the program still runs.
8) Take the generated "music_list.xlsx"
9) open the "itubetagger.pbix"
10) Open the Data transformation window
11) Navigate the sources to your local "music_list.xlsx"
12) click "save and apply changes"
13) Done

## Troubleshooting:

When you get frequent timeouts from the spotify API, its usually on them. Try again.


## Why does it take so long:

The spotify API python overlay (and spotify in general) does not accept lists of requests, hence why every single Video you have ever watched will be parsed to them if it isnt falling under the filters i built in

## Whats planned:

A rating system for Songs, to actually
