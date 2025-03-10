"""Модуль парсинга."""

from __future__ import annotations

from curl_cffi import requests
from lxml import etree


class NoDataForThisDayError(Exception):
    """Исключение, вызываемое в случае если информация по этому дню не найдена."""

    def __str__(self) -> str:
        """Возвращает описание ошибки."""
        return "Информация по этой дате не найдена, возможно она пока не загружена."


class UnknownError(Exception):
    """Исключение, вызываемое в случае если произошла неизвестная ошибка."""

    def __init__(self, e: Exception) -> None:
        """Инициализация класса."""
        self.e = e

    def __str__(self) -> str:
        """Возвращает описание ошибки."""
        return f"Во время парсинга произошла неизвестная ошибка: {self.e}."  # noqa: RUF001


class CAI:
    """Объект разговора о важном."""  # noqa: RUF002

    def __init__(
        self,
        title: str,
        image_url: str,
        str_date: str,
        videos_urls: list | None = None,
        plakat_url: str | None = None,
     ) -> None:
        """Инициализация объекта."""
        self.title = title
        self.image_url = image_url
        self.str_date = str_date

        self.plakat_url = plakat_url

        if videos_urls is None:
            videos_urls = []

        self.videos_urls = videos_urls

    def __str__(self) -> str:
        """Возвращает строковое представление данных."""
        return (
            "{"
            f'"title": "{self.title}", '
            f'"str_date": "{self.str_date}", '
            f'"image_url": "{self.image_url}", '
            f'"plakat_url": "{self.plakat_url}", '
            f'"videos_urls": {self.videos_urls}'
            "}"
        ).replace("'", '"')


class CAIParser:
    """Класс парсера.

    Conversations | Разговоры
    About         | О
    Important     | Важном
    """  # noqa: RUF002

    def __init__(self) -> None:
        """Инициализация парсера."""
        # Инициализация сессии
        self.s = requests.Session()

        # Инициализация парсера html
        self.htmlparser = etree.HTMLParser()

    def get_info(self, date: str) -> CAI:
        """Информация о товаре."""  # noqa: RUF002
        # Запрос к сайту
        url = f"https://xn--80aafadvc9bifbaeqg0p.xn--p1ai/{date}"
        r = self.s.get(url)

        if r.status_code == 200:  # noqa: PLR2004
            # Парсим HTML
            tree = etree.HTML(r.content, self.htmlparser)

            # Название
            title = tree.xpath("/html/body/main/section[1]/div[1]/h1")[0].text

            # Дата в формате строки
            str_date = tree.xpath("/html/body/main/section[1]/div[1]/p[1]")[0].text

            # Ссылка на изображение
            image_url = (
                "https://разговорыоважном.рф" +
                tree.xpath("/html/body/main/section[1]/div[2]/img/@src")[0]
            )

            # Используем set, чтобы исключить повторы
            urls = set()

            # Проходимся по всем элементам с атрибутом href  # noqa: RUF003
            for i in tree.xpath("//@href"):
                # Таким образом проверяем не является ли файл статичным
                if date in i:
                    if "http" in i:
                        urls.add(i)
                    else:
                        urls.add("https://разговорыоважном.рф" + i)

            # Ссылка на плакат
            plakat_url_template = f"https://разговорыоважном.рф/{date}/plakat.jpg"
            plakat_url = plakat_url_template if plakat_url_template in urls else None

            # Ссылки на видеоролики
            videos_urls = sorted([url for url in list(urls) if ".mp4" in url])

            return CAI(
                title,
                image_url,
                str_date,
                videos_urls,
                plakat_url,
            )

        if r.status_code == 404:  # noqa: PLR2004
            raise NoDataForThisDayError

        raise UnknownError(r.status_code)
