#!/usr/bin/env python3

import os
class Env():

    def __init__(self):
        self._vars = {k.lower():v for (k, v) in os.environ.items() if 'radarr' in k.lower()}

    @property
    def allKnown(self):
        return self._vars

    @property
    def event(self):
        event = self._vars.get('radarr_eventtype', None)
        if event:
            return event.lower()
        else:
            return None 

    @property
    def tmdbid(self):
        tmdbKeys = ['radarr_movie_tmdbid']
        for k, v in self._vars.items():
            if k in tmdbKeys:
                return v
        return None

    @property
    def imdbid(self):
        imdbKeys = ['radarr_movie_imdbid']
        for k, v in self._vars.items():
            if k in imdbKeys:
                return v
        return None

    @property
    def year(self):
        yearKeys = ['radarr_movie_year']
        for k, v in self._vars.items():
            if k in yearKeys:
                return v
        return None

    @property
    def movieFileName(self):
        movieFileNameKeys = ['radarr_moviefile_relativepath']
        for k, v in self._vars.items():
            if k in movieFileNameKeys:
                return v
        return None

    @property
    def moviePath(self):
        moviePathKeys = ['radarr_moviefile_path']
        for k, v in self._vars.items():
            if k in moviePathKeys:
                return v
        return None

    @property
    def movieDirectory(self):
        movieDirectoryKeys = ['radarr_movie_path']
        for k, v in self._vars.items():
            if k in movieDirectoryKeys:
                return v
        return None

    @property
    def movieTitle(self):
        movieTitleKeys = ['radarr_movie_title']
        for k, v in self._vars.items():
            if k in movieTitleKeys:
                return v
        return None
