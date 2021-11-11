import requests
import json

STORIES_USER_AGENT = "Instagram 123.0.0.21.114 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15"


class Parser:
    session_id: int
    proxies: dict
    user_agent: str
    uids = dict()

    def __init__(self, login=None, password=None, session_id=None, proxy=None, user_agent=None):
        """При передаче логина и пароля происходит попытка входа. Если вход успешен, куки использоваться не будут.
        session_id - кукa sessionid, необходима чтобы избежать редиректа при большом кол-ве запросов.
        Желательно менять каждые несколько сотен запросов.
        proxies - прокси формата 'socks5h://127.0.0.1:9050'.
        user_agent - агент парсера. По умолчанию "Instagram 123.0.0.21.114 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15"
        Работает сасно, менять необходимости нет"""

        if session_id:
            self.cookies = {"sessionid": session_id}
        else:
            self.cookies = {}

        self.headers = {"Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
                        "Alt-Used": "www.instagram.com",
                        "Connection": "keep-alive",
                        "User-Agent": "Instagram 123.0.0.21.114 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US;"
                                      " en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15"}

        if user_agent:
            self.headers["User-Agent"] = user_agent
        if proxy:
            self.proxies = dict(http=proxy, https=proxy)
        else:
            self.proxies = {}
        if login and password:
            self.authorize(login, password)
        if proxy:
            self.test_proxy()

    def test_proxy(self):
        r = requests.get("http://icanhazip.com").text
        p = requests.get("http://icanhazip.com", proxies=self.proxies)
        if p.status_code != 200 or p.text == r:
            print(f"Proxy doesnt working and will not be used")
            self.proxies = {}
        else:
            print(f"Proxy connection via {p.text} established")

    def authorize(self, username, password):
        """Авторизоваться под именем {username} по паролю {password}.
        После успешного входа использует полученные куки"""

        url = "https://www.instagram.com/"
        login_url = "https://www.instagram.com/accounts/login/ajax/"
        headers = self.headers
        r = requests.get(url, headers=headers)
        csrf_token = r.cookies["csrftoken"]
        headers["X-CSRFToken"] = csrf_token
        cookies = r.cookies
        login_payload = {'username': username, 'password': password}
        login = requests.post(login_url, data=login_payload, allow_redirects=True, headers=headers, cookies=cookies)
        j = login.json()
        if j["authenticated"] and login.status_code == 200:
            self.cookies = login.cookies
            print(f"Login successful for {username}")
        else:
            print(f"Login failed for {username}")

    def __get_json(self, url, useragent=None):
        headers = self.headers
        if useragent:
            headers["User-Agent"] = useragent
        r = requests.get(url, headers=headers, cookies=self.cookies, proxies=self.proxies)

        if r.status_code == 200:
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                print("Instagram redirected to login page")
                raise IGRedirectError()
        else:
            raise NoSuchUserError()

    def __post_json(self, url, payload, useragent=None):
        headers = self.headers
        if useragent:
            headers["User-Agent"] = useragent
        r = requests.post(url, data=payload, headers=headers, cookies=self.cookies, proxies=self.proxies)

        if r.status_code == 200:
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                print("Instagram redirected to login page")
                raise Exception()
        else:
            print(f"Request status code {r.status_code}, {r.text}")
            raise Exception()

    def get_stories(self, login):
        """Получить ссылки на контент актуальных stories пользователся с именем {login}
        Возвращает список ссылок"""

        user_id = self.get_user_id(login)
        return self.get_stories_by_uid(user_id)

    def get_stories_by_uid(self, user_id):
        url = f"https://i.instagram.com/api/v1/feed/reels_media/?reel_ids={user_id}"
        j = self.__get_json(url, STORIES_USER_AGENT)
        try:
            items = j["reels"][str(user_id)]["items"]
        except KeyError:
            raise NoMaterialsFoundError
        urls = []
        for item in items:
            if item["media_type"] == 1:
                url = item["image_versions2"]["candidates"][-1]["url"]
            elif item["media_type"] == 2:
                url = item["video_versions"][-1]["url"]
            else:
                url = f"Strange media_type : {item['media_type']}"
            urls.append(url)

        return urls

    def get_user_id(self, username):
        """Получить instagram id пользователся с именем {username}"""

        if username in self.uids:
            return self.uids[username]
        url = f"https://www.instagram.com/{username}/?__a=1"
        j = self.__get_json(url)
        uid = j["graphql"]["user"]["id"]
        self.uids[username] = uid
        return uid

    def get_profile_pic(self, username):
        """Получить аватар пользователся с именем {username}"""
        url = f"https://www.instagram.com/{username}/?__a=1"
        j = self.__get_json(url)
        try:
            pic_url = j["graphql"]["user"]["profile_pic_url_hd"]
        except KeyError:
            pic_url = j["graphql"]["user"]["profile_pic_url"]
        return pic_url

    def get_highlights_list(self, login):
        """Получить список альбомов highlights аккаунта с именем {login}.
        Возвращает список словарей формата {id, title, thumbnail(url обложки)}"""

        user_id = self.get_user_id(login)
        return self.get_highlights_list_by_uid(user_id)

    def get_highlights_list_by_uid(self, user_id):
        url = f"https://www.instagram.com/graphql/query/?query_hash=c9100bf9110dd6361671f113dd02e7d6&variables=%7B%22user_id%22%3A%22{user_id}%22%2C%22include_chaining%22%3Afalse%2C%22include_reel%22%3Afalse%2C%22include_suggested_users%22%3Afalse%2C%22include_logged_out_extras%22%3Afalse%2C%22include_highlight_reels%22%3Atrue%2C%22include_related_profiles%22%3Afalse%7D"
        j = self.__get_json(url)
        hls = [hl["node"] for hl in j["data"]["user"]["edge_highlight_reels"]["edges"]]
        for i, hl in enumerate(hls):
            hls[i] = {"id": hl["id"], "title": hl["title"], "thumbnail": hl["cover_media_cropped_thumbnail"]["url"]}
        return hls

    def get_highlight_stories(self, hl_id):
        """Получить ссылки на контент альбома highlights c {hl_id}.
        Возвращает список ссылок"""
        url = f"https://www.instagram.com/graphql/query/?query_hash=45246d3fe16ccc6577e0bd297a5db1ab&variables=%7B%22reel_ids%22%3A%5B%5D%2C%22tag_names%22%3A%5B%5D%2C%22location_ids%22%3A%5B%5D%2C%22highlight_reel_ids%22%3A%5B%22{hl_id}%22%5D%2C%22precomposed_overlay%22%3Afalse%7D"
        j = self.__get_json(url)
        items = j["data"]["reels_media"][0]["items"]
        urls = []
        for item in items:
            if item["__typename"] == "GraphStoryVideo":
                url = item["video_resources"][-1]["src"]
            else:
                url = item["display_url"]

            urls.append(url)
        return urls

    def get_posts(self, username, start=0, finish=11):
        """Получить список постов аккаунта с именем {username} от поста с номером {start}
         до поста с номером {finish}(не включая). Нумерация начинается от нуля, нулевым является самый свежий пост.
         Формат возвращаемого значения: список словарей формата {id, urls(список адресов контента поста),
         caption(текст поста), likes (число лайков), comments(число комментов), timestamp(дата и время снимка в секундах
         от начала эпохи)}"""

        if "instagram.com/" in username:
            username = username[username.find("instagram.com/") + 14:]
            if username[-1] == "/":
                username = username[:-1]

        url = f"https://www.instagram.com/{username}/?__a=1"
        j = self.__get_json(url)
        user_id = j["graphql"]["user"]["id"]
        nodes = [node["node"] for node in j['graphql']['user']['edge_owner_to_timeline_media']['edges']]

        has_next_page = j['graphql']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        cursor = ""
        if has_next_page:
            cursor = j['graphql']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        while has_next_page and finish > len(nodes):
            url = f"https://www.instagram.com/graphql/query/?query_hash=8c2a529969ee035a5063f2fc8602a0fd&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A{50}%2C%22after%22%3A%22{cursor}%22%7D"
            j = self.__get_json(url)
            nodes += [node["node"] for node in j['data']['user']['edge_owner_to_timeline_media']['edges']]
            has_next_page = j['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
            if has_next_page:
                cursor = j['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']

        posts = []
        for node in nodes:
            post = dict()
            post["id"] = node["id"]
            if node["__typename"] == "GraphSidecar":
                urls = []
                for lil_node in node["edge_sidecar_to_children"]["edges"]:
                    lil_node = lil_node['node']
                    urls.append(lil_node['display_url'])
                post["urls"] = urls
            elif node["__typename"] == 'GraphVideo':
                post["urls"] = [node["video_url"]]
            else:
                post["urls"] = [node["display_url"]]
            post["caption"] = node["edge_media_to_caption"]["edges"][0]["node"]["text"]
            post["likes"] = node["edge_media_preview_like"]["count"]
            post["comments"] = node["edge_media_to_comment"]["count"]
            post["timestamp"] = node["taken_at_timestamp"]
            if post["id"] not in [post_n["id"] for post_n in posts]:
                posts.append(post)
        return posts[start:finish], user_id

    def get_posts_by_date(self, login, start_date, fin_date):
        """Получить список постов аккаунта с именем {login} загруженных между датами {start_date} и {fin_date}(дата и время снимка в секундах
         от начала эпохи).
         Формат возвращаемого значения: список словарей формата {id, urls(список адресов контента поста),
         caption(текст поста), likes (число лайков), comments(число комментов), timestamp(дата и время снимка в секундах
         от начала эпохи)}"""

        url = f"https://www.instagram.com/{login}/?__a=1"
        j = self.__get_json(url)
        user_id = j["graphql"]["user"]["id"]
        self.uids[login] = user_id

        nodes = [node["node"] for node in j['graphql']['user']['edge_owner_to_timeline_media']['edges']]
        has_next_page = j['graphql']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        cursor = ""
        if has_next_page:
            cursor = j['graphql']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']

        last_node_date = nodes[-1]["taken_at_timestamp"]

        while has_next_page and last_node_date > start_date:
            url = f"https://www.instagram.com/graphql/query/?query_hash=8c2a529969ee035a5063f2fc8602a0fd&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A{50}%2C%22after%22%3A%22{cursor}%22%7D"
            j = self.__get_json(url)
            nodes += [node["node"] for node in j['data']['user']['edge_owner_to_timeline_media']['edges']]
            has_next_page = j['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
            if has_next_page:
                cursor = j['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
            last_node_date = nodes[-1]["taken_at_timestamp"]

        posts = []
        for node in nodes:
            post = dict()
            post["id"] = node["id"]
            if node["__typename"] == "GraphSidecar":
                urls = []
                for lil_node in node["edge_sidecar_to_children"]["edges"]:
                    lil_node = lil_node['node']
                    urls.append(lil_node['display_url'])
                post["urls"] = urls
            elif node["__typename"] == 'GraphVideo':
                post["urls"] = [node["video_url"]]
            else:
                post["urls"] = [node["display_url"]]
            post["caption"] = node["edge_media_to_caption"]["edges"][0]["node"]["text"]
            post["likes"] = node["edge_media_preview_like"]["count"]
            post["comments"] = node["edge_media_to_comment"]["count"]
            post["timestamp"] = node["taken_at_timestamp"]
            if (post["id"] not in [post_n["id"] for post_n in posts]) and start_date < post["timestamp"] < fin_date:
                posts.append(post)
        return posts

    def get_reels(self, login, start=0, finish=50):
        """Получить список reels аккаунта с именем {login} от поста с номером {start}
         до поста с номером {finish}(не включая). Нумерация начинается от нуля, нулевым является самый свежий reel.
         Формат возвращаемого значения: список словарей формата {id, url(адрес контента reel),
         likes (число лайков), comments(число комментов), timestamp(дата и время поста в секундах
         от начала эпохи)}"""
        user_id = self.get_user_id(login)
        return self.get_reels_by_uid(user_id, start, finish)

    def get_reels_by_uid(self, user_id, start, finish):
        url = "https://i.instagram.com/api/v1/clips/user/"
        items = []
        has_next_page = True
        max_id = ''
        while has_next_page and finish > len(items):
            payload = {"target_user_id": user_id,
                       "page_size": 50,
                       "max_id": max_id}

            j = self.__post_json(url, payload,
                                 useragent="Instagram 123.0.0.21.114 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15")
            items += [item["media"] for item in j["items"]]
            has_next_page = j['paging_info']['more_available']
            if has_next_page:
                max_id = j['paging_info']['max_id']
        reels = []
        for item in items:
            reel = dict()
            reel["id"] = item["id"]
            reel["url"] = item["video_versions"][0]["url"]
            reel["likes"] = item["like_count"]
            reel["comments"] = item["comment_count"]
            reel["timestamp"] = item["taken_at"]
            reels.append(reel)

        return reels[start:finish]

    def get_reels_by_date(self, login, start_date, fin_date):
        """Получить список reels аккаунта с именем {login} загруженных между датами {start_date} и {fin_date}(дата и время публикации в секундах
         от начала эпохи). Нумерация начинается от нуля, нулевым является самый свежий reel.
         Формат возвращаемого значения: список словарей формата {id, url(адрес контента reel),
         likes (число лайков), comments(число комментов), timestamp(дата и время публикации в секундах
         от начала эпохи)}"""
        user_id = self.get_user_id(login)
        return self.get_reels_by_date_by_uid(user_id, start_date, fin_date)

    def get_reels_by_date_by_uid(self, user_id, start_date, fin_date):
        url = "https://i.instagram.com/api/v1/clips/user/"
        items = []
        has_next_page = True
        max_id = ''
        last_node_date = fin_date
        while has_next_page and last_node_date > start_date:
            payload = {"target_user_id": user_id,
                       "page_size": 50,
                       "max_id": max_id}

            j = self.__post_json(url, payload,
                                 useragent="Instagram 123.0.0.21.114 (iPhone; CPU iPhone OS 11_4 like Mac OS X; en_US; en-US; scale=2.00; 750x1334) AppleWebKit/605.1.15")
            items += [item["media"] for item in j["items"]]
            has_next_page = j['paging_info']['more_available']
            if has_next_page:
                max_id = j['paging_info']['max_id']
            last_node_date = items[-1]["taken_at"]
        reels = []
        for item in items:
            reel = dict()
            reel["id"] = item["id"]
            reel["url"] = item["video_versions"][0]["url"]
            reel["likes"] = item["like_count"]
            reel["comments"] = item["comment_count"]
            reel["timestamp"] = item["taken_at"]
            if fin_date > reel["timestamp"] > start_date:
                reels.append(reel)

        return reels


class NoSuchUserError(BaseException):
    pass


class IGRedirectError(BaseException):
    pass


class NoMaterialsFoundError(BaseException):
    pass

if __name__ == '__main__':
    pass
