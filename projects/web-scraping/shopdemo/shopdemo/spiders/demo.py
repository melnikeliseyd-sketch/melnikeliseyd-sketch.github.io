import scrapy


class DemoSpider(scrapy.Spider):
    name = "demo"
    allowed_domains = ["webscraper.io"]
    start_urls = ["https://webscraper.io/test-sites/e-commerce/allinone"]

    processed_titles = set()
    def parse(self, response):
        categories = response.css("li.nav-item a::attr(href)").getall()
        for category in categories:
            yield response.follow(category, self.parse_item_types)

    def parse_item_types(self, response):
        item_types_ul = response.css("ul.nav-second-level")
        item_types = item_types_ul.css("li.nav-item a::attr(href)").getall()
        for item_type in item_types:
            yield response.follow(item_type, self.parse_items)

    def parse_items(self, response):
        cards = response.css('div.thumbnail, div.card')
        for c in cards:
            title = c.css('a.title::text').get()
            price = c.css('h4.price [itemprop="price"]::text').get()
            description = c.css('p.description::text').get()
            rating = c.css('div.ratings p[data-rating]::attr(data-rating)').get()
            reviews = c.css("div.ratings reviewCount::text").get()
            title_clean = title.strip()
            if title_clean not in self.processed_titles:
                self.processed_titles.add(title_clean)

                yield {
                    "title": title.strip(),
                    "price": price.strip(),
                    "description": description.strip() ,
                    "rating": rating.strip(),
                    "reviews": reviews.strip()
                }