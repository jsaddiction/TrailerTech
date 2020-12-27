#!/usr/bin/env python3

import os
import shutil
import youtube_dl
import requests

from utils import logger
from downloaders import DL_DIRECTORY

log = logger.get_log(__name__)

class Downloader():
    def __init__(self):
        self._createTempDir()

    def cleanUp(self):
        for filename in os.listdir(DL_DIRECTORY):
            file_path = os.path.join(DL_DIRECTORY, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except OSError as e:
                log.warning('Failed to remove: {} ERROR: {}'.format(filename, e))
                continue
            log.debug('Removed {}'.format(file_path))

    def _moveTo(self, source, destination):
        log.info('Download Complete Moving {} to {}'.format(os.path.basename(source), os.path.dirname(destination)))
        # check for destination directory
        if not os.path.isdir(os.path.dirname(destination)):
            log.warning('Failed to move {} ERROR: {} does not exist.'.format(os.path.basename(source), os.path.dirname(destination)))
            return False

        # attempt to move the file
        try:
            # os.replace(source, destination)
            shutil.move(source, destination)
        except OSError as e:
            log.warning('Failed to move {} ERROR: {}'.format(os.path.basename(source), e))
            return False
        return True

    def _createTempDir(self):
        if not os.path.isdir(DL_DIRECTORY):
            os.mkdir(DL_DIRECTORY)

    def downloadYouTube(self, fileName, destinationDirectory, link):
        tempFilePath = os.path.join(DL_DIRECTORY, fileName)
        destinationPath = os.path.join(destinationDirectory, fileName)
        options = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]',
        'default_search': 'ytsearch1:',
        'restrict_filenames': 'TRUE',
        'prefer_ffmpeg': 'TRUE',
        'quiet': 'TRUE',
        'no_warnings': 'TRUE',
        'ignoreerrors': 'TRUE',
        'no_playlist': 'TRUE',
        'no_progress': 'TRUE',
        'logger': logger.get_log('YouTube-DL'),
        'outtmpl': tempFilePath
        }

        log.info('Attempting to download video: {} from "{}". Please Wait...'.format(fileName, link))
        try:
            with youtube_dl.YoutubeDL(options) as youtube:
                youtube.extract_info(link, download=True)
        except Exception as e:
            log.warning('Something went wrong while getting trailer from {}. ERROR: {}'.format(link, e))
            return False

        if os.path.isfile(tempFilePath):
            self._moveTo(tempFilePath, destinationPath)
            return True
        else:
            log.warning('Failed to download from {}'.format(link))
            return False

    def downloadApple(self, fileName, destinationDirectory, link):
        log.info('Attempting to download video at "{}". Please Wait...'.format(link))
        tempPath = os.path.join(DL_DIRECTORY, fileName)
        destinationPath = os.path.join(destinationDirectory, fileName)
        headers = {'User-Agent': 'Quick_time/7.6.2'}
        r = requests.get(link, stream=True, headers=headers)
        with open(tempPath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        if r.status_code == 200:
            self._moveTo(tempPath, destinationPath)
            return True
        else:
            log.warning('Failed to download from {}.'.format(link))
            return False
