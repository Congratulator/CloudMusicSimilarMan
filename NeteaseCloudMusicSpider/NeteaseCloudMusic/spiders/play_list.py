# -*- coding: utf-8 -*-
import json
import os
import random

import pymongo
import scrapy

from NeteaseCloudMusic.items.PlayListItem import PlayListItem
from NeteaseCloudMusic.items.song import SongItem, ArtistItem, AlbumItem
from NeteaseCloudMusic.requests.WeapiRequest import WeapiRequest


class PlayListSpider(scrapy.Spider):
    name = 'play_list'
    allowed_domains = ['music.163.com']

    def start_requests(self):
        mongo_uri = self.settings.get('MONGO_URI'),
        mongo_db = self.settings.get('MONGO_DATABASE')
        client = pymongo.MongoClient(mongo_uri)
        db = client[mongo_db]
        for item in db['play_list'].find({'song_ids': {'$exists': False}}, {'id': 1}):
            yield WeapiRequest(
                url='http://music.163.com/weapi/v3/playlist/detail',
                formdata={
                    'id': item['id'],
                    'total': True,
                    'limit': 1000,
                    'n': 1000,
                    'offset': 0,
                },
                referer='http://music.163.com/m/playlist?id=%d' % item['id'],
                meta=dict(play_list_id=item['id']),
                ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12) AppleWebKit/%s' % os.urandom(random.randint(20, 50)),
            )

    def parse(self, response):
        resp = json.loads(response.body)
        if resp['code'] == 200 and 'playlist' in resp and 'tracks' in resp['playlist']:
            song_ids = []
            for song in resp['playlist']['tracks']:
                artist_ids = []
                song_ids.append(int(song['id']))
                for artist in song['ar']:
                    artist_ids.append(int(artist['id']))
                    yield ArtistItem(
                        id=int(artist['id']),
                        name=artist['name'],
                    )
                yield AlbumItem(
                    id=int(song['al']['id']),
                    name=song['al']['name'],
                    pic_url=song['al']['picUrl'],
                )
                yield SongItem(
                    id=int(song['id']),
                    name=song['name'],
                    album_id=int(song['al']['id']),
                    artist_ids=artist_ids,
                    mv=song['mv'],
                    publish_time=song['publishTime'],
                    copyright=bool(song['copyright']),
                    length=int(song['dt']),
                )
            yield PlayListItem(
                id=response.meta['play_list_id'],
                song_ids=song_ids,
            )
