#!/usr/bin/env python3

import os
import json
import subprocess
import re
from datetime import datetime
from utils import logger
try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

MIN_MOVIE_DURATION = 600  # In seconds
MIN_TRAILER_SIZE = 500000  # In bytes
VIDEO_EXTENSIONS = ['.mkv', '.iso', '.wmv', '.avi', '.mp4', '.m4v', '.img', '.divx', '.mov', '.flv', '.m2ts', '.ts']
NFO_EXTENSIONS = ['.nfo', '.xml']
ID_TAGS = ['imdb', 'tmdb', 'imdbid', 'tmdbid', 'tmdb_id', 'imdb_id', 'id']
IMDB_ID_PATTERN = re.compile(r'ev\d{7,8}\/\d{4}(-\d)?|(ch|co|ev|nm|tt)\d{7,8}', flags=re.IGNORECASE)
TMDB_ID_PATTERN = re.compile(r'[1-9]\d{1,10}')
YEAR_PATTERN = re.compile(r'\d{4}')

log = logger.get_log(__name__)

class File():
    def __init__(self, path):
        self.path = path

    @property
    def fileName(self):
        return os.path.basename(self.path)

    @property
    def fileSize(self):
        return os.path.getsize(self.path)

    def delete(self):
        try:
            os.remove(self.path)
        except OSError:
            pass

