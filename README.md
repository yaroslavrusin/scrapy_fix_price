Проект для парсинга товаров с fix-price.com по категориям. Проект выполнен с использованием
Scrapy.
Список со ссылками по категории [urls](./urls).
В файле [settings.py](./fix_price/fix_price/settings.py) укажите:
- *REGION_NUMBER* - номер региона для fix-price.com. Можно посмотреть в заголовке запроса "X-City". \
Если есть proxy, то укажите:
- *PROXY_IP* - ip-адрес proxy сервера.
- *PROXY_PORT* - port proxy сервера. \
Для запуска передите в директорию fix_price и запустите команду: \
`scrapy crawl fix_price -o result.json`