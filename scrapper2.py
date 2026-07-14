import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/150.0.0.0 Safari/537.36"
    )
}


# --------------------------------------------------
# 0. 기본 데이터
# --------------------------------------------------

# The Guardian 리그별 일정 주소
LEAGUES = {
    "EPL": {
        "name": "프리미어리그",
        "url": (
            "https://www.theguardian.com/"
            "football/premierleague/fixtures"
        ),
        "expected": 380
    },

    "라리가": {
        "name": "라리가",
        "url": (
            "https://www.theguardian.com/"
            "football/laligafootball/fixtures"
        ),
        "expected": 380
    },

    "세리에A": {
        "name": "세리에 A",
        "url": (
            "https://www.theguardian.com/"
            "football/serieafootball/fixtures"
        ),
        "expected": 380
    },

    "리그앙": {
        "name": "리그 1",
        "url": (
            "https://www.theguardian.com/"
            "football/ligue1football/fixtures"
        ),
        "expected": 306
    }
}


# 사용자가 입력할 수 있는 리그 별명
LEAGUE_ALIASES = {
    "epl": "프리미어리그",
    "프리미어리그": "프리미어리그",
    "premier league": "프리미어리그",

    "라리가": "라리가",
    "laliga": "라리가",
    "la liga": "라리가",

    "세리에a": "세리에 A",
    "세리에 a": "세리에 A",
    "serie a": "세리에 A",

    "리그앙": "리그 1",
    "리그1": "리그 1",
    "리그 1": "리그 1",
    "ligue 1": "리그 1"
}


# 한글 팀명을 영문 검색어로 변경
TEAM_ALIASES = {
    "리버풀": "liverpool",
    "아스널": "arsenal",
    "아스날": "arsenal",
    "첼시": "chelsea",
    "맨시티": "man city",
    "맨체스터 시티": "man city",
    "맨유": "man utd",
    "맨체스터 유나이티드": "man utd",
    "토트넘": "spurs",

    "레알마드리드": "real madrid",
    "레알 마드리드": "real madrid",
    "바르셀로나": "barcelona",
    "아틀레티코": "atletico",

    "인터밀란": "inter",
    "인터 밀란": "inter",
    "ac밀란": "milan",
    "ac 밀란": "milan",
    "유벤투스": "juventus",
    "토리노": "torino",

    "파리생제르맹": "psg",
    "파리 생제르맹": "psg",
    "마르세유": "marseille"
}


# Wikipedia 문서명이 일반 팀명과 다른 팀
WIKI_PAGES = {
    "torino": "Torino_FC",
    "liverpool": "Liverpool_F.C.",
    "arsenal": "Arsenal_F.C.",
    "chelsea": "Chelsea_F.C.",
    "man city": "Manchester_City_F.C.",
    "manchester city": "Manchester_City_F.C.",
    "man utd": "Manchester_United_F.C.",
    "manchester united": "Manchester_United_F.C.",
    "spurs": "Tottenham_Hotspur_F.C.",
    "tottenham": "Tottenham_Hotspur_F.C.",
    "barcelona": "FC_Barcelona",
    "real madrid": "Real_Madrid_CF",
    "atletico": "Atlético_Madrid",
    "inter": "Inter_Milan",
    "milan": "AC_Milan",
    "juventus": "Juventus_FC",
    "psg": "Paris_Saint-Germain_F.C.",
    "marseille": "Olympique_de_Marseille"
}


DATE_PATTERN = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|"
    r"Saturday|Sunday),?\s+\d{1,2}\s+[A-Za-z]+\s+20\d{2}$"
)

TIME_PATTERN = re.compile(
    r"^(\d{1,2}[:.]\d{2})(?:\s+[A-Z]{2,5})?$"
)


# --------------------------------------------------
# 1. 공통 함수
# --------------------------------------------------

def clean_text(text):
    """여러 개의 공백을 한 칸으로 정리합니다."""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def get_soup(url):
    """웹페이지에 접속하고 BeautifulSoup 객체를 반환합니다."""

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    return soup, response.url


def next_token(tokens, start):
    """
    일정 페이지에서 다음 글자를 가져옵니다.
    Image 같은 불필요한 글자는 건너뜁니다.
    """

    skip_words = {
        "",
        "image"
    }

    index = start

    while index < len(tokens):
        token = clean_text(
            tokens[index]
        )

        if token.lower() not in skip_words:
            return token, index

        index += 1

    return "", len(tokens)


# --------------------------------------------------
# 2. The Guardian 경기 일정 크롤링
# --------------------------------------------------

