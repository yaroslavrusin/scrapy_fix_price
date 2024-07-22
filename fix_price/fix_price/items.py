# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from dataclasses import dataclass
from enum import StrEnum


class MarketingTags(StrEnum):
    specialPrice = 'Спец цена'
    isFresh = 'Свежий'
    isNew = 'Новый'
    isPromo = 'Промо'
    adult = 'Для взрослых'
    isSeason = 'Сезон'
    isHit = 'Хит'
    isQRMark = 'QR-маркер'
    forbidden = 'forbidden'
    unit = 'Единичный'


@dataclass
class FixPriceItem:
    timestamp: int
    RCP: str
    url: str
    title: str
    marketing_tags: list[str]
    brand: str
    section: list[str]
    price_data: dict[str, float | str]
    stock: dict[str, bool | int]
    assets: dict[str, str | list[str]]
    metadata: dict[str, str]
    variants: int
