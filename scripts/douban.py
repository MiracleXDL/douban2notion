import argparse
import json
import os
import re
from bs4 import BeautifulSoup
import pendulum
from retrying import retry
import requests
from notion_helper import NotionHelper
import utils
import feedparser
import re
from datetime import datetime
DOUBAN_API_HOST = os.getenv("DOUBAN_API_HOST", "frodo.douban.com")
DOUBAN_API_KEY = os.getenv("DOUBAN_API_KEY", "0ac44ae016490db2204ce0a042db2916")

from config import (
    movie_properties_type_dict,
    book_properties_type_dict,
    TAG_ICON_URL,
    USER_ICON_URL,
)
from utils import get_icon
from dotenv import load_dotenv

load_dotenv()
rating = {
    1: "⭐️",
    2: "⭐️⭐️",
    3: "⭐️⭐️⭐️",
    4: "⭐️⭐️⭐️⭐️",
    5: "⭐️⭐️⭐️⭐️⭐️",
}
movie_status = {
    "mark": "想看",
    "doing": "在看",
    "done": "看过",
}
book_status = {
    "mark": "想读",
    "doing": "在读",
    "done": "读过",
}
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

headers = {
    "host": DOUBAN_API_HOST,
    "authorization": f"Bearer {AUTH_TOKEN}" if AUTH_TOKEN else "",
    "user-agent": "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.16(0x18001023) NetType/WIFI Language/zh_CN",
    "referer": "https://servicewechat.com/wx2f9b06c1de1ccfca/84/page-frame.html",
    "Cookie":os.getenv("COOKIE")
}

parse_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    "Cookie": os.getenv("COOKIE")
}


@retry(stop_max_attempt_number=3, wait_fixed=5000)
def fetch_subjects(user, type_, status):
    offset = 0
    page = 0
    url = f"https://{DOUBAN_API_HOST}/api/v2/user/{user}/interests"
    total = 0
    results = []
    while True:
        params = {
            "type": type_,
            "count": 50,
            "status": status,
            "start": offset,
            "apiKey": DOUBAN_API_KEY,
        }
        response = requests.get(url, headers=headers, params=params)
        
        if response.ok:
            response = response.json()
            interests = response.get("interests")
            if len(interests) == 0:
                break
            results.extend(interests)
            print(f"total = {total}")
            print(f"size = {len(results)}")
            page += 1
            offset = page * 50
    return results



def insert_movie():
    notion_movies = notion_helper.query_all(database_id=notion_helper.movie_database_id)
    notion_movie_dict = {}
    for i in notion_movies:
        movie = {}
        for key, value in i.get("properties").items():
            movie[key] = utils.get_property_value(value)
        notion_movie_dict[movie.get("豆瓣链接")] = {
            "短评": movie.get("短评"),
            "状态": movie.get("状态"),
            "观影日期": movie.get("观影日期"),
            "评分": movie.get("评分"),
            "page_id": i.get("id"),
        }
    results = []
    for i in movie_status.keys():
        results.extend(fetch_subjects(douban_name, "movie", i))
    for result in results:
        movie = {}
        subject = result.get("subject")
        if (
            subject.get("title") == "未知电影" or subject.get("title") == "未知电视剧"
        ) and subject.get("url") in unknown_dict:
            unknown = unknown_dict.get(subject.get("url"))
            subject["title"] = unknown.get("title")
            subject["pic"]["large"] = unknown.get("img")
        movie["电影名"] = subject.get("title")
        create_time = result.get("create_time")
        create_time = pendulum.parse(create_time, tz=utils.tz)
        # 时间上传到Notion会丢掉秒的信息，这里直接将秒设置为0
        create_time = create_time.replace(second=0)
        movie["观影日期"] = create_time.int_timestamp
        movie["豆瓣链接"] = subject.get("url")
        movie.update(parse_movie(subject.get("url")))
        movie["状态"] = movie_status.get(result.get("status"))
        if result.get("rating"):
            movie["评分"] = rating.get(result.get("rating").get("value"))
        if result.get("comment"):
            movie["短评"] = result.get("comment")
        if notion_movie_dict.get(movie.get("豆瓣链接")):
            notion_movive = notion_movie_dict.get(movie.get("豆瓣链接"))
            if (
                notion_movive.get("日期") != movie.get("日期")
                or notion_movive.get("短评") != movie.get("短评")
                or notion_movive.get("状态") != movie.get("状态")
                or notion_movive.get("评分") != movie.get("评分")
            ):
                properties = utils.get_properties(movie, movie_properties_type_dict)
                notion_helper.get_date_relation(properties, create_time)
                notion_helper.update_page(
                    page_id=notion_movive.get("page_id"), properties=properties
                )

        else:
            print(f"插入{movie.get('电影名')}")
            movie["类型"] = subject.get("type")
            properties = utils.get_properties(movie, movie_properties_type_dict)
            notion_helper.get_date_relation(properties, create_time)
            parent = {
                "database_id": notion_helper.movie_database_id,
                "type": "database_id",
            }
            notion_helper.create_page(
                parent=parent, properties=properties, icon=get_icon(movie["海报"])
            )


