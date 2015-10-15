# -*- coding: utf-8 -*-

# based on argenteam.net subtitles, based on a mod of Subdivx.com subtitles, based on a mod of Undertext subtitles
# developed by quillo86 and infinito for Subtitulos.es and XBMC.org
# little fixes and updates by tux_os

# updated to new gotham subtitles service by infinito

# adapted to new tusubtitulo.com website by anon6

import xbmc
import re
import urllib
from operator import itemgetter
from utils import languages
try:
	import StorageServer
except:
	import storageserverdummy as StorageServer

main_url = "http://www.tusubtitulo.com/"
debug_pretext = "tusubtitulo.com"
series_pattern = "<img class=\"icon\" src=\"images/icon-television.png\"[^>]*><a href=\"/show/([^\"]+)\">:TVSHOW</a>"
subtitle_pattern1 = "<div id=\"version\" class=\"ssdiv\">(.+?)Versi&oacute;n(.+?)<span class=\"right traduccion\">(.+?)</div>(.+?)</div>"
subtitle_pattern2 = "<li class='li-idioma'>(.+?)<strong>(.+?)</strong>(.+?)<li class='li-estado (.+?)</li>(.+?)<li class='descargar (.+?)'>(.+?)</li>"
cache = StorageServer.StorageServer("tusubtitulocom", 168)

def log(module, msg):
	xbmc.log("### [%s] - %s" % (module,msg,), level=xbmc.LOGDEBUG)

def search_tvshow(tvshow, season, episode, languages, filename):
	subs = list()

	retry = True

	while True:
		content = cache.cacheFunction(getseries)

		for level in range(4):
			searchstring, ttvshow, sseason, eepisode = getsearchstring(tvshow, season, episode, level)

			serie_pattern = re.sub(':TVSHOW', ttvshow, series_pattern)
			#log( __name__ ,"%s Serie pattern = %s" % (debug_pretext, serie_pattern))

			for matches in re.finditer(serie_pattern, content, re.IGNORECASE | re.DOTALL | re.MULTILINE | re.UNICODE):
				retry = False
				numshow = matches.group(1)
				#log( __name__ ,"%s numshow = %s" % (debug_pretext, numshow))

				url = main_url + searchstring + '/' + numshow
				#log( __name__ ,"%s url = %s" % (debug_pretext, url))

				subs.extend(getallsubsforurl(url, languages, None, ttvshow, sseason, eepisode, level))

		if retry:
			#log( __name__ ,"%s retry" % (debug_pretext))
			cache.delete("%")
			retry = False
		else:
			break

	subs = clean_subtitles_list(subs)
	subs = order_subtitles_list(subs)
	return subs

def getseries():
	#log( __name__ ,"%s getseries list" % (debug_pretext))
	url = main_url + 'series.php'
	return geturl(url)
		
def getsearchstring(tvshow, season, episode, level):

	# Clean tv show name
	if level == 1 and re.search(r'\([^)][a-zA-Z]*\)', tvshow):
	    # Series name like "Shameless (US)" -> "Shameless US"
	    tvshow = tvshow.replace('(', '').replace(')', '')

	if level == 2 and re.search(r'\([^)][0-9]*\)', tvshow):
	    # Series name like "Scandal (2012)" -> "Scandal"
	    tvshow = re.sub(r'\s\([^)]*\)', '', tvshow)

	if level == 3 and re.search(r'\([^)]*\)', tvshow):
	    # Series name like "Shameless (*)" -> "Shameless"
	    tvshow = re.sub(r'\s\([^)]*\)', '', tvshow)

	# Zero pad episode
	episode = str(episode).rjust(2, '0')

	tvshow = tvshow.strip()

	# Build search string
	searchstring = 'serie/' + tvshow + '/' + season + '/' + episode

	# Replace spaces with dashes
	searchstring = re.sub(r'\s', '-', searchstring)

	searchstring = searchstring.lower()

	#log( __name__ ,"%s Search string = %s" % (debug_pretext, searchstring))
	return searchstring, tvshow, season, episode

