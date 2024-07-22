import json
from datetime import datetime
from functools import partial
from typing import Iterable
from urllib.parse import urlparse, urljoin, parse_qsl, urlencode

import scrapy
from scrapy import Request

from fix_price import settings
from fix_price import utils
from fix_price.items import FixPriceItem, MarketingTags


class FixPriceSpider(scrapy.Spider):
    """Класса для парсинка товаров в категории"""
    name = 'fix_price'

    def start_requests(self) -> Iterable[Request]:
        for url in utils.get_urls():
            category = f'{urlparse(url).path.lstrip('catalog/')}'
            param = {
                'page': 1,
                'limit': 24,
                'sort': 'sold'
            }
            url_to_api = f"{urljoin(settings.BASE_URL_API, f'product/in/{category}')}?{urlencode(param)}"
            body_request = {
                'category': category,
                'brand': [],
                'price': [],
                'isDividedPrice': False,
                'isNew': False,
                'isHit': False,
                'isSpecialPrice': False
            }
            yield scrapy.Request(
                url_to_api,
                callback=partial(self.parse, body_request=body_request),
                method='POST',
                body=json.dumps(body_request)
            )

    def get_item_parse(self, response, item: FixPriceItem = None, **kwargs):
        item_response = json.loads(response.text)
        if item_response['video']:
            item.assets['video'].append(f'https://www.youtube.com/watch?v={item_response['video']}')
        id_main_image = item_response['image']
        if id_main_image:
            for image in item_response['images']:
                if image['id'] == id_main_image:
                    item.assets['main_image'] = image['src']
                item.assets['set_images'].append(image['src'])
        item.metadata['__description'] = item_response['description'].strip()
        if item_response.get('properties'):
            for feature in item_response['properties']:
                alias = feature['alias']
                value = feature['value']
                item.metadata[alias] = value
        if item_response['variants']:
            variant = item_response['variants'][0]
            if variant:
                dimensions = variant['dimensions']
                if dimensions:
                    item.metadata.update(dimensions)
        yield item

    def parse(self, response, body_request=None, **kwargs):
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
            brand = item_response['brand']
            if brand:
                item.brand = brand['title']
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
                    'count': int(item_response['inStock'])
                }
            variant_count = item_response['variantCount']
            if variant_count:
                item.variants = int(variant_count)
            url = item_response['url']
            if url:
                url_item = urljoin(settings.BASE_URL_API, f"product/{item_response['url']}")
                yield scrapy.Request(
                    url_item,
                    method='GET',
                    callback=partial(self.get_item_parse, item=item),
                    body=json.dumps(body_request)
                )

        if len(json_response) > 0:
            url = urlparse(response.url)
            param = parse_qsl(url.query)
            next_page = int(param[0][1]) + 1
            param = {
                'page': next_page,
                'limit': 24,
                'sort': 'sold'
            }
            url_to_api = f"{urljoin(f'{url.scheme}://{url.netloc}', url.path)}?{urlencode(param)}"
            yield scrapy.Request(
                url_to_api,
                callback=self.parse,
                method='POST'
            )
