#!/usr/bin/env python3

from argparse import ArgumentParser

def get_arguments(name, description, version):
    parser = ArgumentParser(description=description)

    # Add basic arguments
    parser.add_argument('-v', '--version', action='version', version=version, help='Show the name and version number')
    parser.add_argument('-r', '--recursive', action='store_true', dest='recursive', help='Scan all directories within the path given', default=False)
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', help='Only log results of scan and critical errors to screen. (useful for cron jobs)', default=False)
    parser.add_argument('-d', '--directory', metavar='directory', dest='directory', help='Directory to scan. Use -r flag to scan entire library.', default=None)
    parser.add_argument('--use_threads', action='store_true', dest='threads', help='Speed up scans with threading', default=False)
    parser.add_argument('--delete_corrupt', action='store_true', dest='deleteCorrupt', help='Remove trailers with corruption and replace', default=False)

    # Create argument groups
    title_year_group = parser.add_argument_group('Movie Title Year info')
    id_group = parser.add_argument_group('IMDB, TMDB id info')

    # Create a group for specific movie data
    title_year_group.add_argument('-y', metavar='year', dest='year', help='Release year of the movie', type=int, default=None)
    title_year_group.add_argument('-t', metavar='title', dest='title', help='Movie title', default=None)
    id_group.add_argument('-tmdb', metavar='TMDB id', dest='tmdb', help='TMDB id of the movie', type=int, default=None)
    id_group.add_argument('-imdb', metavar='IMDB id', dest='imdb', help='IMDB id of the movie', default=None)

    return parser.parse_args()
