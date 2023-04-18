import vk_apps
import vk_bot
import models
from models import Session, engine
from vk_api.longpoll import VkEventType
from art import tprint
from datetime import datetime as dt

# заставка для консоли)
tprint('VKinder Bot')

# bot_user_info = {}


def main():
    dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
    print(f'\n{dtime}: service started...', end='')

    vk_api = vk_apps.VkApi()
    vkbot = vk_bot.VKBot()

    session = Session()
    connection = engine.connect()

    bot_user_info = {}
    stack = []

    flag_favorite = False
    flag_black = False

    print('OK')

    def add_user_to_db(bot_user_id, flag_list):
        """
        Добавляет информацию о пользователе в Избранное или Игнор-лист
        flag_list True - добавляет в Избранное
        flag_list False - добавляет в Игнор-лист
        :param bot_user_id: bot_user_id
        :param flag_list: Boolean
        :return: Boolean
        """
        nonlocal flag_favorite
        nonlocal flag_black

        first_name, last_name, url, user_attachment = stack.pop()
        vk_user_id = int(url.split('id')[1])

        if flag_list and models.check_if_match_exists(vk_user_id)[0] is None:
            flag_favorite = False
            models.add_new_match_to_favorites(
                    vk_user_id, bot_user_id,
                    first_name,
                    last_name, url
                    )
            models.add_photo_of_the_match(
                    user_attachment,
                    vk_user_id,
                    bot_user_id
                    )

            dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')

            print(f'{dtime}: user id{event.user_id} '
                  f'add id{vk_user_id} to the Favorites')

            vkbot.send_msg(event.user_id, "Добавлено в Избранное")

            return True

        elif not flag_list and \
                models.check_if_match_exists(vk_user_id)[1] is None:

            flag_black = False

            models.add_new_match_to_black_list(
                    vk_user_id, bot_user_id,
                    first_name,
                    last_name, url
                    )
            models.add_photo_of_the_match(
                    user_attachment,
                    vk_user_id,
                    bot_user_id
                    )

            vkbot.send_msg(event.user_id, "Добавлено в Игнор-лист")

            dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
            print(f'{dtime}: user id{event.user_id} '
                  f'add id{vk_user_id} to the BlackList')

            return True
        return False

    for event in vkbot.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                message = event.text.lower()

                if message in ('start', 'hi', 'привет', 'старт'):
                    dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
                    print(f'{dtime}: user id{event.user_id} connected')

                    # запросить всю инфу от пользователя бота,

                    res = vk_api.get_user_info(event.user_id, 1)
                    name_bot_user, city, sex, bdate, relation = res

                    # заполняем словарь для поиска
                    bot_user_info['city'] = city
                    bot_user_info['sex'] = sex
                    bot_user_info['relation'] = relation
                    bot_user_info['bdate'] = bdate

                    vkbot.send_msg(event.user_id, f'Привет, {name_bot_user}!')

                    # добавляем пользователя в БД, если его там нет

                    if models.check_if_bot_user_exists(event.user_id) is None:
                        models.add_bot_user(event.user_id)

                    # если отсутствуют город и дата рождения
                    if not city:
                        # проверяем city в словаре
                        city = bot_user_info.get('city')
                        if not city:
                            vkbot.send_msg(
                                event.user_id,
                                f'❗ Не указан город в Вашем профиле\n'
                                f'Наберите "город название_города"\n'
                                f'Или укажите его в Вашем профиле ВК'
                                )
                    elif not bdate:
                        # проверяем ДР в словаре
                        bdate = bot_user_info.get('bdate')
                        if not bdate:
                            vkbot.send_msg(
                                event.user_id,
                                f'❗ Не указана дата рождения в Вашем профиле\n'
                                f'Наберите "год рождения год_рождения "',
                                f'(4 цифры).\n'
                                f'Или укажите его в Вашем профиле ВК')
                    else:
                        vkbot.send_msg(event.user_id,
                                       f'Нажми "Поиск" для старта')

                elif message == "избранное":
                    for user in models.show_all_favorites(event.user_id):
                        msg = f'{user[0]} {user[1]}\n{user[2]}'

                        vkbot.send_msg(event.user_id,
                                       message=msg,
                                       attachment=user[3])

                elif message == "игнор-лист":
                    for user in models.show_all_blacklisted(event.user_id):
                        msg = f'{user[0]} {user[1]}\n{user[2]}'

                        vkbot.send_msg(event.user_id,
                                       message=msg,
                                       attachment=user[3])

                elif message == "в избранное":
                    add_user_to_db(event.user_id, True)

                elif message == "игнорировать":
                    add_user_to_db(event.user_id, False)

                elif message == "поиск":
                    # читаем данные пользователя из словаря,
                    # созданного при старте бота

                    city = bot_user_info.get('city')
                    sex = bot_user_info.get('sex')
                    bdate = bot_user_info.get('bdate')
                    relation = bot_user_info.get('relation')

                    # поиск людей  в соответствии с данными
                    # пользователя бота
                    data = vk_api.search_user(city, sex, bdate, relation)

                    if data:
                        stack.append(data)
                        dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
                        print(f'{dtime}: '
                              f'user id{event.user_id} '
                              f'search result: {data}')

                        msg = f'{data[0]} {data[1]}\n{data[2]}'

                        vkbot.send_msg(event.user_id,
                                       message=msg,
                                       attachment=data[3])
                        # print(bot_user_info)
                        flag_favorite, flag_black = True, True

                    elif not data:
                        # если данных нет (пришел пустой список)
                        dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
                        print(f'{dtime}: Searching end, count records 0')
                        vkbot.send_msg(event.user_id,
                                       message='Совпадающих данных нет')

                    elif 'Error' in data:
                        dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
                        print(f'{dtime}: VK service error')
                        vkbot.send_msg(event.user_id,
                                       message='Ошибка сервиса VK')

                elif message == 'удалить игнор-лист':
                    models.delete_match_from_black_list(event.user_id)
                    dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
                    print(f'{dtime}: user id{event.user_id} '
                          f'cleared the Black list')
                    vkbot.send_msg(event.user_id, 'Игнор-лист очищен')

                elif message == 'удалить избранное':
                    models.delete_match_from_favorites_list(event.user_id)
                    dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
                    print(f'{dtime}: user id{event.user_id} '
                          f'cleared the Favorite list')
                    vkbot.send_msg(event.user_id, 'Избранное очищено')

                elif message.startswith('город '):
                    city = message.split()[1]
                    bot_user_info['city'] = city.title()
                    vkbot.send_msg(event.user_id,
                                   f'✅ Ваш город {city.title()}\n'
                                   f'Нажмите "Поиск" для продолжения')

                elif message.startswith('год рождения'):
                    year = message.split()[1]
                    bot_user_info['year'] = int(year)
                    vkbot.send_msg(event.user_id,
                                   f'✅ Год вашего рождения: {year}\n'
                                   f'Нажмите "Поиск" для продолжения')
                else:
                    vkbot.send_msg(event.user_id, "Неизвестная команда")


if __name__ == '__main__':
    main()
