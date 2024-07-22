from fix_price.items import FixPriceItem


def add_section(item: FixPriceItem, category: dict) -> None:
    item.section.append(category['title'])
    if category.get('parentCategory') is None:
        return
    else:
        category = category['parentCategory']
        return add_section(item, category)
