import functions_framework
import requests
from bs4 import BeautifulSoup
from bs4 import element

#Helps parse miscellaneous tags <i>, </br>, etc,.
def _lyricsHelper(html, lyrics_list):
    for tag in html.childGenerator():
        if type(tag) == element.NavigableString:
            _handleLyricAppend(lyrics_list, tag.text.strip())
        elif tag.name == 'br' and lyrics_list[len(lyrics_list) - 1] != '':
            lyrics_list.append('')
        elif html.name == 'a':
            _lyricsHelper(tag, lyrics_list)

#Reads the HTML for lyrics dividers (if they exist) and appends the lyrics line by line to a list
def _getLyricsFromHTML(html):
    lyrics = html.findAll("div", {"data-lyrics-container" : "true"})
    lyrics_list = ['']
    for segment in lyrics:
        for a in segment.childGenerator():
            lyric = None
            if type(a) == element.NavigableString:
                lyric = a.strip()
                _handleLyricAppend(lyrics_list, lyric)
            else:
                _lyricsHelper(a, lyrics_list)
            if a.name == 'br' and lyrics_list[len(lyrics_list) - 1] != '':
                lyrics_list.append('')
    return lyrics_list

#Helper function to handle appending and manipulating lyrics_list. A new line is generated only for </br> tags
def _handleLyricAppend(lyrics_list, lyric):
    if lyric is not None:
        last_index = len(lyrics_list) - 1
        #Handle special cases (parenthesis and symbols stick with words for instance)
        if lyrics_list[last_index] != '' and (lyrics_list[last_index][-1] in ['(','[','{','<'] or lyric in [')',']','}','>','!','?',',','.']):
            lyrics_list[last_index] += lyric
        else:
            lyrics_list[last_index] += " " + lyric if lyrics_list[last_index] != '' else lyric

#Determines whether a song will need to be translated (returns the link if it does, otherwise returns None)
def _getSongTranslationLink(html):
    translation_tags = html.findAll('a', class_='TextButton-sc-192nsqv-0 hVAZmF LyricsControls__TextButton-sghmdv-6 hXTHjZ')
    for tag in translation_tags:
        if "english-translations" in tag['href']:
            return tag['href']
    return None

#Determines whether a page exists
def _pageExists(html):
    return html.find('div', class_='render_404') == None

@functions_framework.http
def get_lyrics(request):
    headers = { 
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }   
    # try:
    #     request_json = request.get_json()
    # except:
    #     request_json = None
    request_args = request.args
    artistnames = []
    songname = ''
    # if request_json and all(k in request_json for k in ("artists","song")):
    #     artistnames = request_json['artists']
    #     songname = request_json['song']
    if request_args and all(k in request_args for k in ("artists","song")):
        artistnames = request_args['artists'].split(',')
        songname = request_args['song']
    else:
        return ({"error":"Bad Input, must pass artist(s) and song name"}, 400, headers)
    lyrics_list = []
    found = False
    i = 0
    html = None
    while i < len(artistnames) and not(found):
        artistname = artistnames[i]
        artistname2 = str(artistname.replace(' ','-')) if ' ' in artistname else str(artistname)
        songname2 = str(songname.replace(' ','-')) if ' ' in songname else str(songname)
        page_url = 'https://genius.com/'+ artistname2 + '-' + songname2 + '-' + 'lyrics'
        page = requests.get(page_url)
        html = BeautifulSoup(page.text, 'html.parser') 
        found = _pageExists(html)
        i += 1
    if found:
        #check if there is an english translation
        translation_url = _getSongTranslationLink(html)
        if translation_url is not None:
            page = requests.get(translation_url)
            html = BeautifulSoup(page.text, 'html.parser') 
            lyrics_list = _getLyricsFromHTML(html)
        else:
            #If there isn't a translation, make sure it's in english in the first place
            english = False
            for script in html.findAll('script'):
                if "language\\\":\\\"en" in str(script):
                    english = True
            if english: lyrics_list = _getLyricsFromHTML(html)
    return ({"lyrics":lyrics_list}, 200, headers)

###################
   
   # request_json = request.get_json(silent=True)
   # request_args = request.args
   # print("json: \n",request_json,sep='')
   # print("args: \n",request_args,sep='')
   # """HTTP Cloud Function.
   # Args:
   #    request (flask.Request): The request object.
   #    <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
   # Returns:
   #    The response text, or any set of values that can be turned into a
   #    Response object using `make_response`
   #    <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
   # """
   # if request_json and 'name' in request_json:
   #    name = request_json['name']
   # elif request_args and 'name' in request_args:
   #    name = request_args['name']
   # else:
   #    name = 'World'