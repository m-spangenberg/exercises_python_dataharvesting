import scrapy
import sqlite3
import re


class carSpider(scrapy.Spider):
    name = "cars"
    allowed_domains = ['targetdomain.tld']

    def __init__(self):
        super(carSpider, self).__init__()
        self.checkpoint_B = ''
        self.checkpoint_A = ''
        self.pagerange = 4
        self.pathrange = 15

    
    def checkpoint(self):
        '''
        Check database for freshest item url
        '''
        check = []

        con = sqlite3.connect('cars.db')
        cur = con.cursor()
        res = cur.execute("""SELECT url FROM car ORDER BY id DESC LIMIT 1""")
        fet = res.fetchone()
        con.close()

        if fet != None:
            check.append(fet[0])
        
        return check


    def start_requests(self):
        '''
        Index through listing pages
        '''
        self.checkpoint_A = self.checkpoint()

        for page in range(1, self.pagerange):
            if str(self.checkpoint_A[0]) == str(self.checkpoint_B):
                break
            yield scrapy.Request('https://www.targetdomain.tld/?module=cars&order_by=date_created&filters=no&order_to=desc&page='+ str(page))


    def parse(self, response):
        '''
        Index through all available items on page
        '''
        for carpath in range(1, self.pathrange):

            if str(self.checkpoint_A[0]) == str(self.checkpoint_B):
                raise scrapy.exceptions.CloseSpider('Checkpoint Reached: Shutting Down')

            # Xpath queries to the site's source code
            car_id = re.search(r"(\d{8,})", str(response.xpath('/html/body/div[9]/div[5]/div[2]/div[5]/div[' + str(carpath) + ']/div[1]/a/@href').get()))
            car_url = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/div[' + str(carpath) + ']/div[1]/a/@href').get())
            car_make = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/div[' + str(carpath) + ']/div[1]/a/strong/span/text()').get()).strip()
            car_model = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/div[' + str(carpath) + ']/div[1]/a/span/text()').get()).strip()
            car_year = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/div[' + str(carpath) + ']/div[1]/a/strong/text()').get()).strip()
            car_fuel = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/a[' + str(carpath) + ']/div[3]/div[3]/text()').get()).strip()
            car_odo = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/a[' + str(carpath) + ']/div[3]/div[1]/text()').get()).strip('km').replace(' ', '').strip()
            car_engine = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/a[' + str(carpath) + ']/div[3]/div[4]/text()').get()).replace('L', '').strip()
            car_gears = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/a[' + str(carpath) + ']/div[3]/div[2]/text()').get()).strip()
            car_price = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/div[' + str(carpath) + ']/div[3]/span[1]/text()').get()).replace('N$', '').replace(',', '').strip()
            car_location = str(response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/a[' + str(carpath) + ']/div[3]/div[5]/text()').get()).strip()

            # Set checkpoint B to current item url being processed
            self.checkpoint_B = car_url

            # Construct an item with the following key:value pairs mined from the above page
            yield {
                'car_id' : str(car_id.group(0)),
                'car_url' : car_url,
                'car_make' : car_make,
                'car_model' : car_model,
                'car_year' : car_year,
                'car_fuel' : car_fuel,
                'car_odo' : car_odo,
                'car_engine' : car_engine,
                'car_gears' : car_gears,
                'car_price' : car_price,
                'car_location' : car_location,
            }
