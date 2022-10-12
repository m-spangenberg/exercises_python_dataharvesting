# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CarsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    car_id = scrapy.Field()
    car_url = scrapy.Field()
    car_make = scrapy.Field()
    car_model = scrapy.Field()
    car_year = scrapy.Field()
    car_fuel = scrapy.Field()
    car_odo = scrapy.Field()
    car_engine = scrapy.Field()
    car_gears = scrapy.Field()
    car_price = scrapy.Field()
    car_location = scrapy.Field()