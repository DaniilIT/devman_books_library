import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import os
from urllib.parse import urljoin, urlparse, unquote, urlsplit
import argparse


TUTULU_URL = 'https://tululu.org'


def check_for_redirect(response):
    """Функция для проверки перенаправлений запроса
    Args:
        response (requests.models.Response): Запрос.
    """
    # print(response.history, response.url)
    if response.history:
        raise requests.HTTPError


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Ссылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    response = requests.get(url, verify=False)

    response.raise_for_status()
    check_for_redirect(response)

    books_dir = Path.cwd().joinpath(folder)
    Path(books_dir).mkdir(exist_ok=True)

    filename = sanitize_filename(f"{filename}.txt")
    path_to_file = os.path.join(folder, filename)

    with open(path_to_file, 'w') as file:
        file.write(response.text)

    return path_to_file


def download_image(url):
    """Функция для скачивания изображений.
    Args:
        url (str): Ссылка на изображение, которое хочется скачать.
    Returns:
        str: Путь до файла, куда сохранено изображение.
    """
    response = requests.get(url, verify=False)
    response.raise_for_status()

    images_dir = Path.cwd().joinpath('images/')
    Path(images_dir).mkdir(exist_ok=True)

    filename = sanitize_filename(urlparse(url).path.split('/')[-1])
    path_to_file = os.path.join('images/', filename)

    with open(path_to_file, 'wb') as file:
        file.write(response.content)

    return path_to_file


def parse_book_page(soup):
    """Функция парсит данные со страницы.
    Args:
        soup (bs4.BeautifulSoup): html-контент страницы
    Returns:
        book_info (dict): словарь с данными о книге:
                        - 'title'         - название книги,
                        - 'author'        - автор книги,
                        - 'bookimage_url' - ссылка на изображение книги,
                        - 'genres'        - список жанров книги,
                        - 'comments'      - список комментариев книги.
    """

    book_info = dict()

    title_and_author = soup.find('h1').text.split('::')
    book_info['title'] = title_and_author[0].strip()
    if (len(title_and_author) > 1) and (len(title_and_author[-1].strip()) > 0):
        book_info['author'] = title_and_author[-1].strip()
    else:
        book_info['author'] = 'unknown'

    bookimage_url = unquote(soup.find('div', class_='bookimage').find('img')['src'])
    book_info['bookimage_url'] = urljoin(TUTULU_URL, bookimage_url)

    genres = soup.find('span', class_='d_book').find_all('a')
    book_info['genres'] = list(map(lambda x: x.text, genres))

    comments = soup.find_all('div', class_='texts')
    book_info['comments'] = list(map(lambda x: x.find('span', class_='black').text, comments))

    return book_info


def download_book(book_id):
    page_url = urljoin(TUTULU_URL, f'/b{book_id}/')
    response = requests.get(page_url)

    response.raise_for_status()
    check_for_redirect(response)

    soup = BeautifulSoup(response.text, 'lxml')
    book_info = parse_book_page(soup)

    download_image(book_info['bookimage_url'])

    print(book_info['title'])
    print(book_info['author'])
    print(*book_info['genres'])
    print(*book_info['comments'], sep='\n')
    print()

    booktext_url = urljoin(TUTULU_URL, f"/txt.php?id={book_id}")
    title = f"{book_id}. {book_info['title']}"
    download_txt(booktext_url, title, folder='books/')


def main(start_id, end_id):
    for book_id in range(start_id, end_id + 1):
        try:
            download_book(book_id)
        except requests.exceptions.HTTPError:
            print(f'книги с id={book_id} нет')
            pass


def createParser():
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


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    args = createParser().parse_args()

    main(args.start_id, args.end_id)