def insert_book():
    notion_books = notion_helper.query_all(database_id=notion_helper.book_database_id)
    notion_book_dict = {}
    for i in notion_books:
        book = {}
        for key, value in i.get("properties").items():
            book[key] = utils.get_property_value(value)
        notion_book_dict[book.get("豆瓣链接")] = {
            "短评": book.get("短评"),
            "状态": book.get("状态"),
            "日期": book.get("日期"),
            "评分": book.get("评分"),
            "page_id": i.get("id"),
        }
    results = []
    for i in book_status.keys():
        results.extend(fetch_subjects(douban_name, "book", i))
    for result in results:
        book = {}
        subject = result.get("subject")
        create_time = result.get("create_time")
        create_time = pendulum.parse(create_time, tz=utils.tz)
        # 时间上传到Notion会丢掉秒的信息，这里直接将秒设置为0
        create_time = create_time.replace(second=0)
        book["日期"] = create_time.int_timestamp
        book["豆瓣链接"] = subject.get("url")
        book.update(parse_book(subject.get("url")))
        book["状态"] = book_status.get(result.get("status"))
        if result.get("rating"):
            book["评分"] = rating.get(result.get("rating").get("value"))
        if result.get("comment"):
            book["短评"] = result.get("comment")
        if notion_book_dict.get(book.get("豆瓣链接")):
            notion_movive = notion_book_dict.get(book.get("豆瓣链接"))
            if (
                notion_movive.get("日期") != book.get("日期")
                or notion_movive.get("短评") != book.get("短评")
                or notion_movive.get("状态") != book.get("状态")
                or notion_movive.get("评分") != book.get("评分")
            ):
                properties = utils.get_properties(book, book_properties_type_dict)
                notion_helper.get_date_relation(properties, create_time)
                notion_helper.update_page(
                    page_id=notion_movive.get("page_id"), properties=properties
                )
        else:
            print(f"插入{book.get('书籍名')}")
            book["简介"] = subject.get("intro")
            press = []
            for i in subject.get("press"):
                press.extend(i.split(","))
            book["出版社"] = press
            book["类型"] = subject.get("type")
            if result.get("tags"):
                book["分类"] = [
                    notion_helper.get_relation_id(
                        x, notion_helper.category_database_id, TAG_ICON_URL
                    )
                    for x in result.get("tags")
                ]
            if subject.get("author"):
                book["作者"] = [
                    notion_helper.get_relation_id(
                        x, notion_helper.author_database_id, USER_ICON_URL
                    )
                    for x in subject.get("author")[0:100]
                ]
            properties = utils.get_properties(book, book_properties_type_dict)
            notion_helper.get_date_relation(properties, create_time)
            parent = {
                "database_id": notion_helper.book_database_id,
                "type": "database_id",
            }
            notion_helper.create_page(
                parent=parent, properties=properties, icon=get_icon(book["海报"])
            )


def parse_interests():
    items = feedparser.parse(
        f"https://www.douban.com/feed/people/{douban_name}/interests"
    )
    pattern = r'<img [^>]*src="([^"]+)"'
    for item in items.get("entries"):
        match = re.search(pattern, item.get("summary"))
        if match:
            img_url = match.group(1)
            unknown_dict[item.get("link").replace("http:", "https:")] = {
                "title": item.get("title")[2:],
                "img": img_url,
            }
        else:
            print("没有找到图片链接")


