import scrapy
import re


def exclude_special_notations(data):
    """Выборка списка элементов, которые не соответствуют шаблонам служебной информации."""
    pattern = r'(\[|\()\w+.?(\]|\))|\xa0|\n|\\d|рус.|англ.|\[*?\]|/|\*|\(|\)|\[|\]|\,\ |\,'
    almost_ready = [text.strip() for text in data if not re.search(pattern, text)]
    return ','.join(almost_ready).replace(',,,', ',').replace(',,', ',').split(',')


def parse_film_data(response):
    """Извлечение данных о фильме."""
    title = response.xpath('//*[@class="infobox-above"]//text()').getall()[-1]
    genre = response.xpath('//*[@data-wikidata-property-id="P136"]//text()').getall()
    director = response.xpath('//*[@data-wikidata-property-id="P57"]//text()').getall()
    country_name = response.xpath('//*[@data-wikidata-property-id="P495"]//text()').getall()
    # В редких случаях год находится в неименованном блоке, скрипт такие пропускает
    year = response.xpath('//*[@data-wikidata-property-id="P577"]//a[@title]//text() | '
                          '//*[@class="dtstart"]//text()').getall()  # NOQA

    yield {
        'Название': title,
        'Жанр': exclude_special_notations(genre),
        'Режиссер': exclude_special_notations(director),
        'Страна': exclude_special_notations(country_name),
        # если список существует, то возвращает последнее значение
        'Год': year[-1] if year else year,
    }


class FilmDataMtsShadItem(scrapy.Spider):
    name = 'film_data'
    allowed_domains = ["ru.wikipedia.org"]
    start_urls = ['https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту']

    def parse(self, response, **kwargs):
        # Извлечение ссылок на страницы фильмов
        links = response.xpath('//div[@id="mw-pages"]//div[@class="mw-category-group"]//a/@href').getall()
        for link in links:
            yield response.follow(link, callback=parse_film_data)

        # Переход на следующую страницу
        next_page = response.xpath('//a[contains(text(), "Следующая страница")]/@href').extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
