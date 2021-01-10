#!/usr/bin/env python3

import requests
import socket
from utils import logger

moviePage_url = 'https://trailers.apple.com/'
movieSearch_url = 'https://trailers.apple.com/trailers/home/scripts/quickfind.php'
log = logger.get_log(__name__)

class Apple():
    def __init__(self, min_resolution, max_resolution):
        self.min_resolution = int(min_resolution)
        self.max_resolution = int(max_resolution)

    def _getMoivePage(self, title, year):
        movies = self._getJson(movieSearch_url, params={'q': title})

        if not movies:
            return False

        if movies.get('error', True) == True:
            log.debug('Apple could not find the movie "{}" url: {}'.format(title, movies['url']))
            return False

        if not 'results' in movies or len(movies.get('results')) < 1:
            log.debug('Apple returned no results for "{}" url: {}'.format(title, movies['url']))
            return False

        # find matching movie in results
        location = None
        for movie in movies.get('results'):
            if title.lower() == movie.get('title', '').lower() and str(year) in movie.get('releasedate', ''):
                    location = movie.get('location', None)
                    break
        
        # check if we found the right movie
        if not location:
            return False

        # build and get data for movie
        url = requests.compat.urljoin(moviePage_url, location + '/data/page.json')
        log.debug('Getting movie data from url: {}'.format(url))
        movieData = self._getJson(url)

        if not movieData:
            return False

        return movieData

    def _getJson(self, url, params=None):
        try:
            with requests.get(url, params=params, timeout=5) as r:
                r.raise_for_status()
                result = r.json()
                result['url'] = r.url
                return result
        except ValueError:
            log.debug('Failed to parse data returned from Apple. url: {} response:{}'.format(r.url, r.text))
            return None
        except requests.exceptions.Timeout:
            log.warning('Timed out while connecting to {}'.format(url))
            return None
        except requests.exceptions.ConnectionError as e:
            log.warning('Failed to connect to {} Error: {}'.format(url, e))
            return None
        except requests.exceptions.HTTPError as e:
            log.warning('Apple search failed for {} Error: {}'.format(url, e))
            return None
        except requests.exceptions.RequestException as e:
            log.warning('Unknown error: {}'.format(e))
            return None

    def getLinks(self, title, year):
        links =[]

        # Get movie page data
        movieData = self._getMoivePage(title, year)

        # return empty list if no movie page was found
        if not movieData:
            return links

        # Collect all trailer links
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
