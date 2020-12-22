#!/usr/bin/env python3

import tmdbsimple as tmdb
from requests import HTTPError
from datetime import datetime
# from providers import config, log, tmdb
from utils import logger

log = logger.get_log(__name__)
YOUTUBE_BASE_URL = 'https://www.youtube.com/watch?v='

class Tmdb(object):
    def __init__(self, api_key):
        self.data = None
        tmdb.API_KEY = api_key

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

    def get_trailer_links(self, languages=None, min_size=0):
        trailers = []
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

            video['link'] = '{}{}'.format(YOUTUBE_BASE_URL, video['key'])

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
            if year in result['release_date'] and result['title'].lower() == title.lower():
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

'''
{
    "adult":false,
    "backdrop_path":"/cqa3sa4c4jevgnEJwq3CMF8UfTG.jpg",
    "belongs_to_collection":null,
    "budget":100000000,
    "genres":[
        {
            "id":10752,
            "name":"War"
        },
        {
            "id":18,
            "name":"Drama"
        },
        {
            "id":28,
            "name":"Action"
        },
        {
            "id":36,
            "name":"History"
        }
        ],
        "homepage":"https://www.1917.movie/",
        "id":530915,
        "imdb_id":"tt8579674",
        "original_language":"en",
        "original_title":"1917",
        "overview":"At the height of the First World War, two young British soldiers must cross enemy territory and deliver a message that will stop a deadly attack on hundreds of soldiers.",
        "popularity":210.76,
        "poster_path":"/iZf0KyrE25z1sage4SYFLCCrMi9.jpg",
        "production_companies":[
            {"id":1522,"logo_path":"/8uaoEVgNxFH0R94O53gUiByahVr.png","name":"Neal Street Productions","origin_country":"GB"},
            {"id":7,"logo_path":"/vru2SssLX3FPhnKZGtYw00pVIS9.png","name":"DreamWorks Pictures","origin_country":"US"},
            {"id":114732,"logo_path":"/tNCbisMxO5mX2X2bOQxHHQZVYnT.png","name":"New Republic Pictures","origin_country":"US"},
            ],
        "production_countries":[
            {"iso_3166_1":"CA","name":"Canada"},
            {"iso_3166_1":"IN","name":"India"},
            ],
        "release_date":"2019-12-25",
        "revenue":374733942,
        "runtime":119,
        "spoken_languages":[
            {"iso_639_1":"en","name":"English"},
            {"iso_639_1":"fr","name":"Français"},
            {"iso_639_1":"de","name":"Deutsch"}
            ],
        "status":"Released",
        "tagline":"Time is the enemy",
        "title":"1917",
        "video":false,
        "vote_average":7.9,
        "vote_count":6329,
        "videos":{
            "results":[
                {
                    "id":"5d43077cd8cc4a001435a1af",
                    "iso_639_1":"en",
                    "iso_3166_1":"US",
                    "key":"UcmZN0Mbl04",
                    "name":"Official Trailer",
                    "site":"YouTube",
                    "size":1080,
                    "type":"Trailer"
                },
                {
                    "id":"5d96a0073bd26e13a4b64c5e",
                    "iso_639_1":"en",
                    "iso_3166_1":"US",
                    "key":"3hSjs2hBa94",
                    "name":"1917 - In Theaters December (Behind The Scenes Featurette) [HD]",
                    "site":"YouTube",
                    "size":1080,
                    "type":"Featurette"
                },
                {
                    "id":"5d969fe63bd26e0011b721b9",
                    "iso_639_1":"en",
                    "iso_3166_1":"US",
                    "key":"YqNYrYUiMfg",
                    "name":"Official Trailer 2",
                    "site":"YouTube",
                    "size":1080,
                    "type":"Trailer"
                },
                {
                    "id":"5dfa71025ed9620013e33ffd",
                    "iso_639_1":"en",
                    "iso_3166_1":"US",
                    "key":"wlbJZQQJ528",
                    "name":"1917 Exclusive Movie Clip - Running Through Ruins (2019) | Movieclips Coming Soon",
                    "site":"YouTube",
                    "size":1080,
                    "type":"Clip"
                },
                {
                    "id":"5e0c35611511aa0014afe590",
                    "iso_639_1":"en",
                    "iso_3166_1":"US",
                    "key":"gZjQROMAh_s",
                    "name":"Official Trailer 3",
                    "site":"YouTube",
                    "size":1080,
                    "type":"Trailer"
                }
                ]
                }
                }
'''