import config
import requests
import models
from time import sleep
from random import randint
from models import Session, engine


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
        self.offset = randint(0, 50)
        self.wish_list = []
        self.black_list = []

    def search_user(self, city, sex, birth_year, relation, count=1):
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
        connection = engine.connect()

        while True:
            # пауза для исключения ошибки 'Too many requests per second'
            sleep(0.3)
            self.offset += count
            params = {
                'count': count,
                'sex': sex,
                'birth_year': birth_year,
                'has_photo': 1,
                'hometown': city,
                'relation': relation,
                'offset': self.offset
            }
            try:
                params = {**params, **self.params}
                resp = requests.get(url=endpoint, params=params)

                if resp.status_code != 200:
                    raise ConnectionError

                # обработка ошибок VK
                if resp.json().get('error'):
                    resp_error = resp.json()['error']['error_code'], \
                                 resp.json()['error']['error_msg']
                    error_msg = f'Error code: {resp_error[0]}\n' \
                                f'Error message: {resp_error[1]}'
                    print(error_msg)
                    continue

                # если пришел пустой ответ, то пропускаем цикл
                if not resp.json()['response']['items']:
                    continue

            except ConnectionError:
                print('Connection error')
                continue
            else:
                person = resp.json()['response']['items'][0]
                # если профиль закрытый, то пропускаем
                if person['is_closed']:
                    continue

            # если пользователь в игнор-листе, то пропускаем
            if session.query(
                    models.BlackList.vk_user_id)\
                    .filter_by(vk_user_id=person['id'])\
                    .first() is not None:
                continue

            photo_profile = self.get_photos_from_profile(person['id'])

            return person['first_name'], person['last_name'], \
                f'{config.base_profile_url}{person["id"]}', \
                photo_profile

    def get_user_info(self, user_id, mode=0):
        """
        Посылает api запрос, используя метод users.get и запрашивает
        информацию о пользователе
        mode: флаг для режима поиска (0 - по умолчанию,
        1 - возвращает только имя (необходимо для начального диалога))

        :param user_id: int
        :param mode: int
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

            # if data.get('city', None) is None:
            #     # если город не указан в профиле
            #     # то получаем его из списка городов VK
            #     params = {'user_ids': user_id,
            #               'country_id': 1,
            #               'need_all': 0
            #               }
            #     res = requests.get(url=f'{config.base_url}database.getCities',
            #                        params={**params, **self.params}).json()
            #
            #     cities = [s['title'] for s in res['response']['items']]
            #     # выбираем город
            #     city = choice(cities)
            # else:

            if data.get('city'):
                city = data.get('city').get('title')
            else:
                city = None

            # Дата рождения
            bdate = data.get('bdate')
            if len(bdate) > 6:
                # bdate = int(data.get('bdate').split('.')[2])
                bdate = int(bdate[-4:])
            else:
                bdate = None

            # Пол (выбираем противоположный)
            sex = (1, 2)[data.get('sex') == 1]

            # Семейное положение
            relation = data.get('relation')
            # if relation is None:
            # выбираем рандомно из кодов ВК
            #    relation = randint(0, 8)

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
        sleep(0.3)
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

        except ConnectionError:
            print('Connection error')

    