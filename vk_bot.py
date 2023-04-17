import config
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll
from vk_api.utils import get_random_id


class VKBot:
    """
    Класс для чат-бота
    """

    def __init__(self):
        self.token = config.token_vkinder
        self.vk_session = VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk_session)
        self.keyboard = self.current_keyboard()

    def send_msg(self, user_id: int, message: str, attachment: str = None):
        """
        Посылает сообщение пользователю чата
        """
        self.vk_session.method('messages.send',
                               {'user_id': user_id,
                                'message': message,
                                'random_id': get_random_id(),
                                'keyboard': self.keyboard,
                                'attachment': attachment})

    @staticmethod
    def current_keyboard():
        """
        Клавиатура для чата
        """
        VK_kb = VkKeyboardColor
        keyboard = VkKeyboard(one_time=False)

        keyboard.add_button('Поиск', color=VK_kb.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('В избранное', color=VK_kb.POSITIVE)
        keyboard.add_button('Игнорировать', color=VK_kb.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Избранное', color=VK_kb.SECONDARY)
        keyboard.add_button('Игнор-лист', color=VK_kb.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('Удалить Избранное', color=VK_kb.SECONDARY)
        keyboard.add_button('Удалить Игнор-лист', color=VK_kb.SECONDARY)

        return keyboard.get_keyboard()
