import requests
from json import loads


def parse(url: str) -> dict:
    name = url.split('/')[3]
    link = f'https://api.kazanexpress.ru/api/shop/{name}?&order=ascending'
    response = requests.get(link)
    json_ = loads(response.text)
    answer = json_["payload"]

    return {
        'orders': answer["orders"],
        'reviews': answer["reviews"],
        'title': answer["title"],
        'name': name
    }

