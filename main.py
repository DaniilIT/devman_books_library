import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pathlib import Path


TUTULU_URL = 'https://tululu.org/txt.php?id='


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def load_book(book_id):
    url = ''.join([TUTULU_URL, str(book_id)])

    response = requests.get(url, verify=False)
    response.raise_for_status()
    check_for_redirect(response)

    return response.text


def main():
    books_dir = Path.cwd().joinpath('books')
    Path(books_dir).mkdir(exist_ok=True)

    for book_id in range(1, 11):
        try:
            book_text = load_book(book_id)

            with open(books_dir.joinpath(f'id{book_id}.txt'), 'w') as file:
                file.write(book_text)

        except requests.exceptions.HTTPError:
            print(f'книги с id={book_id} нет')
            pass


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # disable warnings
    main()