class Video(File):
    def __init__(self, path):
        super().__init__(path)

    @property
    def isCorrupt(self):
        # skip if file not supported
        if os.path.splitext(self.fileName)[-1] in ['.iso']:
            return False

        # if file is too small assume its corrupt
        if self.fileSize < MIN_TRAILER_SIZE:
            return True

        result = subprocess.run([
            'ffprobe', '-v', 'fatal', '-print_format', 
            'json', '-show_format', '-show_streams', '-show_error',
            self.path],
            stdout=subprocess.PIPE
            )

        videoDetails = json.loads(result.stdout.decode())
        returnCode = result.returncode
        if returnCode != 0:
            return True
        if videoDetails.get('error'):
            return True
        if not videoDetails.get('streams'):
            return True
        
        video_streams = [item for item in videoDetails['streams'] if item['codec_type'] == 'video']
        audio_streams = [item for item in videoDetails['streams'] if item['codec_type'] == 'audio']
        
        if len(video_streams) > 0 and len(audio_streams) > 0:
            return False
        else:
            return True

    @property
    def isMovie(self):
        if os.path.splitext(self.fileName)[0].endswith('-trailer'):
            return False

        duration = self.get_duration()
        if not duration is None:
            if duration >= MIN_MOVIE_DURATION:
                return True
            else:
                # video is less than min_movie_duration and does not include -trailer in its filename
                return None
        else:
            # Unable to determine duration assume its the movie since it doesn't have -trailer in file name
            return True

    def get_duration(self):
        result = subprocess.run([
            'ffprobe', '-v', 'fatal', '-show_entries',
            'format=duration', '-of',
            'default=noprint_wrappers=1:nokey=1',
            self.path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
            )
        try:
            return float(result.stdout)
        except ValueError:
            return None

class NFO(File):
    def __init__(self, path):
        super().__init__(path)
        self.__originaltitle = None
        self.__title = None
        self.__localtitle = None
        self.__year = None
        self.__releasedate = None
        self.__premiered = None
        self.__productionyear = None
        self.__imdb = None
        self.__tmdb = None
        self.__unique_id_imdb = None
        self.__unique_id_tmdb = None
        self.__id = None
        self.__parse_nfo()

    @property
    def is_complete(self):
        if self.imdb or self.tmdb:
            return True
        elif self.title and self.year:
            return True
        else:
            return False

    @property
    def title(self):
        if isinstance(self.__originaltitle, str):
            return self.__originaltitle
        elif isinstance(self.__title, str):
            return self.__title
        elif isinstance(self.__localtitle, str):
            return self.__localtitle
        else:
            return None

    @property
    def year(self):
        if self.__premiered:
            year = self.__parse_releaseDate(self.__premiered)
            match = re.match(YEAR_PATTERN, year)
            if match:
                return year
        
        if self.__releasedate:
            year = self.__parse_releaseDate(self.__parse_releaseDate)
            match = re.match(YEAR_PATTERN, year)
            if match:
                return year
        
        if self.__year:
            match = re.match(YEAR_PATTERN, self.__year)
            if match:
                return self.__year

        if self.__productionyear:
            match = re.match(YEAR_PATTERN, self.__productionyear)
            if match:
                return self.__productionyear

        return None

    @property
    def imdb(self):
        if self.__unique_id_imdb and re.match(IMDB_ID_PATTERN, self.__unique_id_imdb):
            return self.__unique_id_imdb
        if self.__imdb and re.match(IMDB_ID_PATTERN, self.__imdb):
            return self.__imdb
        if self.__id and re.match(IMDB_ID_PATTERN, self.__id):
            return self.__id
        return None

    @property
    def tmdb(self):
        if self.__unique_id_tmdb and re.match(TMDB_ID_PATTERN, self.__unique_id_tmdb):
            return self.__unique_id_tmdb
        if self.__tmdb and re.match(TMDB_ID_PATTERN, self.__tmdb):
            return self.__tmdb
        if self.__id and re.match(TMDB_ID_PATTERN, self.__id):
            return self.__id
        return None

    def __parse_nfo(self):
        try:
            nfo = et.parse(self.path)
            root  = nfo.getroot()
        except (IOError, et.ParseError) as e:
            log.debug('Failed to parse NFO: {} ERROR: {}'.format(self.fileName, e))
            return


        for item in root:
            # Parse uniqueid
            if item.tag.lower() == 'uniqueid':
                if item.attrib['type'].lower() == 'tmdb':
                    self.__unique_id_tmdb = item.text
                elif item.attrib['type'].lower() == 'imdb':
                    self.__unique_id_imdb = item.text
            
            # Parse additional ids
            elif item.tag.lower() in ID_TAGS:
                self.__parse_id(item.text)
            
            # Parse release years
            elif item.tag.lower() == 'premiered':
                self.__premiered = self.__parse_releaseDate(item.text)
            elif item.tag.lower() == 'release_date':
                self.__releasedate = self.__parse_releaseDate(item.text)
            elif item.tag.lower() == 'year':
                self.__year = item.text
            elif item.tag.lower() == 'productionyear':
                self.__productionyear = item.text

            # Parse titles
            elif item.tag.lower() == 'title':
                self.__title = item.text
            elif item.tag.lower() == 'originaltitle':
                self.__originaltitle = item.text
            elif item.tag.lower() == 'localtitle':
                self.__localtitle = item.text

    def __parse_releaseDate(self, releaseDate):
        if releaseDate:
            if len(releaseDate) == 4 and releaseDate.isdigit():
                return releaseDate
            try:
                year = str(datetime.strptime(releaseDate, '%Y-%m-%d').year)
            except:
                return None
            return year
        else:
            return None

    def __parse_id(self, movie_id):
        if movie_id:
            if movie_id.lower().startswith('tt'):
                self.__imdb = movie_id
            elif movie_id.isdigit():
                self.__tmdb = movie_id
        return None

class MovieFolder():
    def __init__(self, directory, deleteCorruptTrailer=False):
        self.deleteCorruptTrailer = deleteCorruptTrailer
        self.rootDir = os.path.abspath(directory)
        self.movie = None
        self.trailer = None
        self._nfo = None
        self.scan()

    @property
    def title(self):
        if self._nfo and self._nfo.title:
            return self._nfo.title
        else:
            return self._parseTitleFromFolder()
        return None

    @property
    def year(self):
        if self._nfo and self._nfo.year:
            return self._nfo.year
        else:
            return self._parseYearFromFolder()
        return None

    @property
    def tmdb(self):
        if self._nfo and self._nfo.tmdb:
            return self._nfo.tmdb
        return None

    @property
    def imdb(self):
        if self._nfo and self._nfo.imdb:
            return self._nfo.imdb
        else:
            return self._parseIMDBFromMovieFile()
        return None

    @property
    def trailerName(self):
        if self.hasMovie:
            return os.path.splitext(self.movie.fileName)[0] + '-trailer.mp4'
        else:
            return self.title + ' (' + self.year + ')-trailer.mp4'

    @property
    def trailerDirectory(self):
        if self.hasMovie:
            return os.path.dirname(self.movie.path)
        else:
            return self.rootDir

    @property
    def hasTrailer(self):
        return not self.trailer == None

    @property
    def hasMovie(self):
        return not self.movie == None

    def _parseTitleFromFolder(self):
        title = os.path.basename(self.rootDir).split('(')[0].strip()
        log.debug('Parsed title from folder: {}'.format(title)) 
        return title

    def _parseYearFromFolder(self):
        year = os.path.basename(self.rootDir).split('(')[-1].replace('(', '').replace(')', '').strip()
        log.debug('Parsed year from folder: {}'.format(year))
        match = re.match(YEAR_PATTERN, year)
        if match:
            return year
        return None

    def _parseIMDBFromMovieFile(self):
        if self.movie:
            match = re.search(IMDB_ID_PATTERN, self.movie.path)
            if match:
                imdb = match.group(0)
                log.debug('Parsed IMDB from movie file name: {}'.format(imdb))
                return imdb
        return None

    def scan(self):
        for item in os.scandir(self.rootDir):
            if os.path.isfile(item.path):
                ext = os.path.splitext(item.path)[-1].lower()
                if ext in VIDEO_EXTENSIONS:
                    video = Video(item.path)
                    isMovie = video.isMovie
                    if isMovie:
                        self.movie = video
                        log.debug('Movie Found: {}'.format(self.movie.fileName))
                    elif isMovie == False:
                        if self.deleteCorruptTrailer and video.isCorrupt:
                            log.warning('Deleting corrupt trailer {}'.format(self.trailer.fileName))
                            video.delete()
                        else:
                            self.trailer = video
                            log.debug('Trailer Found: {}'.format(self.trailer.fileName))
                    elif isMovie == None:
                        log.warning('Could not determine if video is movie or trailer: {}'.format(video.path))
                elif ext in NFO_EXTENSIONS:
                    nfo = NFO(item.path)
                    if (nfo.is_complete and not self._nfo) or (nfo.is_complete and nfo.fileSize > self._nfo.fileSize):
                        self._nfo = nfo
                        log.debug('NFO Found: {}'.format(self._nfo.fileName))
            
            elif os.path.isdir(item.path):
    
                # Handle bdmv folders
                if 'bdmv' in item.path.lower() and os.path.isdir(item.path):
                    log.debug('Encountered a BluRay folder structure "{}"'.format(item.path))
                    bd_file = os.path.join(item.path, 'index.bdmv')
                    if os.path.isfile(bd_file):
                        video = Video(bd_file)
                        log.debug('Movie Found: {}'.format(video.fileName))
                        self.movie = video
                        # Find the trailer in the BDMV folder
                        for entry in os.listdir(item.path):
                            path = os.path.join(item.path, entry)
                            if os.path.isfile(path) and os.path.splitext(path)[-1] in VIDEO_EXTENSIONS:
                                video = Video(path)
                                if not video.isMovie:
                                    log.debug('Found trailer: {}'.format(video.fileName))
                                    self.trailer = video
                
                # Handle video_ts folders
                elif 'video_ts' in item.path.lower() and os.path.isdir(item.path):
                    log.debug('Encountered a DVD folder structure "{}"'.format(item.path))
                    dvd_file = os.path.join(item.path, 'VIDEO_TS.IFO')
                    if os.path.isfile(dvd_file):
                        video = Video(dvd_file)
                        log.debug('Movie Found: {}'.format(video.fileName))
                        self.movie = video
                        # Find the trailer in the VIDEO_TS folder
                        for entry in os.listdir(item.path):
                            path = os.path.join(item.path, entry)
                            if os.path.isfile(path) and os.path.splitext(path)[-1] in VIDEO_EXTENSIONS:
                                video = Video(path)
                                if not video.isMovie:
                                    log.debug('Trailer Found: {}'.format(video.fileName))
                                    self.trailer = video