unknown_dict = {}



def extract_earliest_date(dates):
    # 正则表达式去掉括号内的内容
    cleaned_dates = [re.sub(r"\(.*?\)", "", date).strip() for date in dates]
    # 过滤出有效的日期格式
    valid_dates = []
    for date in cleaned_dates:
        try:
            # 尝试解析日期
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
            valid_dates.append(parsed_date)
        except ValueError:
            # 如果解析失败，跳过该日期
            continue
    # 返回最早的日期
    if valid_dates:
        earliest_date = min(valid_dates)
        return earliest_date.strftime("%Y-%m-%d")
    return None


def parse_movie(link):
    print(link)
    response = requests.get(link, headers=parse_headers)
    soup = BeautifulSoup(response.content)
    title = soup.find(property="v:itemreviewed").string
    year = soup.find("span", {"class": "year"}).string[1:-1]
    info = soup.find(id="info")
    cover = soup.find(id="mainpic").img["src"]
    # 类型
    genre = list(map(lambda x: x.string, info.find_all(property="v:genre")))
    genre = [
        notion_helper.get_relation_id(
            x, notion_helper.category_database_id, TAG_ICON_URL
        )
        for x in genre
    ]
    country = []
    language = []
    subtitle = ""
    # 导演
    directors = [x.string for x in info.find_all(rel="v:directedBy")]
    # 演员
    actors = [x.string for x in info.find_all(rel="v:starring")]
    release_date = [x.string for x in info.find_all(property="v:initialReleaseDate")]
    release_date = extract_earliest_date(release_date)
    duration = info.find(property="v:runtime")
    count = None
    if duration:
        duration = duration.string
    for span in info.find_all("span", {"class": "pl"}):
        if "制片国家/地区:" == span.string:
            country = span.next_sibling.string.strip().split("/")
        if "语言:" == span.string:
            language = span.next_sibling.string.strip().split("/")
        if "又名:" == span.string:
            subtitle = span.next_sibling.string.strip()
        if "单集片长:" == span.string:
            duration = span.next_sibling.string.strip()        
        if "集数:" == span.string:
            count = span.next_sibling.string.strip()
    movie_info = {
        "电影名": title,
        "上映年份": year,
        "制片地区": country,
        "分类": genre,
        "语言": language,
        "又名": subtitle,
        "上映日期": release_date,
        "片长时间": duration,
        "集数": count,
        "演员": [
            notion_helper.get_relation_id(
                x, notion_helper.actor_database_id, USER_ICON_URL
            )
            for x in actors[0:5]
        ],
        "导演": [
            notion_helper.get_relation_id(
                x, notion_helper.director_database_id, USER_ICON_URL
            )
            for x in directors[0:5]
        ],
        "海报": cover,
    }
    return movie_info


def parse_book(link):
    print(link)
    response = requests.get(link, headers=parse_headers)
    soup = BeautifulSoup(response.content)
    title = soup.find(property="v:itemreviewed").string
    cover = soup.find(id="mainpic").img["src"]
    info = soup.find(id="info")
    book_info = {"书籍名":title,"海报":cover}
    for span in info.find_all("span", {"class": "pl"}):
        next_sibling = span.next_sibling
        if isinstance(next_sibling, str) and next_sibling.strip() == ":":
            # 如果是字符串并且是冒号，找下一个 <a> 标签
            next_tag = span.find_next("a")
            if next_tag:
                book_info[span.string] = next_tag.string.strip()
        else:
            book_info[span.string.replace(":","")] = next_sibling.string.strip()
    if book_info.get("出版年"):
        year= book_info.get("出版年").split("-")[0]
        book_info["出版年份"] = year.split("/")[0]
    return book_info



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("type")
    options = parser.parse_args()
    type = options.type
    is_movie = True if type == "movie" else False
    notion_helper = NotionHelper(type)
    douban_name = os.getenv("DOUBAN_NAME", None)
    parse_interests()
    if is_movie:
        insert_movie()
    else:
        insert_book()
