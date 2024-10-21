
RICH_TEXT = "rich_text"
URL = "url"
RELATION = "relation"
NUMBER = "number"
DATE = "date"
FILES = "files"
STATUS = "status"
TITLE = "title"
SELECT = "select"
MULTI_SELECT = "multi_select"

book_properties_type_dict = {
    "书籍名":TITLE,
    "副标题":RICH_TEXT,
    "原作名":RICH_TEXT,
    "出版年份":SELECT,
    "短评":RICH_TEXT,
    "ISBN":RICH_TEXT,
    "豆瓣链接":URL,
    "作者":RELATION,
    "评分":SELECT,
    "海报":FILES,
    "分类":RELATION,
    "状态":STATUS,
    "日期":DATE,
    "简介":RICH_TEXT,
    "豆瓣链接":URL,
    "出版社":MULTI_SELECT,
}

TAG_ICON_URL = "https://www.notion.so/icons/tag_gray.svg"
USER_ICON_URL = "https://www.notion.so/icons/user-circle-filled_gray.svg"
BOOK_ICON_URL = "https://www.notion.so/icons/book_gray.svg"


movie_properties_type_dict = {
    "电影名":TITLE,
    "短评":RICH_TEXT,
    # "ISBN":RICH_TEXT,
    # "链接":URL,
    "上映年份": SELECT,
    "制片地区": MULTI_SELECT,
    "语言": MULTI_SELECT,
    "又名": RICH_TEXT,
    "片长时间": RICH_TEXT,
    "上映日期": DATE,
    "导演":RELATION,
    "演员":RELATION,
    # "Sort":NUMBER,
    "海报":FILES,
    "分类":RELATION,
    "状态":STATUS,
    "类型":SELECT,
    "评分":SELECT,
    # "阅读时长":NUMBER,
    # "阅读进度":NUMBER,
    # "阅读天数":NUMBER,
    "观影日期":DATE,
    "集数":NUMBER,
    "简介":RICH_TEXT,
    # "开始阅读时间":DATE,
    # "最后阅读时间":DATE,
    # "简介":RICH_TEXT,
    # "书架分类":SELECT,
    # "我的评分":SELECT,
    "豆瓣链接":URL,
}
