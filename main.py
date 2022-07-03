from pprint import pprint
from datetime import date
from io import BytesIO
from collections import OrderedDict
from time import sleep

import requests
import yadisk
import tqdm

from settings import tokens
from logger import logger


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def upload(self, data: list, directory: str) -> list:
        disk = yadisk.YaDisk(token=self.token)
        if not disk.is_dir(directory):
            disk.mkdir(directory)
            logger(
                f'На Яндекс.Диске успешно создана директория "/{directory}"'
            )
        else:
            logger(
                f'Директория с именем "{directory}" уже существует'
            )
        files_list = list()
        for record in tqdm.tqdm(data):
            photos_url = requests.get(record['url'])
            if (
                    photos_url.status_code == 200
                    and not disk.is_file(f'{directory}/'
                                         + record['file_name'])
            ):
                logger(
                    f'Начало загрузки файла {record["file_name"]}'
                )
                disk.upload(
                    BytesIO(photos_url.content),
                    f'{directory}/' + record['file_name']
                )
                files_list.append(record)
                logger(
                    f'Файл "{record["file_name"]}" успешно загружен на диск'
                )
            else:
                logger(
                    f'Error, файл "{record["file_name"]}" уже сущетвует '
                    f'или удален по этой ссылке {record["url"]}'
                )
        return files_list


class VK:

    def __init__(
            self,
            access_token: str,
            version: str = '5.131'
    ):
        self.token = access_token
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self, users_ids):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': users_ids}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_users_photos_from_album(
            self,
            owner_id: str,
            album: str = 'profile',
            number_photos: int = 5
    ) -> dict:
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': owner_id, 'album_id': album, 'extended': 1}
        response = requests.get(url, params={**self.params, **params}).json()
        # pprint(response)
        # if response.status_code != 200:
        #     logger(f'Error, фотографии у пользователя {owner_id} не найдены')
        #     return {}

        if 'error' in response:
            error = response['error']
            logger(f'Error: {error["error_code"]}, {error["error_msg"]}')
            return {}

        photos = dict()
        for photo in response['response']['items'][:number_photos]:
            likes = photo['likes']['count']
            if likes not in photos:
                photos[likes] = []
            max_photo = self._find_max_size(photo['sizes'])
            photos[likes].append({
                'date': str(date.fromtimestamp(photo['date'])),
                'url': max_photo['url'],
                'size': max_photo['type']
            })
        logger(
            f'От пользователя с id "{owner_id}" '
            f'получено {len(photos)}/{number_photos} фотографий'
        )
        return photos

    @staticmethod
    def _find_max_size(photos_sizes: list) -> dict:
        sizes_dict = OrderedDict.fromkeys('smxyzw')
        for photos_size in photos_sizes:
            size_type = photos_size['type']
            if size_type in sizes_dict:
                sizes_dict[size_type] = photos_size

        max_size = sizes_dict.popitem()[1]
        while not max_size:
            max_size = sizes_dict.popitem()[1]
        assert type(max_size) == dict

        return max_size


def set_photos_name(data: dict) -> list:
    photos_list = list()
    for count_like, records in data.items():
        if len(records) > 1:
            for record in records:
                name = f'{count_like}_{record["date"]}.jpg'
                photos_list.append({
                    'file_name': name,
                    'size': record['size'],
                    'url': record['url']
                })
        else:
            photos_list.append({
                'file_name': f'{count_like}.jpg',
                'size': records[0]['size'],
                'url': records[0]['url']
            })

    return photos_list


def create_directory_name_for_user(user: dict) -> str:
    user = user['response'][0]
    return f'{user["first_name"]}_{user["last_name"]}'


def main():
    while True:
        vk = VK(tokens['vk'])
        my_disk = YaUploader(tokens['yadisk'])
        user_id = input(
            'Введите id пользователя vk:\n'
        )
        if not vk.users_info(user_id)['response']:
            print(f'Пользователь "{user_id}" не найден')
            continue
        sleep(.3)

        photos_from_user = set_photos_name(
            vk.get_users_photos_from_album(user_id)
        )
        if not photos_from_user:
            print('Фотографии пользователя недоступны')
            continue
        sleep(.3)

        user_directory = create_directory_name_for_user(
            vk.users_info(user_id)
        )

        uploaded_files = my_disk.upload(photos_from_user, user_directory)

        print(f'Загруженые файлы в папку {user_directory}:')
        pprint(uploaded_files)

        command = input('Хотите продолжить?\n(y/n)\n')
        if command == 'y':
            continue
        else:
            break


if __name__ == '__main__':
    main()
