#!/usr/bin/env python3

import os
import shutil
import json
import socket
import html.parser
import unicodedata
from unidecode import unidecode
# from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from utils import logger

trailer_url = 'https://trailers.apple.com/'
search_url = 'https://trailers.apple.com/trailers/home/scripts/quickfind.php?q='
log = logger.get_log(__name__)
resolutions = ['1080', '720', '480']

class Apple():
    def __init__(self, min_resolution):
        self.min_resolution = min_resolution

    def getLinks(self, title, year):
        links = []
        query = self._removeSpecialChars(title)
        query = self._removeAccents(query)
        query = query.replace(' ', '+')
        search_url = 'https://trailers.apple.com/trailers/home/scripts/quickfind.php?q='+query
        search = self._loadJson(search_url)

         # Parse search results
        for result in search['results']:
            for res in resolutions:
                if int(res) > int(self.min_resolution):
                    # Filter by year and title
                    if 'releasedate' in result and 'title' in result:
                        if year.lower() in result['releasedate'].lower() and self._matchTitle(title) == self._matchTitle(self._unescape(result['title'])):
                            if 'location' in result:
                                if result['location'].startswith('/'):
                                    result['location'] = result['location'][1:]
                                if result['location'].endswith('/'):
                                    result['location'] = result['location'][:-1]
                            urls = [x['url'] for x in self._getUrls(trailer_url+result['location'], res)]
                            if len(urls) > 0:
                                links.extend(urls)
        return links

    # Match titles
    def _matchTitle(self, title):
        return unicodedata.normalize('NFKD', self._removeSpecialChars(title).replace('/', '').replace('\\', '').replace('-', '').replace(':', '').replace('*', '').replace('?', '').replace("'", '').replace('<', '').replace('>', '').replace('|', '').replace('.', '').replace('+', '').replace(' ', '').lower()).encode('ASCII', 'ignore')

    # Remove special characters
    def _removeSpecialChars(self, query):
        return ''.join([ch for ch in query if ch.isalnum() or ch.isspace()])

    # Remove accent characters
    def _removeAccents(self, query):
        return unidecode(query)

    # Unescape characters
    def _unescape(self, query):
        return html.unescape(query)

    # Load json from url
    def _loadJson(self, url):
        response = urlopen(url)
        str_response = response.read().decode('utf-8')
        return json.loads(str_response)

    # Map resolution
    def _mapRes(self, res):
        res_mapping = {'480': u'sd', '720': u'hd720', '1080': u'hd1080'}
        if res not in res_mapping:
            res_string = ', '.join(res_mapping.keys())
            raise ValueError('Invalid resolution. Valid values: %s' % res_string)
        return res_mapping[res]

    # Convert source url to file url
    def _convertUrl(self, src_url, res):
        src_ending = '_%sp.mov' % res
        file_ending = '_h%sp.mov' % res
        return src_url.replace(src_ending, file_ending)

    # Get file urls
    def _getUrls(self, page_url, res):
        urls = []
        film_data = self._loadJson(page_url + '/data/page.json')
        title = film_data['page']['movie_title']
        apple_size = self._mapRes(res)

        for clip in film_data['clips']:
            video_type = clip['title']
            if apple_size in clip['versions']['enus']['sizes']:
                file_info = clip['versions']['enus']['sizes'][apple_size]
                file_url = self._convertUrl(file_info['src'], res)
                video_type = video_type.lower()
                if (video_type.startswith('trailer')):
                    url_info = {
                        'res': res,
                        'title': title,
                        'type': video_type,
                        'url': file_url,
                    }
                    urls.append(url_info)

        final = []
        length = len(urls)

        if length > 1:
            final.append(urls[length-1])
            return final
        else:
            return urls

# Download the file
# def _downloadFile(url, filepath):
#     data = None
#     headers = {'User-Agent': 'Quick_time/7.6.2'}
#     req = Request(url, data, headers)
#     chunk_size = 1024 * 1024

#     try:
#         server_file_handle = urlopen(req)
#     except HTTPError as e:
#         log.warning('Encountered HTTP error from apple. {}'.format(e))
#         return False
#     except URLError as e:
#         log.warning('Encountered URL error from apple. {}'.format(e))
#         return False

#     log.info('Attempting to download Apple trailer from {}'.format(url))
    
#     try:
#         with open(filepath, 'wb') as local_file_handle:
#             shutil.copyfileobj(server_file_handle, local_file_handle, chunk_size)
#             log.info('Download Complete!')
#             return True
#     except socket.error as e:
#         log.warning('Encountered Socket error from apple. {}'.format(e))
#         return False


# {
#     "error":false,
#     "results":[
#         {
#             "title":"The Croods: A New Age",
#             "releasedate":"Wed, 31 Dec 1969 16:00:00 -0800",
#             "studio":"DreamWorks",
#             "poster":"https:\/\/trailers.apple.com\/trailers\/dreamworks\/the-croods-a-new-age\/images\/poster.jpg",
#             "moviesite":"",
#             "location":"\/trailers\/dreamworks\/the-croods-a-new-age\/",
#             "urltype":"html",
#             "director":"a:1:{i:0;s:13:\"Joel Crawford\";}",
#             "rating":"PG",
#             "genre":["Action and Adventure","Family","Fantasy"],
#             "actors":["Nicolas Cage","Emma Stone","Ryan Reynolds","Catherine Keener","Cloris Leachman","Clark Duke","Leslie Mann","Peter Dinklage","Kelly Marie Tran"],
#             "trailers":[{"type":"Trailer","postdate":"Wed, 07 Oct 2020 00:00:00 -0700","exclusive":false,"hd":true}]
#         }
#     ]
# }


# # Search Apple
# def _searchApple(query):
#     query = _removeSpecialChars(query)
#     query = _removeAccents(query)
#     query = query.replace(' ', '+')
#     search_url = 'https://trailers.apple.com/trailers/home/scripts/quickfind.php?q='+query
#     return _loadJson(search_url)

# def download_apple(year, title, filepath):
# # Search Apple
#     log.debug('Searching Apple for "{} ({})"'.format(title, year))
#     search = _searchApple(title)

#     # Check search results and see if we need to continue.
#     if len(search['results']) == 0:
#         log.debug('No Results.')
#         return False

#     log.debug('Found {} Apple trailers for "{} ({})"'.format(len(search['results']), title, year))

#     # Parse search results
#     for result in search['results']:
#         for res in resolutions:
#             if int(res) > int(config['youtube']['min_resolution']):
#                 # Filter by year and title
#                 if 'releasedate' in result and 'title' in result:
#                     if year.lower() in result['releasedate'].lower() and _matchTitle(title) == _matchTitle(_unescape(result['title'])):
#                         log.debug('Trying resolution "{}"'.format(res))
#                         links = _getUrls(trailer_url+result['location'], res)
#                         for link in links:
#                             if _downloadFile(link['url'], filepath):
#                                 return True
#                     else:
#                         log.info('Filtering incorrect result: "{} ({})"'.format(result['title'], result['releasedate'].lower()))
#     # return false if no trailer was downloaded
#     return False