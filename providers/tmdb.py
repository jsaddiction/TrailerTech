#!/usr/bin/env python3

import tmdbsimple as tmdb
from requests import HTTPError
from datetime import datetime
from utils import logger

log = logger.get_log(__name__)
YOUTUBE_BASE_URL = 'https://www.youtube.com/watch?v='
VIMEO_BASE_URL = 'https://vimeo.com/'
TMDB_API = '28c936c57b653df80585b30667c1aa2d'

class Tmdb(object):
    def __init__(self, min_resolution, max_resolution, languages, api_key=None):
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        self.languages = languages
        self.data = None
        if not api_key:
            tmdb.API_KEY = TMDB_API
        else:
            tmdb.API_KEY = api_key

    @property
    def hasAPIkey(self):
        return not tmdb.API_KEY == None

    @property
    def title(self):
        if not self.data:
            return None

        if 'original_title' in self.data:
            return self.data.get('original_title', None)
        if 'title' in self.data:
            return self.data.get('title', None)
        return None

    @property
    def year(self):
        if not self.data:
            return None

        if 'release_date' in self.data:
            try:
                year = str(datetime.strptime(self.data['release_date'], '%Y-%m-%d').year)
            except:
                return None
            else:
                return year
        return None

    @property
    def videos(self):
        if self.data and 'videos' in self.data:
            videos = self.data.get('videos', None)
            if 'results' in videos:
                return videos.get('results', None)
        return None

    @property
    def has_videos(self):
        if not self.videos == None:
            return True
        return False

    def getLinks(self):
        links = []

        # return empty list if no movie details or videos exist
        if not self.data or not self.videos:
            return links

        # Filter videos 
        for video in self.videos:
            # Filter based on type
            if not video['type'].lower() == 'trailer':
                log.debug('Filtered based on type. {}'.format(video['name']))
                continue

            # Filter based on size
            if not int(self.min_resolution) <= int(video['size']) or not int(self.max_resolution) >= int(video['size']):
                log.debug('Filtered based on size. {}'.format(video['name']))
                continue

            # Filter based on language
            if not video['iso_639_1'] in self.languages:
                log.debug('Filtered based on language. {}'.format(video['name']))
                continue
            
            # Build link
            trailer = {}
            if 'youtube' == video['site'].lower():
                trailer['url'] = '{}{}'.format(YOUTUBE_BASE_URL, video['key'])
            elif 'vimeo' == video['site'].lower():
                trailer['url'] = '{}{}'.format(VIMEO_BASE_URL, video['key'])
            trailer['height'] = int(video['size'])

            links.append(trailer)
        return links

    def get_trailer_links(self, languages=None, min_size=0):
        trailers = []
        if not self.videos:
            return trailers
        for video in self.videos:
            # Filter based on type
            if not video['type'].lower() == 'trailer':
                log.debug('Filtered based on type. {}'.format(video['name']))
                continue

            # Filter based on size
            if not int(min_size) < int(video['size']):
                log.debug('Filtered based on size. {}'.format(video['name']))
                continue

            # Filter based on language
            if languages:
                if not video['iso_639_1'] in languages:
                    log.debug('Filtered based on language. {}'.format(video['name']))
                    continue
            
            # Build link
            if 'youtube' == video['site'].lower():
                video['link'] = '{}{}'.format(YOUTUBE_BASE_URL, video['key'])
            elif 'vimeo' == video['site'].lower():
                video['link'] = '{}{}'.format(VIMEO_BASE_URL, video['key'])

            trailers.append(video)
        return [x['link'] for x in trailers]

    def get_movie_details(self, tmdbid=None, imdbid=None, title=None, year=None):
        log.debug('Getting data from TMDB')
        if tmdbid:
            log.debug('Searching by TMDBid: {}'.format(tmdbid))
            movie = self.__get_movie(tmdbid)
        elif imdbid:
            log.debug('Searching by IMDBid: {}'.format(imdbid))
            movie = self.__get_movie(self.__convert_imdb(imdbid))
        elif title and year:
            log.debug('Searching by Title and Year: {} {}'.format(title, year))
            movie = self.__get_movie(self.__convert_title_year(title, year))
        else:
            log.critical('Not enough info was provided to search TMDB. \n\tTMDBID: {}\n\tIMDBID: {}\n\tTitle: {}\n\tYear:{}'.format(
                tmdbid, imdbid, title, year
            ))
            return None
        try:
            self.data = movie.info(append_to_response='videos')
        except HTTPError as e:
            self._handle_error(e)
            return None
        return True

    def __get_movie(self, tmdbid):
        try:
            movie = tmdb.Movies(tmdbid)
        except HTTPError as e:
            self._handle_error(e)
            return False
        return movie

    def __get_movie_data(self, movie):
        try:
            data = movie.info(append_to_response='videos')
        except HTTPError as e:
            self._handle_error(e)
            return None

        return data

    def __convert_imdb(self, imdbid):
        try:
            tmdb_id = tmdb.Find(imdbid).info(external_source='imdb_id')['movie_results'][0]['id']
        except HTTPError as e:
            self._handle_error(e)
            return False
        except IndexError:
            log.warning('IMDB id not found: {}'.format(imdbid))
            self.data = None
            return False
        
        return tmdb_id

    def __convert_title_year(self, title, year):
        try:
            response = tmdb.Search().movie(query=title, year=year)
        except HTTPError as e:
            self._handle_error(e)
            return False
        
        if not response['results'] or len(response['results']) < 1:
            self.data = None
            return False

        for result in response['results']:
            if str(year) in result['release_date'] and result['title'].lower() == title.lower():
                return result['id']

    def _handle_error(self, error):
        status_code = error.response.status_code
        self.data = None
        if status_code == 401:
            log.error('TMDB API key was not accepted.')
        elif status_code == 404:
            log.debug('TMDB reported "Not Found"')
        else:
            log.warning('TMDB returned Error: {}:{}'.format(status_code, error.response))
        return
