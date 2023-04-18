import config
import requests
import models
from models import Session
# from time import sleep
# from random import randint


class VkApi:
    """
    Класс для работы с  VK API
    """

    def __init__(self):
        self.token = config.access_token
        self.params = {
            'access_token': self.token,
            'v': config.vkapi_version
        }
        self.offset = 0
        self.wish_list = []
        self.black_list = []

    def search_user(self, city, sex, birth_year, relation, count=30):
        """
        Посылает API запрос, используя VK API метод users.search,
        с параметрами 'count', 'sex', 'birth_year', 'has_photo', 'hometown',
        'offset'. Если профиль пользователя закрытый или пользователь находится
        в списке игнорирования (black list) или в избранном, то пользователь
        пропускается.
        Возвращает имя, фамилию, ссылку на профиль и 3 фото (полученных методом
        get_photos_from_profile())
        """
        endpoint = f'{config.base_url}users.search'

        session = Session()

        params = {
            'count': count,
            'sex': sex,
            'birth_year': birth_year,
            'has_photo': 1,
            'hometown': city,
            'relation': relation,
            'offset': self.offset
        }
        params = {**params, **self.params}
        resp = requests.get(url=endpoint, params=params)

        if resp.json().get('error'):
            resp_error = resp.json()['error']['error_code'], \
                resp.json()['error']['error_msg']
            error_msg = f'Error code: {resp_error[0]}\n' \
                        f'Error message: {resp_error[1]}'
            print(error_msg)
            return ('Error', )

        for row in resp.json()['response']['items']:
            self.offset += 1
            # если профиль закрытый, то пропускаем
            if row['is_closed']:
                continue

            # если пользователь в игнор-листе, то пропускаем
            if session.query(
                    models.BlackList.vk_user_id)\
                    .filter_by(vk_user_id=row['id'])\
                    .first() is not None:
                continue

            # если пользователь в избранном, то пропускаем
            if session.query(
                    models.FavoriteUser.vk_user_id)\
                    .filter_by(vk_user_id=row['id'])\
                    .first() is not None:
                continue

            photo_profile = self.get_photos_from_profile(row['id'])

            return row['first_name'], row['last_name'], \
                f'{config.base_profile_url}{row["id"]}', \
                photo_profile

    def get_user_info(self, user_id):
        """
        Посылает api запрос, используя метод users.get и запрашивает
        информацию о пользователе
        mode: флаг для режима поиска (0 - по умолчанию,
        1 - возвращает только имя (необходимо для начального диалога))

        :param user_id: int
        :return: str
        """

        endpoint = f'{config.base_url}users.get'
        params = {
            'user_ids': user_id,
            'fields': 'first_name, last_name, bdate, sex, city, relation'
        }
        try:
            response = requests.get(url=endpoint,
                                    params={**params, **self.params})

            if response.status_code != 200:
                raise ConnectionError

        except ConnectionError:
            print('Connection error')

        else:
            data = response.json()['response'][0]

            # Город
            if data.get('city'):
                city = data.get('city').get('title')
            else:
                city = None

            # Дата рождения
            bdate = data.get('bdate')
            if len(bdate) > 6:
                bdate = int(bdate[-4:])
            else:
                bdate = None

            # Пол (выбираем противоположный)
            sex = (1, 2)[data.get('sex') == 1]

            # Семейное положение
            relation = data.get('relation')

            # Имя
            name = data.get('first_name')
            if not name:
                name = data.get('last_name')

            return name, city, sex, bdate, relation

    def get_photos_from_profile(self, user_id):
        """
        Получает user_id и возвращает 3 фото с наибольшим количеством
        лайков и комментариев
        :param user_id: int
        :return: str
        """
        # пауза для исключения ошибки 'Too many requests per second'
        # sleep(0.2)

        res = []

        endpoint = f'{config.base_url}photos.get'
        params = {'owner_id': user_id,
                  'album_id': 'profile',
                  'extended': 1, }

        try:
            resp = requests.get(endpoint, params={**self.params,
                                                  **self.params,
                                                  **params})
            resp.raise_for_status()

            if resp.status_code != 200:
                raise ConnectionError

        except ConnectionError:
            print('Connection error')

        else:
            # критерии отбора фото (весА)
            # likes:comments 3:1
            like_score = 1
            comm_score = 3

            sort_photos = \
                lambda x: \
                (
                 x['likes']['count'], x['comments']['count']
                )[x['likes']['count'] * like_score <=
                  x['comments']['count'] * comm_score]

            result = sorted(resp.json()['response']['items'],
                            key=sort_photos, reverse=True)

            for foto in result:
                res.append(f"photo{foto['owner_id']}_{foto['id']}")
                if len(res) == 3:
                    break

            return ','.join(res)
