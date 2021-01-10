#!/usr/bin/env python3

import os
import shutil
import json
import socket
import html.parser
import unicodedata
import requests
from unidecode import unidecode
from urllib.request import Request, urlopen
from utils import logger

trailer_url = 'https://trailers.apple.com/'
moviePage_url = 'https://trailers.apple.com/'
# search_url = 'https://trailers.apple.com/trailers/home/scripts/quickfind.php?q='
search_url = 'https://trailers.apple.com/trailers/home/scripts/quickfind.php'
log = logger.get_log(__name__)
resolutions = ['1080', '720', '480']

class Apple():
    def __init__(self, min_resolution, max_resolution):
        self.min_resolution = int(min_resolution)
        self.max_resolution = int(max_resolution)

    # New
    def _getJson(self, url, params=None):
        try:
            with requests.get(url, params=params, timeout=5) as r:
                r.raise_for_status()
                result = r.json()
                result['url'] = r.url
                return result
        except ValueError:
            log.warning('Failed to parse data returned from Apple. url: {} response:{}'.format(url, r.text))
            return None
        except requests.exceptions.Timeout:
            log.warning('Timed out while connecting to {}'.format(url))
            return None
        except ConnectionError as e:
            log.warning('Failed to connect to {} Error: {}'.format(url, e))
            return None
        except requests.exceptions.HTTPError as e:
            log.warning('Apple search failed for "{}". {}'.format(url, e))
            return None

    # New
    def getLinks(self, title, year):
        urls = []

        # search for movies
        movies = self._getJson(search_url, params={'q': title})
        log.warning(movies['url'])

        if not movies:
            return urls

        # ensure we don't have errors
        if movies.get('error', True) == True:
            log.warning('Apple returned an error in its response. Response: {}'.format(movies))
            return urls

        # ensure we have at least one result to parse
        if not len(movies.get('results')) > 0:
            return urls


        # Get all movies that title and year match
        for movie in movies.get('results'):
            if title.lower() == movie.get('title').lower():
                if str(year) in movie.get('releasedate'):
                    location = movie.get('location', None)
                else:
                    log.warning('{} not in {}'.format(year, movie.get('releasedate')))
                    location = None
            else:
                log.warning('{} != {}'.format(title, movie.get('title')))
                location = None

        # check if we have a movie page
        if not location:
            return urls

        # Get Movie data
        movieData = self._getJson(moviePage_url + location + '/data/page.json')

        # Collect all trailer links
        links =[]
        for clip in movieData['clips']:
            if 'trailer' in clip['title'].lower():
                for item in clip['versions']['enus']['sizes']:
                    if int(clip['versions']['enus']['sizes'][item]['height']) >= self.min_resolution:
                        if int(clip['versions']['enus']['sizes'][item]['height']) <= self.max_resolution:
                            links.append({
                                'url': clip['versions']['enus']['sizes'][item]['src'],
                                'height': clip['versions']['enus']['sizes'][item]['height'],
                                })
                            links.append({
                                'url': clip['versions']['enus']['sizes'][item]['srcAlt'],
                                'height': clip['versions']['enus']['sizes'][item]['height'],
                                })

        links.sort(reverse=True, key=lambda link: link['height'])

        return [link['url'] for link in links]

    # # Match titles
    # def _matchTitle(self, title):
    #     return unicodedata.normalize('NFKD', self._removeSpecialChars(title).replace('/', '').replace('\\', '').replace('-', '').replace(':', '').replace('*', '').replace('?', '').replace("'", '').replace('<', '').replace('>', '').replace('|', '').replace('.', '').replace('+', '').replace(' ', '').lower()).encode('ASCII', 'ignore')

    # # Remove special characters
    # def _removeSpecialChars(self, query):
    #     return ''.join([ch for ch in query if ch.isalnum() or ch.isspace()])

    # # Remove accent characters
    # def _removeAccents(self, query):
    #     return unidecode(query)

    # # Unescape characters
    # def _unescape(self, query):
    #     return html.unescape(query)

    # # Load json from url
    # def _loadJson(self, url):
    #     response = urlopen(url)
    #     str_response = response.read().decode('utf-8')
    #     return json.loads(str_response)

    # # Map resolution
    # def _mapRes(self, res):
    #     res_mapping = {'480': u'sd', '720': u'hd720', '1080': u'hd1080'}
    #     if res not in res_mapping:
    #         res_string = ', '.join(res_mapping.keys())
    #         raise ValueError('Invalid resolution. Valid values: %s' % res_string)
    #     return res_mapping[res]

    # # Convert source url to file url
    # def _convertUrl(self, src_url, res):
    #     src_ending = '_%sp.mov' % res
    #     file_ending = '_h%sp.mov' % res
    #     return src_url.replace(src_ending, file_ending)

    # # Get file urls
    # def _getUrls(self, page_url, res):
    #     urls = []
    #     film_data = self._loadJson(page_url + '/data/page.json')
    #     title = film_data['page']['movie_title']
    #     apple_size = self._mapRes(res)

    #     for clip in film_data['clips']:
    #         video_type = clip['title']
    #         if apple_size in clip['versions']['enus']['sizes']:
    #             file_info = clip['versions']['enus']['sizes'][apple_size]
    #             file_url = self._convertUrl(file_info['src'], res)
    #             video_type = video_type.lower()
    #             if (video_type.startswith('trailer')):
    #                 url_info = {
    #                     'res': res,
    #                     'title': title,
    #                     'type': video_type,
    #                     'url': file_url,
    #                 }
    #                 urls.append(url_info)

    #     final = []
    #     length = len(urls)

    #     if length > 1:
    #         final.append(urls[length-1])
    #         return final
    #     else:
    #         return urls

    # def getLinks_old(self, title, year):
            # links = []
            # query = self._removeSpecialChars(title)
            # query = self._removeAccents(query)
            # query = query.replace(' ', '+')
            # search_url = 'https://trailers.apple.com/trailers/home/scripts/quickfind.php?q='+query
            # log.warning(search_url)
            # search = self._loadJson(search_url)

            # # Parse search results
            # for result in search['results']:
            #     for res in resolutions:
            #         if int(res) > int(self.min_resolution):
            #             # Filter by year and title
            #             if 'releasedate' in result and 'title' in result:
            #                 if str(year).lower() in result['releasedate'].lower() and self._matchTitle(title) == self._matchTitle(self._unescape(result['title'])):
            #                     if 'location' in result:
            #                         if result['location'].startswith('/'):
            #                             result['location'] = result['location'][1:]
            #                         if result['location'].endswith('/'):
            #                             result['location'] = result['location'][:-1]
            #                     urls = [x['url'] for x in self._getUrls(trailer_url+result['location'], res)]
            #                     if len(urls) > 0:
            #                         links.extend(urls)
            # return links