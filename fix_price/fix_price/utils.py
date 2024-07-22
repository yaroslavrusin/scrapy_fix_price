from pathlib import Path
from typing import Iterable

from fix_price.items import FixPriceItem


def add_section(item: FixPriceItem, category: dict) -> None:
    """Рекурсивно проходимся по категориям"""
    item.section.append(category['title'])
    if category.get('parentCategory') is None:
        return
    else:
        category = category['parentCategory']
        return add_section(item, category)


def get_urls() -> Iterable[str]:
    """Открываем файл со ссылками на категории товаров"""
    base_dir = Path(__name__).absolute().parent.parent
    with open(base_dir / 'urls', mode='r', encoding='utf-8') as file:
        for url in file:
            yield url
