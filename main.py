import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import os


TUTULU_URL = 'https://tululu.org'


def check_for_redirect(response):
    """Функция для проверки перенаправлений запроса
    Args:
        response (requests.models.Response): Запрос.
    """
    print(response.history, response.url)
    if response.history:
        raise requests.HTTPError


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
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

    filename = sanitize_filename(f'{filename}.txt')
    path_to_file = os.path.join(folder, filename)

    with open(path_to_file, 'w') as file:
        file.write(response.text)

    return path_to_file


def download_book(book_id):
    page_url = ''.join([TUTULU_URL, '/b', str(book_id), '/'])
    response = requests.get(page_url)

    response.raise_for_status()
    # check_for_redirect(response)

    soup = BeautifulSoup(response.text, 'lxml')
    title_and_autor = soup.find('h1').text.split('::')
    title = f'{book_id}. {title_and_autor[0].strip()}' # Заголовок
    # if len(title_and_autor) > 1:
    #     autor = title_and_autor[-1].strip()  # Автор

    # oup.find('img', class_='attachment-post-image')['src']
    # soup.find('div', class_='entry-content')

    txt_url = ''.join([TUTULU_URL, '/txt.php?id=', str(book_id)])
    download_txt(txt_url, title, folder='books/')


def main():
    for book_id in range(1, 11):
        try:
            download_book(book_id)

        except requests.exceptions.HTTPError:
            print(f'книги с id={book_id} нет')
            pass


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    main()
