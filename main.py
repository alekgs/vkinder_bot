import vk_apps
import vk_bot
import models
from models import Session, engine
from vk_api.longpoll import VkEventType
from art import tprint
from datetime import datetime as dt

# заставка для консоли)
tprint('VKinder Bot')


def main():
    dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
    print(f'\n{dtime}: service started...', end='')

    vk_api = vk_apps.VkApi()
    vkbot = vk_bot.VKBot()

    session = Session()
    connection = engine.connect()

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

            vkbot.send_msg(event.user_id, "Добавлено в Игнор-лист")
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
                    f_name = vk_api.get_user_info(event.user_id, 1)
                    print(f'{dtime}: user id{event.user_id} connected')

                    vkbot.send_msg(event.user_id,
                                   f'Привет, {f_name}!\n'
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

                    data = vk_api.get_user_for_bot(event.user_id)

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

                        flag_favorite, flag_black = True, True

                    else:
                        dtime = dt.now().strftime('%d.%m.%Y %H:%M:%S')
                        print(f'{dtime}: VK service error')
                        vkbot.send_msg(event.user_id, message='Ошибка сервиса')

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

                else:
                    vkbot.send_msg(event.user_id, "Неизвестная команда")


if __name__ == '__main__':
    main()
