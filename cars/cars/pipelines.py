# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import sqlite3


class CarsPipeline:
    def __init__(self):
        self.con = sqlite3.connect('cars.db')
        self.con.execute("PRAGMA foreign_keys = ON")
        self.cur = self.con.cursor()

    def process_item(self, item, spider):
        self.cur.execute("""INSERT OR IGNORE INTO car VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
        (
            item['car_id'],
            item['car_url'],
            item['car_make'],
            item['car_model'],
            item['car_year'],
            item['car_fuel'],
            item['car_odo'],
            item['car_engine'],
            item['car_gears'],
            item['car_price'],
            item['car_location']))
        self.con.commit()
        return item
