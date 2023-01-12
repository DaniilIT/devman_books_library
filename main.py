import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path, PurePath
import argparse
from sys import stderr
import logging
from time import sleep


TUTULU_URL = 'https://tululu.org'


def check_for_redirect(response):
    """Функция для проверки перенаправлений запроса.
    Args:
        response (requests.models.Response): Запрос.
    """
    if response.history:
        raise requests.HTTPError


def download_txt(url, book_id, book_title, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Ссылка на текст, который хочется скачать.
        book_id (int): Номер книги на сайте.
        book_title (str): Название книги.
        folder (str): Папка, куда сохранять.
    """
    params = {'id': book_id}
    response = requests.get(url, params=params, verify=False)
    response.raise_for_status()
    check_for_redirect(response)

    books_dir = Path.cwd().joinpath(folder)
    Path(books_dir).mkdir(exist_ok=True)

    filename = sanitize_filename(f"{book_id}. {book_title}.txt")
    file_path = PurePath(folder, filename)
    with open(file_path, 'w') as file:
        file.write(response.text)


def download_image(url):
    """Функция для скачивания изображений.
    Args:
        url (str): Ссылка на изображение, которое хочется скачать.
    """
    response = requests.get(url, verify=False)
    response.raise_for_status()

    images_dir = Path.cwd().joinpath('images/')
    Path(images_dir).mkdir(exist_ok=True)

    filename = sanitize_filename(urlparse(url).path.split('/')[-1])
    file_path = PurePath('images/', filename)
    with open(file_path, 'wb') as file:
        file.write(response.content)


def parse_book_page(soup):
    """Функция парсит данные со страницы.
    Args:
        soup (bs4.BeautifulSoup): html-контент страницы
    Returns:
        book (dict): словарь с данными о книге:
                    - 'title'         - название книги,
                    - 'author'        - автор книги,
                    - 'image_url' - ссылка на изображение книги,
                    - 'genres'        - список жанров книги,
                    - 'comments'      - список комментариев книги.
    """
    title_and_author = soup.find('h1').text.split('::')
    genres_soup = soup.find('span', class_='d_book').find_all('a')
    comments_soup = soup.find_all('div', class_='texts')

    book = {
        'title': title_and_author[0].strip(),
        'author': title_and_author[-1].strip(),
        'image_url': unquote(soup.find('div', class_='bookimage').find('img')['src']),
        'genres': list(map(lambda x: x.text, genres_soup)),
        'comments': list(map(lambda x: x.find('span', class_='black').text, comments_soup)),
    }

    return book


def create_parser():
    """Функция производит синтаксический анализ командной строки
    """
    parser = argparse.ArgumentParser(
        description='Программа скачивает книги с сайта https://tululu.org'
    )
    parser.add_argument(
        '--start_id',
        help='Номер страницы, с которой начнется скачивание книг',
        default=1,
        type=int
    )
    parser.add_argument(
        '--end_id',
        help='Номер страницы, на которой закончится скачивание книг',
        default=10,
        type=int
    )
    return parser


def main():
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )
    logging.basicConfig(filename='app.log', filemode='w')
    args = create_parser().parse_args()

    for book_id in range(args.start_id, args.end_id + 1):
        while True:
            try:
                page_url = urljoin(TUTULU_URL, f"/b{book_id}/")
                response = requests.get(page_url)
                response.raise_for_status()
                check_for_redirect(response)

                soup = BeautifulSoup(response.text, 'lxml')
                book = parse_book_page(soup)

                download_image(urljoin(page_url, book['image_url']))
                download_txt(urljoin(page_url, f"/txt.php"), book_id, book['title'])
                break

            except requests.exceptions.HTTPError:
                stderr.write(f"Книга №{book_id} отсутствует на сайте.\n")
                logging.warning(f"Книга №{book_id} отсутствует на сайте.")
                break

            except requests.exceptions.ConnectionError:
                stderr.write(f"Соединение с сервером на книге №{book_id} прервано.\n")
                logging.warning(f"Соединение с сервером на книге №{book_id} прервано.")
                sleep(5)


if __name__ == '__main__':
    main()
