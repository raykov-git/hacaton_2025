from abc import ABC, abstractmethod
import logging

LOGGER = logging.getLogger(__name__)

class AbstractBot(ABC):
    """
    Абстрактный класс для бота (+- любого)
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def api(self) -> str:
        """
        Возвращает стандартное приветственное сообщение API.
        Returns:
            str: Текст приветствия.
        """
        pass

    @abstractmethod
    def process_message(self, user_text: str) -> str:
        """
        Обработка входящего сообщения пользователя.
        Args:
            user_text (str): Текст запроса.
        Returns:
            str: Ответ бота или сообщение об ошибке.
        Raises:
            ValueError: Если запрос пустой.
        """
        pass