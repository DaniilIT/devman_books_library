import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path, PurePath
from sys import stderr
import logging
from time import sleep
import json

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
                    - 'image_src'     - ссылка на изображение книги,
                    - 'genres'        - список жанров книги,
                    - 'comments'      - список комментариев книги.
    """
    title_and_author = soup.select_one('h1').text.split('::')
    genres_soup = soup.select('span.d_book a')
    comments_soup = soup.select('div.texts span.black')

    book = {
        'title': title_and_author[0].strip(),
        'author': title_and_author[-1].strip(),
        'image_src': unquote(soup.select_one('div.bookimage img')['src']),
        'genres': list(map(lambda x: x.text, genres_soup)),
        'comments': list(map(lambda x: x.text, comments_soup)),
    }

    return book


def parse_category_page(soup):
    """Функция парсит данные со страницы.
    Args:
        soup (bs4.BeautifulSoup): html-контент страницы
    Returns:
        book_srcs (list[str]): ссылки на книги в одной категории
    """
    category_books = soup.select('table.d_book')
    book_srcs = list(map(lambda book: unquote(book.select_one('td > a')['href']), category_books))
    return book_srcs


def main():
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )
    logging.basicConfig(filename='app.log', filemode='w')

    book_urls = []

    for number_page in range(1, 2):
        try:
            category_page_url = urljoin(TUTULU_URL, f"/l55/{number_page}/")
            response = requests.get(category_page_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            book_srcs = parse_category_page(soup)
            book_urls.extend(list(map(lambda book_src: urljoin(category_page_url, book_src), book_srcs)))

        except requests.exceptions.HTTPError:
            stderr.write(f"отсутствует на сайте.\n")
            logging.warning(f"отсутствует на сайте.")

        except requests.exceptions.ConnectionError:
            stderr.write(f"Соединение с сервером прервано.\n")
            logging.warning(f"Соединение с сервером прервано.")
            sleep(5)

    books = []

    for book_url in book_urls:
        book_id = int(urlparse(book_url).path[2:-1])
        while True:
            try:
                response = requests.get(book_url)
                response.raise_for_status()
                check_for_redirect(response)

                soup = BeautifulSoup(response.text, 'lxml')
                book = parse_book_page(soup)

                download_txt(urljoin(book_url, f"/txt.php"), book_id, book['title'])
                download_image(urljoin(book_url, book['image_src']))

                books.append(book)
                break

            except requests.exceptions.HTTPError:
                stderr.write(f"Книга №{book_id} отсутствует на сайте.\n")
                logging.warning(f"Книга №{book_id} отсутствует на сайте.")
                break

            except requests.exceptions.ConnectionError:
                stderr.write(f"Соединение с сервером на книге №{book_id} прервано.\n")
                logging.warning(f"Соединение с сервером на книге №{book_id} прервано.")
                sleep(5)

    with open("books.json", "w") as f:
        json.dump(books, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
