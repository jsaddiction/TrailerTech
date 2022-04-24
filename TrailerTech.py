#!/usr/bin/env python3

import sys
import os
import concurrent.futures
import time

from utils import config, logger, env, args
from media.movieFolder import MovieFolder
from providers.tmdb import Tmdb
from providers.apple import Apple
from downloaders.downloader import Downloader

log = logger.get_log('TrailerTech')

class TrailerTech():
    def __init__(self):
        self.directoriesScanned = 0
        self.trailersDownloaded = []
        self.trailersFound = 0
        self.startTime = time.perf_counter()
        self.tmdb = Tmdb(config.min_resolution, config.max_resolution, config.languages, config.tmdb_API_key)
        self.apple = Apple(config.min_resolution, config.max_resolution)
        self.downloader = Downloader()

    def printStats(self):
        secondsElapsed = time.perf_counter() - self.startTime
        missingTrailers = self.directoriesScanned - (len(self.trailersDownloaded) + self.trailersFound)
        statsStr = '''
           TrailerTech Stats:
           Movie Directories Scanned: {}
           Trailers Downloaded:       {}
           Missing Trailers:          {}
           Completed In:              {}s
        '''.format(self.directoriesScanned, len(self.trailersDownloaded), missingTrailers, int(secondsElapsed))
        if len(self.trailersDownloaded) > 0:
            statsStr += '\nNew Trailers:\n'
        for trailer in self.trailersDownloaded:
            statsStr += '{}\n'.format(trailer)
        
        print(statsStr)

    def get_Trailer(self, movieDir, tmdbid=None, imdbid=None, title=None, year=None):
        links = []
        # Check for invalid directory
        if not os.path.isdir(os.path.abspath(movieDir)):
            log.warning('Skipping. Invalid path: {}'.format(movieDir))
            return

        # Parse movie folder. skip if no movies found
        folder = MovieFolder(movieDir, deleteCorruptTrailer=args.deleteCorrupt)
        if not folder.hasMovie:
            log.warning('Skipping. Unable to determine Movie file in: {}'.format(movieDir))
            return

        self.directoriesScanned += 1
        
        # skip if trailer already exists
        if folder.hasTrailer:
            log.debug('Skipping. Local trailer found: {}'.format(folder.trailer.path))
            self.trailersFound += 1
            return

        # If user provided data parse that info
        if (tmdbid or imdbid) or (title and year):
            if self.tmdb.get_movie_details(tmdbid, imdbid, title, year):
                if config.apple_enabled:
                    links.extend(self.apple.getLinks(self.tmdb.title, self.tmdb.year))
                if config.youtube_enabled:
                    links.extend(self.tmdb.getLinks())
            else:
                return
        
        # Otherwise use movie folder data
        else:
            if config.apple_enabled:
                links.extend(self.apple.getLinks(folder.title, folder.year))
            if config.youtube_enabled:
                if self.tmdb.get_movie_details(folder.tmdb, folder.imdb, folder.title, folder.year):
                    links.extend(self.tmdb.getLinks())

        # sort by source; reverse=True = prefer youtube-dl
        links.sort(reverse=config.perferred_source == 'youtube', key=lambda link: link['source'])

        # sort by height; reverse=True = prefer higher definition
        links.sort(reverse=True, key=lambda link: link['height'])


        log.debug('Found {} trailer Links for "{}" ({}).'.format(len(links), folder.title, folder.year))
        for link in links:
            log.debug('Source: {}, Size: {}, link: {}'.format(link['source'], link['height'], link['url']))

        # send them to the downloader
        for link in links:
            if self.downloader.download(folder.trailerName, folder.trailerDirectory, link['url']):
                self.trailersDownloaded.append(folder.trailerName)
                return
        
        log.info('No local or downloadable trailers for "{}" ({})'.format(folder.title, folder.year))

    def scanLibrary(self, directory):
        libraryDir = os.path.abspath(directory)
        if not os.path.isdir(libraryDir):
            log.critical('"{}" is not a valid path. Exiting.'.format(libraryDir))
            return

        for item in os.listdir(libraryDir):
            path = os.path.abspath(os.path.join(libraryDir, item))
            if os.path.isdir(path):
                log.info('Scanning: {}'.format(path))
                self.get_Trailer(path)

    def scanLibraryThreaded(self, directory):
        libraryDir = os.path.abspath(directory)
        if not os.path.isdir(libraryDir):
            log.critical('"{}" is not a valid path. Exiting.'.format(libraryDir))
            return
        log.info('Building list of directories to scan for trailers.')
        movieDirs = [os.path.join(libraryDir, subDir) for subDir in os.listdir(libraryDir) if os.path.isdir(os.path.join(libraryDir, subDir))]
        log.info('Initiating scan on {} movie directories.'.format(len(movieDirs)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=None) as executer:
            executer.map(self.get_Trailer, movieDirs)

    def main(self):
        log.info('Starting TrailerTech')
        if not self.tmdb.hasAPIkey:
            log.critical('No TMDB API key was found, try adding one to settings.ini Aborting all operations.')
            sys.exit(0)
        # Check if any args were parsed from user
        if args.directory:
            if args.recursive:
                # Parse entire library
                if args.threads:
                    log.info('Parsing "{}" in recursive mode. Threads enabled.'.format(args.directory))
                    self.scanLibraryThreaded(args.directory)
                else:
                    log.info('Parsing "{}" in recursive mode.'.format(args.directory))
                    self.scanLibrary(args.directory)
            else:
                # Parse single movie directory
                log.info('Parsing "{}" in single movie mode.'.format(args.directory))
                self.get_Trailer(args.directory, args.tmdb, args.imdb, args.title, args.year)

            # Cleanup the temp download directory
            log.info('Cleaning up temp directory.')
            self.downloader.cleanUp()

        # Check environment variables
        elif env.event == 'download' and env.movieDirectory:
            log.info('Called from Radarr Parsing "{}"'.format(env.movieDirectory))
            self.get_Trailer(env.movieDirectory, env.tmdbid, env.imdbid, env.movieTitle, env.year)

            # Cleanup the temp download directory
            log.info('Cleaning up temp directory.')
            self.downloader.cleanUp()

        elif env.event == 'test':
            log.info('Radarr called with event: {}'.format(env.event))
            sys.exit(0)

        elif env.event:
            log.info('Exiting. Radarr called with unsupported EVENT: {}'.format(env.event))
            sys.exit(0)

        else:
            log.info('Exiting. Not enough data collected from arguments or environment variables.')
            sys.exit(1)



if __name__ == '__main__':
    app = TrailerTech()
    try:
        app.main()
    except KeyboardInterrupt:
        log.info('User terminated script.')
        app.printStats()
        sys.exit(0)

    log.info('Script Completed Successfully!')
    app.printStats()