def parse_schedule(soup, league_name, source_url):
    """
    Guardian 페이지에서 날짜, 시간, 홈팀, 원정팀을 가져옵니다.
    """

    tokens = []

    for text in soup.stripped_strings:
        text = clean_text(text)

        if text != "":
            tokens.append(text)

    games = []
    used_games = set()

    current_date = ""
    index = 0

    while index < len(tokens):
        token = tokens[index]

        # 날짜를 발견하면 현재 날짜로 저장
        if DATE_PATTERN.fullmatch(token):
            current_date = token
            index += 1
            continue

        time_match = TIME_PATTERN.fullmatch(token)
        is_tbc = token.upper() in ["TBC", "TBD"]

        # 시간 다음에 홈팀, v, 원정팀이 있는지 확인
        if current_date != "" and (
            time_match is not None
            or is_tbc
        ):
            home_team, home_index = next_token(
                tokens,
                index + 1
            )

            versus, versus_index = next_token(
                tokens,
                home_index + 1
            )

            away_team, away_index = next_token(
                tokens,
                versus_index + 1
            )

            if (
                home_team != ""
                and versus.lower() == "v"
                and away_team != ""
            ):
                game_key = (
                    current_date,
                    home_team,
                    away_team
                )

                if game_key not in used_games:
                    used_games.add(game_key)

                    game_time = token

                    if time_match is not None:
                        game_time = (
                            time_match.group(1)
                            .replace(".", ":")
                        )

                    games.append({
                        "league": league_name,
                        "season": "2026/27",
                        "date": current_date,
                        "time": game_time,
                        "home_team": home_team,
                        "away_team": away_team,
                        "source_url": source_url
                    })

                index = away_index + 1
                continue

        index += 1

    return games


def search_schedule(league_key):
    """한 리그의 전체 일정을 수집합니다."""

    league = LEAGUES[league_key]

    try:
        soup, real_url = get_soup(
            league["url"]
        )

        games = parse_schedule(
            soup,
            league["name"],
            real_url
        )

        print(
            league["name"],
            "일정:",
            len(games),
            "건"
        )

        return games, real_url, ""

    except requests.RequestException as error:
        print(
            league["name"],
            "일정 수집 실패:",
            error
        )

        return [], league["url"], str(error)


def collect_all_games():
    """네 리그의 전체 일정을 한 번에 수집합니다."""

    all_games = []
    status = {}

    for league_key in LEAGUES:
        games, source_url, error = search_schedule(
            league_key
        )

        all_games += games

        status[league_key] = {
            "league": LEAGUES[league_key]["name"],
            "count": len(games),
            "expected": LEAGUES[league_key]["expected"],
            "source_url": source_url,
            "error": error
        }

        # 너무 빠르게 요청하지 않도록 잠시 대기
        time.sleep(0.5)

    print(
        "전체 일정:",
        len(all_games),
        "건"
    )

    return all_games, status


def change_keyword(keyword):
    """리그명과 한글 팀명을 검색 가능한 글자로 바꿉니다."""

    search_word = keyword.lower().strip()

    if search_word in LEAGUE_ALIASES:
        return LEAGUE_ALIASES[
            search_word
        ].lower()

    if search_word in TEAM_ALIASES:
        return TEAM_ALIASES[
            search_word
        ]

    return search_word


def search_games(all_games, keyword):
    """전체 일정에서 리그명 또는 팀명을 검색합니다."""

    if keyword == "전체":
        return all_games

    search_word = change_keyword(
        keyword
    )

    results = []

    for game in all_games:
        league = game["league"].lower()
        home_team = game["home_team"].lower()
        away_team = game["away_team"].lower()

        if (
            search_word in league
            or search_word in home_team
            or search_word in away_team
        ):
            results.append(game)

    return results


# --------------------------------------------------
# 3. Google News RSS 뉴스 크롤링
# --------------------------------------------------

def make_news_query(keyword):
    """검색어 뒤에 football을 붙여 축구 뉴스만 검색합니다."""

    if keyword == "전체":
        return "European football"

    search_word = keyword.lower().strip()

    if search_word in LEAGUE_ALIASES:
        return (
            LEAGUE_ALIASES[search_word]
            + " football"
        )

    if search_word in TEAM_ALIASES:
        return (
            TEAM_ALIASES[search_word]
            + " football"
        )

    return keyword + " football"


