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
