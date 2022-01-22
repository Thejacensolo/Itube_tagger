# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 23:05:32 2021

@author: Tibor
"""

import pandas as pd
import numpy as np
from xml.etree import ElementTree as ET
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials



def df_creation(PATHOUT):
    
    tree = ET.parse(PATHOUT+'Mediathek.xml')
    root = tree.getroot()
    
    main_dict=root.findall('dict')
    for item in list(main_dict[0]):    
        if item.tag=="dict":
            tracks_dict=item
            break
    tracklist=list(tracks_dict.findall('dict'))
    
    music=[] #All music elements
    
    
    for item in tracklist:
        x=list(item)
        for i in range(len(x)):
            if x[i].text =="Track Type" and x[i+1].text=="File":
                
                music.append(list(item))
    
    cols=[]
    for i in range(len(music)):
        for j in range(len(music[i])):
            if music[i][j].tag=="key":
                cols.append(music[i][j].text)
    cols = set(cols)
    
    #df=pd.DataFrame(columns=cols)
    songlist = []
    tagdf = pd.DataFrame(columns=["comb_key", "tag"])
    for i in range(len(music)):
        dict1={'Album':np.nan, 'Album Artist':np.nan, 'Album Rating':np.nan, 'Album Rating Computed':np.nan,
               'Artist':np.nan, 'BPM':np.nan, 'Bit Rate':np.nan, 'Comments':np.nan, 'Compilation':np.nan,
               'Composer':np.nan, 'Date Added':np.nan, 'Date Modified':np.nan, 'Disabled':np.nan,
               'Explicit':np.nan, 'Genre':np.nan, 'Grouping':np.nan,
               'Loved':np.nan,
               'Name':np.nan,  'Persistent ID':np.nan, 'Play Count':np.nan, 'Play Date':np.nan,
               'Purchased':np.nan, 'Rating':np.nan, 'Rating Computed':np.nan,
               'Release Date':np.nan,  'Skip Count':np.nan, 'Skip Date':np.nan,
                'Stop Time':np.nan, 'Total Time':np.nan, 'Track Count':np.nan,
               'Track ID':np.nan, 'Track Number':np.nan, 
               'Year':np.nan, 'comb_key':np.nan}
        for j in range(len(music[i])):
            if music[i][j].tag == "key":
                if music[i][j].text in dict1.keys():
                    
                    dict1[music[i][j].text] = music[i][j+1].text
        
        # Create Combination key

        dict1['comb_key'] = '_'.join((str(dict1['Artist']),str(dict1['Name']))) 

        
        try:
            if "last.fm" in dict1["Comments"]:
                try:
                    last_fm_list = re.search("last.fm:.*;", dict1["Comments"])
                    
                    list_of_last_fm = last_fm_list.group().split(",")
                    
                    for tag in list_of_last_fm:
                        
                        single_tag = re.search("\{(.*?)\}",tag)
                        tagdict = {"comb_key": dict1["comb_key"], "tag": single_tag.group()[1:-1]}
                        tagdf = tagdf.append(tagdict,ignore_index=True)
                        
                except AttributeError:
                    pass
        except TypeError:
            pass
        songlist.append(dict1)
            
    
    itunes_song_DF = pd.DataFrame(songlist)
    
    artist_list = itunes_song_DF["Artist"].to_list()
    song_list = itunes_song_DF["Name"].to_list()
    return itunes_song_DF, tagdf, artist_list, song_list


 
def create_youtube_music_DF(PATHOUT):
    youtube_history_df = pd.read_json(PATHOUT+"Wiedergabeverlauf.json")

    # Loading and formatting the youtube music history
    youtube_music_history_df = youtube_history_df[youtube_history_df["header"]=="YouTube Music"]
    youtube_music_history_df.loc[:,"time"] = youtube_music_history_df.loc[:, "time"].str[:10]
    youtube_music_history_df.loc[:,"title"] = youtube_music_history_df.loc[:,"title"].str[:-10]
    youtube_music_history_df = youtube_music_history_df.loc[:,["title","time","subtitles","titleUrl"]]
    youtube_music_history_df['index'] = youtube_music_history_df.index
    youtube_music_history_df['youtube'] = 'youtube_music'

    # Extract the artist
    artist = youtube_music_history_df[["subtitles","index"]].values.tolist()
    artist_list = []
    for entry in artist:
        entrydict = {"name": "", "sub_url": "", "list_ind":""}
        try:
            if entry[0][0]["name"].endswith(" - Topic"):
                entrydict["name"] = entry[0][0]["name"][:-8]
            else:
                entrydict["name"] = entry[0][0]["name"]
            entrydict["url"] = entry[0][0]["url"]
            entrydict["list_ind"] = entry[1]
        except:
            pass
        artist_list.append(entrydict)

    artist_df = pd.DataFrame(artist_list)

    youtube_music_history_df_fin = pd.merge(youtube_music_history_df, artist_df, left_on = "index", right_on="list_ind",how="left") 

    youtube_music_history_df_fin = youtube_music_history_df_fin.drop(columns=["subtitles", "list_ind"])
 


    # Aquire a Youtube tagged DF via spotify
    print("sort youtube music files")


    youtube_music_history_df_fin_dict = youtube_music_history_df_fin.apply(get_spotify_tags,axis=1)
    
    music_list_dict = []
    for k in youtube_music_history_df_fin_dict.keys():
        try:

            music_list_dict.append(youtube_music_history_df_fin_dict[k])
        except TypeError:
            pass
    music_list_dict =  filter(lambda x: x!=None, music_list_dict)
    youtube_music_history_df_fin = pd.DataFrame(music_list_dict)
    artist_list = youtube_music_history_df_fin["Artist"].to_list()
    song_list = youtube_music_history_df_fin["Name"].to_list()    

    return youtube_music_history_df_fin, artist_list, song_list


def add_youtube_views(PATHOUT, youtube_music_DF):
    youtube_history_df = pd.read_json(PATHOUT+"Wiedergabeverlauf.json")
    youtube_df = youtube_history_df[youtube_history_df["header"]=="YouTube"]
    youtube_df.loc[:,"time"] = youtube_df.loc[:, "time"].str[:10]
    youtube_df.loc[:,"title"] = youtube_df.loc[:,"title"].str[:-10]
    youtube_df = youtube_df.loc[:,["title","time","subtitles","titleUrl"]]
    youtube_df['index'] = youtube_df.index    
    youtube_df['youtube'] = "youtube"


    artist = youtube_df[["subtitles","index"]].values.tolist()
    artist_list = []
    for entry in artist:
        entrydict = {"name": "", "sub_url": "", "list_ind":""}
        try:
            if entry[0][0]["name"].endswith(" - Topic"):
                entrydict["name"] = entry[0][0]["name"][:-8]
            else:
                entrydict["name"] = entry[0][0]["name"]
            entrydict["url"] = entry[0][0]["url"]
            entrydict["list_ind"] = entry[1]
        except:
            pass
        artist_list.append(entrydict)

    artist_df = pd.DataFrame(artist_list)
    youtube_df = pd.merge(youtube_df, artist_df, left_on = "index", right_on="list_ind",how="left") 
    youtube_df = youtube_df.drop(columns=["subtitles","list_ind"])
    youtube_df['comb_key'] = youtube_df.apply(lambda x:'%s_%s' % (x['name'],x['title']),axis=1)
    youtube_df = youtube_df.dropna(subset=['name'])
     
    
    # Aquire a Youtube tagged   spotify
    print("sort youtube files")

    sorted_youtube_dict  = youtube_df.apply(get_spotify_tags,axis=1)

    music_list_dict = []
    for k in sorted_youtube_dict.keys():
        try:

            music_list_dict.append(sorted_youtube_dict[k])
        except TypeError:
            pass
        
    music_list_dict =  filter(lambda x: x!=None, music_list_dict)
    
    youtube_gotten_df = pd.DataFrame(music_list_dict)
    


    # Combine all in list

    youtube_music_DF = youtube_music_DF.append(youtube_gotten_df)
    return youtube_music_DF

def itunes_youtube_comb(youtube_music_DF, itunes_music_df):

    itunes_dict  = itunes_music_df.to_dict('records')
    youtube_dict = youtube_music_DF.to_dict('records')
    
    #Iterriere durch alle reihen durch. scheiß laufzeit lol
    
    for itunesrow in itunes_dict:
        for youtuberow in youtube_dict:
            if str(itunesrow["Artist"]) in str(youtuberow["Artist"]):
                if str(itunesrow["Name"]) in str(youtuberow["Name"]):
                    if "mix" in str(youtuberow["Name"]):
                        pass
                    else:
                        try:
                        
                         itunesrow["Play Count"] = int(itunesrow["Play Count"]) + youtuberow["Play Count"]
                         youtuberow["comb_key"] = np.nan
                         
                        except ValueError:
                            itunesrow["Play Count"] = youtuberow["Play Count"]
                            youtuberow["comb_key"] = np.nan
                            
    itunes_music_df = pd.DataFrame(itunes_dict)
    youtube_music_DF = pd.DataFrame(youtube_dict)
    youtube_music_DF = youtube_music_DF.dropna(subset=['comb_key'])    
                    
    
    return itunes_music_df, youtube_music_DF
    

def get_spotify_tags(row):

    # create final dict for the track
    # Search track

    try:
        ### Get Spotify inf
        
        client_credentials_manager = SpotifyClientCredentials(client_id='<INSERT YOUR CLIENT ID>',client_secret='<INSERT YOUR CLIENT SECRET NUMBER>')
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        
        #cleaning and checking if Artist/Song appears
        row["name"] = str(row["name"])
        row["title"] = str(row["title"])
        
        if "https://www.youtube.com/watch?" in row["title"]:
            pass 
        elif "Ein Video angesehen, das entfernt wurde" in row["title"]:
            pass
        else:
            if "-" in row["title"]:
                titlestring = row["title"].split("-")
                result = sp.search("artist:"+ titlestring[0] + " +" + "track:" + titlestring[-1], type="track")
    
            else:
                try:
                    title_string = string_cleaning(row["title"])
                    artist_string = string_cleaning(row["name"])
                    
                    
                    
                    
                    artist_name_check = title_string.split(" ") 
                    # Manual filter
                    for word in artist_name_check:
                        if word in ARTIST_LIST:
                            row["name"] = word
                        else:
                            artist_string_list = artist_string.split(" ")
                            if "OFFICIAL" in artist_string_list:
                                artist_string_list.remove("OFFICIAL")
                            elif "official" in artist_string_list:
                                artist_string_list.remove("official")
                            row["name"] = ' '.join(artist_string)
                        if word in SONG_LIST:
                            row["title"] = word
                            
                except TypeError:
                    pass
                
                result = sp.search("artist:"+ str(row["name"]) + " +" + "track:" + str(row["title"]), type="track")
            
            if len(result["tracks"]["items"]) != 0:
                track_uri = result["tracks"]["items"][0]["uri"]
                try:
                # create extractable information
                    audio_analysis = sp.audio_analysis(track_uri)
                    BPM = round(audio_analysis["track"]["tempo"],0)
                except:
                    BPM = np.nan
                track_dict = sp.track(track_uri)
                album_dict = sp.album(track_dict["album"]["uri"])
                
                artist_dict = sp.artist(album_dict["artists"][0]["uri"])
                
                genre_combination = artist_dict["genres"] + album_dict["genres"]
                genre_list = []
                [genre_list.append(x) for x in genre_combination if x not in genre_list]
                
                #fill in
                youtube_sup_dict = {'Album':album_dict["name"], 
                                    'Album Artist':album_dict["artists"][0]["name"], 
                                    'Album Rating':album_dict["popularity"], 
                                    'Album Rating Computed':np.nan,
                                    'Artist':track_dict["artists"][0]["name"], 
                                    'BPM':BPM, 
                                    'Bit Rate':np.nan, 
                                    'Comments':np.nan, 
                                    'Compilation':np.nan,
                                    'Composer':np.nan, 
                                    'Date Added':row["time"], 
                                    'Date Modified':np.nan, 
                                    'Disabled':np.nan,
                                    'Explicit':track_dict["explicit"], 
                                    'Genre': genre_list,
                                    'Grouping':np.nan,
                                    'Loved':np.nan,
                                    'Name':track_dict["name"],  
                                    'Persistent ID':np.nan, 
                                    'Play Date':np.nan,
                                    'Purchased':np.nan, 
                                    'Rating':np.nan, 
                                    'Rating Computed':track_dict["popularity"],
                                    'Release Date':album_dict["release_date"],  
                                    'Skip Count':np.nan, 
                                    'Skip Date':np.nan,
                                    'Stop Time':np.nan, 
                                    'Total Time':int(str(track_dict["duration_ms"])[:3]), 
                                    'Track Count':np.nan,
                                    'Track ID':np.nan, 
                                    'Track Number':track_dict["track_number"], 
                                    'Year':np.nan, 
                                    'comb_key':"_".join((track_dict["artists"][0]["name"],track_dict["name"]))} 
                if row["index"] % 1500 == 0:
                    print("1500 completed")
                
                return(youtube_sup_dict)
            else:
                if row["youtube"] == "youtube_music":
                    youtube_sup_dict = {'Album':np.nan, 
                                        'Album Artist':np.nan, 
                                        'Album Rating':np.nan, 
                                        'Album Rating Computed':np.nan,
                                        'Artist':row["name"], 
                                        'BPM':np.nan, 
                                        'Bit Rate':np.nan, 
                                        'Comments':np.nan, 
                                        'Compilation':np.nan,
                                        'Composer':np.nan, 
                                        'Date Added':row["time"], 
                                        'Date Modified':np.nan, 
                                        'Disabled':np.nan,
                                        'Explicit':np.nan, 
                                        'Genre': np.nan,
                                        'Grouping':np.nan,
                                        'Loved':np.nan,
                                        'Name':row["title"],  
                                        'Persistent ID':np.nan, 
                                        'Play Date':np.nan,
                                        'Purchased':np.nan, 
                                        'Rating':np.nan, 
                                        'Rating Computed':np.nan,
                                        'Release Date':np.nan,  
                                        'Skip Count':np.nan, 
                                        'Skip Date':np.nan,
                                        'Stop Time':np.nan, 
                                        'Total Time':np.nan, 
                                        'Track Count':np.nan,
                                        'Track ID':np.nan, 
                                        'Track Number':np.nan, 
                                        'Year':np.nan, 
                                        'comb_key':"_".join((row["name"],row["title"]))} 
                    if row["index"] % 1500 == 0:
                        print(row["index"], " completed")
                    return(youtube_sup_dict)
                else:
                    pass
            
    except AttributeError as e:
        print("error: ", e)

def string_cleaning(title):
    list_match = re.findall(r"[\s\w]|[\s\w]+]", title, re.UNICODE)
    
    
    return ''.join(list_match)


PATHITUNES = "<PATH TO YOUR ITUNES LIBARY.XML>"
PATHOUT = "<PATH TO YOUR YOUTUBE HISTORY>"



### READ IN

## Itunes
print("Processing Itunes")
itunes_music_df, lastFM_tag_df, ARTIST_LIST, SONG_LIST = df_creation(PATHOUT)



## Youtube Music
print("processing youtube music")
youtube_music_DF, ARTIST_LIST1, SONG_LIST1  = create_youtube_music_DF(PATHOUT)

ARTIST_LIST = ARTIST_LIST + ARTIST_LIST1
ARTIST_LIST = list(dict.fromkeys(ARTIST_LIST))

SONG_LIST = SONG_LIST + SONG_LIST1
SONG_LIST = list(dict.fromkeys(SONG_LIST))
print("processing youtube")
youtube_music_DF = add_youtube_views(PATHOUT, youtube_music_DF)


play_count_youtube_music_title = youtube_music_DF.groupby(['comb_key']).size()
play_count_youtube_music_title.name = 'Play Count'

youtube_music_DF = youtube_music_DF.drop_duplicates(subset=['comb_key'])
youtube_music_DF = pd.merge(youtube_music_DF, play_count_youtube_music_title, on='comb_key')



## PROCESS
print("Insert youtube music and youtube duplicates into the Itunes list")
itunes_changed_df, youtube_music_DF_changed = itunes_youtube_comb(youtube_music_DF, itunes_music_df)

print("add the 2 Dataframes")
final_df = youtube_music_DF.append(itunes_music_df)

# Writing to Script
writer = pd.ExcelWriter(PATHOUT+"music_list.xlsx", engine='xlsxwriter')

final_df.to_excel(writer, sheet_name='MusikDB',index=False)

lastFM_tag_df.to_excel(writer, sheet_name='Last FM tags',index=False)

writer.close()