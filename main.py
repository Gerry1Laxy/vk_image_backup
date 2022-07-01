from pprint import pprint
from datetime import date

import requests

from settings import tokens


class VK:

    def __init__(
            self,
            access_token: str,
            version: str = '5.131'
    ):
        self.token = access_token
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    # def users_info(self):
    #     url = 'https://api.vk.com/method/users.get'
    #     params = {'user_ids': self.id}
    #     response = requests.get(url, params={**self.params, **params})
    #     return response.json()

    def get_users_photos_from_album(
            self,
            owner_id: str,
            album: str = 'profile',
            number_photos: int = 5
    ):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': owner_id, 'album_id': album, 'extended': 1}
        response = requests.get(url, params={**self.params, **params})
        photos = dict()
        pprint(response.json())
        for photo in response.json()['response']['items'][:number_photos]:
            likes = photo['likes']['count']
            if likes not in photos:
                photos[likes] = []
            photos[likes].append({
                'date': str(date.fromtimestamp(photo['date'])),
                'url': photo['sizes'][-1]['url'],
                'size': photo['sizes'][-1]['type']
            })
        return photos


if __name__ == '__main__':
    user_id = '1'
    vk = VK(tokens['vk'])
    pprint(vk.get_users_photos_from_album(user_id))
