from bs4 import BeautifulSoup
import requests
import os
import psycopg2
import sqlite3 as lite
import schedule
import time
from config import TOKEN, chat_id,  DATABASE_URL


def crawlingNews():

    website_request = requests.get('http://msit.in/latest_news')
    website_content = BeautifulSoup(website_request.content, 'html.parser')

    jobs_link = website_content.select('div.tab-content a')
    return jobs_link


def crawlingNotice():

    website_request = requests.get('http://msit.in/notices')
    website_content = BeautifulSoup(website_request.content, 'html.parser')
    notices_link = website_content.select('div.tab-content a')
    return notices_link


def crawlingMarq():

    website_request = requests.get('http://msit.in/')
    website_content = BeautifulSoup(website_request.content, 'html.parser')

    marq_link = website_content.select('div.marquee-text a')
    return marq_link


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def send_message(chat_id, text, doc):
    URL = "https://api.telegram.org/bot{}/".format(TOKEN)
    url = URL + \
        f"sendDocument?chat_id={chat_id}&parse_mode=html&caption={text}&document={doc}"
    print(url)
    get_url(url)


def send_marq(chat_id, text, doc):
    URL = "https://api.telegram.org/bot{}/".format(TOKEN)
    url = URL + \
        f"sendMessage?chat_id={chat_id}&parse_mode=html&text={text} {doc}"
    print(url)
    get_url(url)


def check_result_send_mess():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        jobs_db = conn.cursor()
        print("Connected to DB")
        jobs_db.execute(
            'CREATE TABLE IF NOT EXISTS jobs (id SERIAL, job TEXT NOT NULL)')
    except:
        send_message(chat_id, 'The database could not be accessed')

    jobs_link_pm = crawlingNews()
    notices_link = crawlingNotice()
    marquee_link = crawlingMarq()

    for item in jobs_link_pm:
        job_exists = jobs_db.execute(
            'SELECT job FROM jobs WHERE job = %s', [item.text])

        if len(jobs_db.fetchall()) != 1:
            news_content = f"<b>LATEST NEWS</b>: {item.text}"
            news_doc = f"http://msit.in{item['href']}"
            print(f"NEWS FETCHING : \n {news_content}\n")
            send_message(chat_id, news_content, news_doc)
            jobs_db.execute('INSERT INTO jobs (job) VALUES (%s);', [item.text])
            conn.commit()
        else:
            continue

    for item in notices_link:
        job_exists = jobs_db.execute(
            'SELECT job FROM jobs WHERE job = %s', [item.text])

        if len(jobs_db.fetchall()) != 1:
            notices_content = f"<b>LATEST NOTICE</b>: {item.text}"
            notices_doc = f"http://msit.in{item['href']}"
            print(f"NOTICE FETCHING : \n {notices_content}\n")
            send_message(chat_id, notices_content, notices_doc)
            jobs_db.execute('INSERT INTO jobs (job) VALUES (%s);', [item.text])
            conn.commit()
        else:
            continue

    for item in marquee_link:
        job_exists = jobs_db.execute(
            'SELECT job FROM jobs WHERE job = %s', [item.text])

        if len(jobs_db.fetchall()) != 1:
            mess_content = f"<b>Newsflash!</b>: {item.text}"
            print(f"MARQUEE FETCHING : \n {mess_content}\n")
            checker = item['href'].find("media")
            if checker != -1:
                doc = f"http://msit.in{item['href']}"
            else:
                doc = f"{item['href']}"
            send_marq(chat_id, mess_content, doc)
            jobs_db.execute('INSERT INTO jobs (job) VALUES (%s);', [item.text])
            conn.commit()
        else:
            continue

    jobs_db.close()


# bot and chat ids
schedule.every().hour.do(check_result_send_mess)
while True:
    schedule.run_pending()
    time.sleep(1)
