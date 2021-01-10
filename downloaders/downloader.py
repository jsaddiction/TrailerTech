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
        'default_search': 'auto',
        'restrictfilenames': True,
        'prefer_ffmpeg': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'noplaylist': True,
        'noprogress': True,
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

        try:
            with requests.get(link, stream=True, headers=headers, timeout=5) as response:
                response.raise_for_status()
                if int(response.headers.get('Content-length')) < 1000000:
                    log.warning('File too small. URL: {} Content-Length: {}'.format(link, response.headers.get('Content-Length')))
                    return False
                with open(tempPath, 'wb') as tempFile:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        tempFile.write(chunk)

        except requests.exceptions.HTTPError as e:
            log.warning('Encountered an HTTP error while downloading from: {} ERROR: {}'.format(link, e))
            return False
        except IOError as e:
            log.warning('Encountered an error while writing to disk. File: {} ERROR: {}'.format(tempPath, e))
            return False

        if self._moveTo(tempPath, destinationPath):
            self.cleanUp()
            return True

    def download(self, fileName, destinationDirectory, link):
        if 'apple' in link.lower():
            return self.downloadApple(fileName, destinationDirectory, link)
        elif 'youtube' in link.lower() or 'vimeo' in link.lower():
            return self.downloadYouTube(fileName, destinationDirectory, link)