def getallsubsforurl(url, langs, file_original_path, tvshow, season, episode, level):

	subtitles_list = []

	content = geturl(url)

	for matches in re.finditer(subtitle_pattern1, content, re.IGNORECASE | re.DOTALL | re.MULTILINE | re.UNICODE):
		
		filename = urllib.unquote_plus(matches.group(2))
		filename = re.sub(r' ', '.', filename)
		filename = re.sub(r'\s', '.', tvshow) + "." + season + "x" + episode + filename

		server = filename
		backup = filename
		subs = matches.group(4)

		for matches in re.finditer(subtitle_pattern2, subs, re.IGNORECASE | re.DOTALL | re.MULTILINE | re.UNICODE):
			#log( __name__ ,"Descargas: %s" % (matches.group(2)))

			lang = matches.group(2)
			lang = re.sub(r'\xc3\xb1', 'n', lang)
			lang = re.sub(r'\xc3\xa0', 'a', lang)
			lang = re.sub(r'\xc3\xa9', 'e', lang)

			#log( __name__ ,"lang: %s" % (lang))

			if lang in languages:
				languageshort = languages[lang][1]
				languagelong = languages[lang][0]
				filename = filename + ".(%s)" % languages[lang][2]
				server = filename
				order = 1 + languages[lang][3]
			else:
				lang = "Unknown"
				languageshort = languages[lang][1]
				languagelong = languages[lang][0]
				filename = filename + ".(%s)" % languages[lang][2]
				server = filename
				order = 1 + languages[lang][3]

			#log( __name__ ,"lang: %s - %s - %s" % (lang,languageshort,languagelong))

			estado = matches.group(4)
			estado = re.sub(r'\s', '', estado)

			#log( __name__ ,"estado: %s" % (estado))

			id = matches.group(7)
			id = re.sub(r'([^-]*)href="', '', id)
			id = re.sub(r'">original([^-]*)', '', id)
			id = re.sub(r'"><b>([^-]*)', '', id)
			id = re.sub(r'"><img ([^-]*)', '', id)
			id = re.sub(r'" rel([^-]*)', '', id)
			id = re.sub(r'" re([^-]*)', '', id)
			id = re.sub(r'http://www.tusubtitulo.com/', '', id)

			#log( __name__ ,"id: %s" % (id))

			if estado.strip() == "green'>Completado".strip() and languageshort in langs:
				subtitles_list.append({'rating': "0", 'no_files': 1, 'filename': filename, 'server': server, 'sync': False, 'id' : id, 'language_flag': languageshort + '.gif', 'language_name': languagelong, 'hearing_imp': False, 'link': main_url + id, 'lang': languageshort, 'order': order})

			filename = backup
			server = backup
			    
	return subtitles_list


def geturl(url):
	class AppURLopener(urllib.FancyURLopener):
		version = "App/1.7"
		def __init__(self, *args):
			urllib.FancyURLopener.__init__(self, *args)
		def add_referrer(self, url=None):
			if url:
				urllib._urlopener.addheader('Referer', url)

	urllib._urlopener = AppURLopener()
	urllib._urlopener.add_referrer("http://www.tusubtitulo.com/")
	try:
		response = urllib._urlopener.open(url)
		content    = response.read()
	except:
		#log( __name__ ,"%s Failed to get url:%s" % (debug_pretext, url))
		content    = None
	return content

def clean_subtitles_list(subtitles_list):
    seen = set()
    subs = []
    for sub in subtitles_list:
        filename = sub['link']
        #log(__name__, "Filename: %s" % filename)
        if filename not in seen:
            subs.append(sub)
            seen.add(filename)
    return subs

def order_subtitles_list(subtitles_list):
	return sorted(subtitles_list, key=itemgetter('order')) 
	
"""
if __name__ == "__main__":
	subs = search_tvshow("les revenants", "1", "1", "es,en,fr", None)
	for sub in subs: print sub['server'], sub['link']
"""
