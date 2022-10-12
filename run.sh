#!/bin/sh

START_TIME="`date "+%Y-%m-%d %H:%M:%S"`";
echo "START | $START_TIME" >> /home/user/projects/project/cars/log.txt
cd /home/user/projects/project/cars/
/home/user/.local/bin/pipenv run scrapy crawl cars
END_TIME="`date "+%Y-%m-%d %H:%M:%S"`";
echo "HALT  | $END_TIME" >> /home/user/projects/project/cars/log.txt
