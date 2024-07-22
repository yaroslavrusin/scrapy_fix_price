import json
from datetime import datetime
from functools import partial
from typing import Iterable
from urllib.parse import urlparse, urljoin

import scrapy
from scrapy import Request

from fix_price import settings
from fix_price import utils
from fix_price.items import FixPriceItem, MarketingTags


class FixPriceSpider(scrapy.Spider):
    name = 'fix_price'

    def start_requests(self) -> Iterable[Request]:
        urls = [
            'https://fix-price.com/catalog/dlya-doma',
        ]
        for url in urls:
            category = f'{urlparse(url).path.lstrip('catalog/')}'
            url_to_api = urljoin(settings.BASE_URL_API, f'product/in/{category}') + '?page=1'
            yield scrapy.Request(
                url_to_api,
                callback=self.parse,
                method='POST'
            )

    def get_item_parse(self, response, item: FixPriceItem = None, **kwargs):
        item_response = json.loads(response.text)
        id_main_image = item_response['image']
        if item_response['video']:
            item.assets['video'].append(f'https://www.youtube.com/watch?v={item_response.get('video')}')
        for image in item_response['images']:
            if image['id'] == id_main_image:
                item.assets['main_image'] = image['src']
            item.assets['set_images'].append(image['src'])
        item.metadata['__description'] = item_response.get('description')
        if item_response.get('properties'):
            for feature in item_response.get('properties'):
                alias = feature['alias']
                value = feature['value']
                item.metadata[alias] = value
        yield item

    def parse(self, response, **kwargs):
        json_response = json.loads(response.text)
        for item_response in json_response:
            item = FixPriceItem(
                timestamp=int(datetime.now().timestamp()),
                RCP=item_response['sku'],
                url=urljoin(settings.BASE_URL, item_response['url']),
                title=item_response['title'],
                marketing_tags=[],
                brand='',
                section=[],
                price_data={
                    'current': 0,
                    'original': 0,
                    'sale_tag': ''
                },
                stock={
                    'in_stock': False,
                    'count': 0
                },
                assets={
                    'main_image': '',
                    'set_images': [],
                    'view360': [],
                    'video': []
                },
                metadata={
                    '__description': ''
                },
                variants=0
            )
            if item_response['isFresh']:
                item.marketing_tags.append(MarketingTags.isFresh)
            if item_response['isNew']:
                item.marketing_tags.append(MarketingTags.isNew)
            if item_response['isPromo']:
                item.marketing_tags.append(MarketingTags.isPromo)
            if item_response['adult']:
                item.marketing_tags.append(MarketingTags.adult)
            if item_response['isSeason']:
                item.marketing_tags.append(MarketingTags.isSeason)
            if item_response['isHit']:
                item.marketing_tags.append(MarketingTags.isHit)
            if item_response['isQRMark']:
                item.marketing_tags.append(MarketingTags.isQRMark)
            if item_response['forbidden']:
                item.marketing_tags.append(MarketingTags.forbidden)
            if item_response['unit']:
                item.marketing_tags.append(MarketingTags.unit)
            if item_response['specialPrice']:
                item.marketing_tags.append(MarketingTags.specialPrice)
            item.brand = item_response['brand']['title']
            category = item_response['category']
            if category:
                utils.add_section(item, category)
            special_price = item_response['specialPrice']
            original = float(item_response['price'])
            if special_price:
                current = float(special_price['price'])
                discount_percentage = (original - current) * 100 / original
                item.price_data = {
                    'current': current,
                    'original': original,
                    'sale_tag': f'Скидка {discount_percentage:.2f}%'
                }
            else:
                item.price_data = {
                    'current': original,
                    'original': original,
                }
            if item_response['inStock']:
                item.stock = {
                    'in_stock': True,
                    'count': int(item_response.get('inStock'))
                }
            variant_count = item_response['variantCount']
            if variant_count:
                item.variants = int(variant_count)
            url = item_response['url']
            if url:
                url_item = urljoin(settings.BASE_URL_API, f"product/{item_response.get('url')}")
                yield scrapy.Request(
                    url_item,
                    method='GET',
                    callback=partial(self.get_item_parse, item=item)
                )

        if len(json_response) >= settings.MAX_ITEMS_TO_PAGE:
            url = urlparse(response.url)
            page = int(url.query.lstrip('page='))
            next_page = page + 1
            url_to_api = urljoin(f'{url.scheme}://{url.netloc}', url.path) + f'?page={next_page}'
            yield scrapy.Request(
                url_to_api,
                callback=self.parse,
                method='POST'
            )
