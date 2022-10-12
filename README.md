# Data Harvesting

## **Summary**

Here's an overview of a simple web scraping project with notes. The spider currently sits in production and collects data on a target I have interest in. The program is scheduled with [Cron](https://en.wikipedia.org/wiki/Cron) which calls the `run.sh` shell script, which in turn invokes a [Scrapy](https://docs.scrapy.org/) spider with [Pipenv](https://pipenv.pypa.io/) and appends some basic performance tracking to a log file. The spider feeds our clean data to a [SQLite3](https://www.sqlite.org/index.html) database which will eventually be used to train a Multiple Regression machine learning model in order to make some useful predictions.

## **Target Analysis**

It's important to keep our goals in mind to limit the scope of the work and focus our efforts.

* What are we looking to collect?
  * Time-Series Data
  * Classification Variables
* How much work is it to collect?
  * Most features are labeled
  * Possibly some text analysis required (word-association token mining)
* Are there bandwidth and time considerations?
  * Mostly low-impact text requests
  * Spread over many hours
  * Some images (~750kB per page-load)
  * Scrape during off-peak times
  * CRON-job triggers the action
  * Notify stats and errors

## **Database**

For a simple collection procedure like this, we won't be needing concurrency support, so SQLite3 is perfectly usable for our needs.

All we have to do, is create a database.

```bash
sqlite3 cars.db
```

I chose a simple schema consisting of a table for item data that automatically generates a UTC timestamp and a table for item history that tracks changes for price and mileage, with its own timestamp.

```sql
CREATE TABLE IF NOT EXISTS car (
    id TEXT PRIMARY KEY,
    url TEXT,
    make TEXT,
    model TEXT,
    year TEXT,
    fuel TEXT,
    odo TEXT,
    engine TEXT,
    gears TEXT,
    price TEXT,
    location TEXT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
```

```sql
CREATE TABLE IF NOT EXISTS history (
    car_id TEXT NOT NULL,
    date TEXT,
    price TEXT,
    odo TEXT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(car_id) REFERENCES car(id)
);
```

### **Spider**

#### **JavaScript**

It's important to remember that modern websites have a lot of JavaScript, and that means content will get interactively loaded by browsers resulting in web pages appearing differently to different user-agents. Although there are JS helpers that plug into Scrapy, Scrapy by itself is not a browser and won't load interactive content. For us, the source page is good enough, so all we have to do is *disable JavaScript* in our browser and then do our XPath lookups.

#### **Selectors**

Example of an Xpath selection on our response object using manual string concatenation

```python
response.xpath('//html/body/div[9]/div[5]/div[2]/div[5]/div[' + str(variable) + ']/div[1]/a/span/text()').get()
```

#### **Targets**

First, we need to create a list of URLs that point to each individual car. Fortunately this is easy to do because most listing sites present their user with an index pages. This allows us to construct a function to iterate through all the available pages. On top of that, we can leverage the site's API to simplify the our collection process by crafting a GET request that filters all the content by its creation date, meaning after an initial full scan, we then only fetch changes going forward.

Example: collecting targets
```py
...
def start_requests(self):
    page = 1
    while(scrapy.response.status == 200):
        yield scrapy.Request(
            "https://www.domain.com/?\
                module=cars&\
                order_by=date_created&\
                filters=no&\
                order_to=desc&\
                page=" + str(page))
        page += 1
...
```

#### **Checkpointing for Partial Scans**

Ideally we want to only perform partial updates to the database after an initial full scan. To establish a last known good state after a full scan, we can reference the first scanned item's URL, and on successive updates, only scan up to the last page containing that url. The logic in our spider should be such that performing an initial scan, must instantiate our database and populate it with the entire site's catalogue of items, and on successive scans do partial updates if the DB contains data. This windowed-stream approach will reduce network pressure on the source, which is always polite.

1. query db for newest url based on the most recent item id
2. initiate scan with newest url as stop-condition

```py
...

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

...
```

### **History Updates for Full Scans**

It turns out, only doing partial updates to our database will result in information being lost, namely the changes of pricing in existing listings, which in itself is an important indicator that can help us derive other features such as short term sale pressures. When performing the full scan, we append to the item's price history, this is less expensive as we don't need to perform any comparisons. We can optionally drop redundant data or perform pruning with scheduled database operations.

Example: Pseudo-Code
```py
...
# if id in db and item price != db price:
  # append item price to history
  # update db price
# if id in db and item odo != db odo:
  # append item odo to history
  # update db odo
...
```

### **Pipelines**

Scrapy's built-in item pipeline is going to help us insert the clean data into our SQLite3 database. Here we could make consideration for data validation and filtering, for example if a vehicle has no price data or is not a motor car, it should be dropped.

Example: Scrapy pipeline
```py
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
```

## **Automation**

Ideally, we want the collection process to be automatic, so let's do some basic automation with a **shell script** and **CRON job**. I chose to set up the scraper on a Raspberry Pi 1B+, which needed `libxslt-dev` installed. The shell script simply changes directory into our project folder and executes a crawl using our virtual environment manager to run our spider. The time is logged to `log.txt` as the crawl starts and ends, so we have some idea if our CRON job is working. If the need arises, we can enhance this script and our spider to append more stats to `log.txt`.

Example: logging portion of the shell script that executes when our Cron job runs.
```bash
START_TIME="`date "+%Y-%m-%d %H:%M:%S"`";
echo "START | $START_TIME" >> log.txt

END_TIME="`date "+%Y-%m-%d %H:%M:%S"`";
echo "HALT  | $END_TIME" >> log.txt
```

### Scheduling

The spider has been running for more than a month without issue. To reduce impact on the 

Example: `crontab -e` set to run our shell script every 8 hours starting at midnight.

```bash
0 */8 * * * /usr/bin/sh /home/user/projects/project/run.sh
```

We can check to see if our database is successfully updated by querying the newest item id, and comparing that with the source.

```sql
.mode column
SELECT * FROM car ORDER BY id DESC LIMIT 1;
```

The resulting database table is populated as follows.

```bash
id          url                       make         model        year  fuel    odo     engine  gears       price   location     time               
----------  ------------------------  -----------  -----------  ----  ------  ------  ------  ----------  ------  -----------  -------------------
0000000000  /make-model-relative-url  Nissan       Navara       2008  Petrol  170000  4.0     Manual      150000  City         2022-08-02 23:48:43
0000000001  /make-model-relative-url  Hyundai      Sonata       2003  Petrol  181000  2.4     Autotronic  30000   City         2022-08-02 23:48:43
0000000002  /make-model-relative-url  Toyota       Dyna         1994  Diesel  283133  0.0     None        185000  City         2022-08-02 23:48:43
```

## Notes

In case anyone decides to fork and play with this code, I've anonymized the spider so my target doesn't get hammered by test requests. You'd have to specify a new target, modify the Xpath selectors, modify the Item pipeline and change the shell script to match your project to start getting results.