def search_news(keyword, limit=10):
    """Google News RSS에서 관련 뉴스를 가져옵니다."""

    url = "https://news.google.com/rss/search"

    try:
        response = requests.get(
            url,
            params={
                "q": make_news_query(keyword),
                "hl": "ko",
                "gl": "KR",
                "ceid": "KR:ko"
            },
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

    except (
        requests.RequestException,
        ET.ParseError
    ) as error:
        print(
            "뉴스 수집 실패:",
            error
        )

        return []

    news = []

    for item in root.findall(".//item"):
        title_tag = item.find("title")
        link_tag = item.find("link")
        date_tag = item.find("pubDate")
        source_tag = item.find("source")

        if title_tag is None or link_tag is None:
            continue

        news.append({
            "title": clean_text(
                title_tag.text or ""
            ),
            "link": clean_text(
                link_tag.text or ""
            ),
            "published": clean_text(
                date_tag.text or ""
            ) if date_tag is not None else "",
            "source": clean_text(
                source_tag.text or ""
            ) if source_tag is not None else ""
        })

        if len(news) >= limit:
            break

    return news


# --------------------------------------------------
# 4. Wikipedia 팀 스쿼드 크롤링
# --------------------------------------------------

def empty_squad(message):
    """스쿼드가 없을 때 사용할 기본값입니다."""

    return {
        "team_name": "",
        "players": [],
        "source_url": "",
        "message": message
    }


def find_wikipedia_page(keyword):
    """팀의 Wikipedia 문서 주소를 찾습니다."""

    search_word = keyword.lower().strip()

    if search_word in TEAM_ALIASES:
        search_word = TEAM_ALIASES[
            search_word
        ]

    # 자주 검색하는 팀은 저장된 문서명 사용
    if search_word in WIKI_PAGES:
        page_name = WIKI_PAGES[
            search_word
        ]

        url = (
            "https://en.wikipedia.org/wiki/"
            + quote(
                page_name,
                safe="()._-"
            )
        )

        return get_soup(url)

    # 저장된 팀이 아니면 Wikipedia 검색 이용
    search_url = (
        "https://en.wikipedia.org/"
        "w/index.php"
    )

    response = requests.get(
        search_url,
        params={
            "search": (
                search_word
                + " football club"
            )
        },
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # 검색 결과가 팀 문서로 바로 이동한 경우
    if "/wiki/" in response.url:
        return soup, response.url

    first_link = soup.select_one(
        ".mw-search-result-heading a"
    )

    if first_link is None:
        raise ValueError(
            "팀 문서를 찾지 못했습니다."
        )

    team_url = urljoin(
        "https://en.wikipedia.org",
        first_link.get("href")
    )

    return get_soup(team_url)


def get_nationality(cell):
    """국적 칸에서 국적 이름을 가져옵니다."""

    image = cell.find("img")

    if image is not None:
        nationality = (
            image.get("alt")
            or image.get("title")
            or ""
        )

        if nationality != "":
            return clean_text(
                nationality
            )

    return clean_text(
        cell.get_text(
            " ",
            strip=True
        )
    )


def get_player_name(cell):
    """
    선수 칸에서 선수 이름을 가져옵니다.

    사진은 선수 링크 주소가 아니라 선수 이름으로 찾습니다.
    Wikipedia 링크 형식이 바뀌어도 사진 검색이 가능해집니다.
    """

    links = cell.find_all(
        "a",
        href=True
    )

    # 선수 이름 링크는 보통 칸의 마지막 링크입니다.
    for link in reversed(links):
        player_name = clean_text(
            link.get_text(
                " ",
                strip=True
            )
        )

        if player_name != "":
            return player_name

    return clean_text(
        cell.get_text(
            " ",
            strip=True
        )
    )


def parse_player(cells):
    """표의 네 칸을 선수 한 명의 딕셔너리로 만듭니다."""

    if len(cells) < 4:
        return None

    number = clean_text(
        cells[0].get_text(
            " ",
            strip=True
        )
    )

    position = clean_text(
        cells[1].get_text(
            " ",
            strip=True
        )
    )

    nationality = get_nationality(
        cells[2]
    )

    name = get_player_name(
        cells[3]
    )

    if (
        name == ""
        or name.lower() == "player"
        or position.lower() in ["pos", "position"]
    ):
        return None

    return {
        "number": number or "-",
        "position": position or "-",
        "nationality": nationality or "-",
        "name": name,
        "image_url": ""
    }


def parse_squad(soup):
    """Wikipedia 선수단 표에서 선수 목록을 가져옵니다."""

    players = []
    used_names = set()

    for table in soup.select("table"):
        table_text = clean_text(
            table.get_text(
                " ",
                strip=True
            )
        ).lower()

        # 선수단 표인지 간단하게 확인
        if (
            "player" not in table_text
            or "pos" not in table_text
        ):
            continue

        for row in table.select("tr"):
            cells = row.find_all(
                "td",
                recursive=False
            )

            if len(cells) < 4:
                continue

            # 한 행에 선수가 두 명이면 4칸씩 나누기
            for start in range(
                0,
                len(cells),
                4
            ):
                group = cells[
                    start:start + 4
                ]

                player = parse_player(
                    group
                )

                if player is None:
                    continue

                name_key = player[
                    "name"
                ].lower()

                if name_key in used_names:
                    continue

                used_names.add(name_key)
                players.append(player)

        if len(players) > 0:
            break

    return players[:40]


# --------------------------------------------------
# 5. Wikipedia 선수 사진 API
# --------------------------------------------------

def change_api_title(title, title_map):
    """
    Wikipedia API가 바꾼 문서 제목을 최종 제목으로 변환합니다.

    예:
    Alisson → Alisson Becker
    """

    changed_title = title

    for _ in range(3):
        if changed_title not in title_map:
            break

        changed_title = title_map[
            changed_title
        ]

    return changed_title


def add_player_images(players):
    """
    선수 이름을 이용해 Wikipedia API에서 사진을 가져옵니다.

    기존 코드처럼 선수 링크 주소에 의존하지 않기 때문에
    Wikipedia HTML 링크 형식이 달라져도 사진을 찾을 수 있습니다.
    """

    player_names = []

    for player in players:
        if player["name"] != "":
            player_names.append(
                player["name"]
            )

    if len(player_names) == 0:
        return players

    # API 제한을 피하기 위해 20명씩 나누어 요청
    for start in range(
        0,
        len(player_names),
        20
    ):
        name_group = player_names[
            start:start + 20
        ]

        try:
            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "formatversion": 2,
                    "prop": "pageimages",
                    "piprop": "thumbnail",
                    "pithumbsize": 180,
                    "pilicense": "any",
                    "redirects": 1,
                    "titles": "|".join(
                        name_group
                    )
                },
                headers=HEADERS,
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

        except (
            requests.RequestException,
            ValueError
        ) as error:
            print(
                "선수 사진 수집 실패:",
                error
            )

            continue

        query = data.get(
            "query",
            {}
        )

        title_map = {}

        # API가 문서 제목의 띄어쓰기 등을 정리한 정보
        for item in query.get(
            "normalized",
            []
        ):
            old_title = item.get(
                "from",
                ""
            )

            new_title = item.get(
                "to",
                ""
            )

            if old_title != "" and new_title != "":
                title_map[
                    old_title
                ] = new_title

        # 다른 이름의 문서로 이동된 정보
        for item in query.get(
            "redirects",
            []
        ):
            old_title = item.get(
                "from",
                ""
            )

            new_title = item.get(
                "to",
                ""
            )

            if old_title != "" and new_title != "":
                title_map[
                    old_title
                ] = new_title

        image_map = {}

        for page in query.get(
            "pages",
            []
        ):
            page_title = page.get(
                "title",
                ""
            )

            thumbnail = page.get(
                "thumbnail",
                {}
            )

            image_url = thumbnail.get(
                "source",
                ""
            )

            if page_title != "":
                image_map[
                    page_title
                ] = image_url

        # 선수 이름을 최종 Wikipedia 제목으로 바꾼 뒤 사진 연결
        for player in players:
            if player["name"] not in name_group:
                continue

            final_title = change_api_title(
                player["name"],
                title_map
            )

            player["image_url"] = image_map.get(
                final_title,
                ""
            )

    photo_count = 0

    for player in players:
        if player["image_url"] != "":
            photo_count += 1

    print(
        "선수 사진:",
        photo_count,
        "/",
        len(players),
        "명"
    )

    return players


def search_team_squad(keyword):
    """
    팀명을 검색했을 때 현재 스쿼드와 선수 사진을 가져옵니다.
    """

    search_word = keyword.lower().strip()

    # 전체 또는 리그 검색에는 특정 팀이 없음
    if (
        keyword == "전체"
        or search_word in LEAGUE_ALIASES
    ):
        return empty_squad(
            "리그명 검색에는 팀 스쿼드가 표시되지 않습니다."
        )

    try:
        soup, source_url = find_wikipedia_page(
            keyword
        )

        title_tag = soup.select_one(
            "h1"
        )

        team_name = keyword

        if title_tag is not None:
            team_name = clean_text(
                title_tag.get_text(
                    " ",
                    strip=True
                )
            )

        players = parse_squad(
            soup
        )

        players = add_player_images(
            players
        )

        if len(players) == 0:
            return {
                "team_name": team_name,
                "players": [],
                "source_url": source_url,
                "message": "선수단 표를 찾지 못했습니다."
            }

        return {
            "team_name": team_name,
            "players": players,
            "source_url": source_url,
            "message": ""
        }

    except (
        requests.RequestException,
        ValueError
    ) as error:
        print(
            "스쿼드 수집 실패:",
            error
        )

        return empty_squad(
            "제대로 검색하세요."
        )
