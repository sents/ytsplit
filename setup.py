# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name = 'ytsplit',
    version = '0.1',
    description = 'A script to download and split up videos from youtube',
    long_description = \
    '''
    This script is supposed to be used to import audios from youtube to a music collection,
    splitting up the audion at times given in a timstamp string as used on youtube
    ''',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    license = 'The Unlicense',
    install_requires = ['youtube-dl'],
    author = 'sents',
    author_email = 'finn@krein.moe',
    url = 'https://github.com/sents/ytsplit',
    packages = ['ytsplit'],
    entry_points = { 'console_scripts' : ['ytsplit = ytsplit.ytsplit:main'] }
)
