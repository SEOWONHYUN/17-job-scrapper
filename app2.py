from pathlib import Path

from flask import Flask, render_template, request, redirect, send_file

from scrapper2 import (
    collect_all_games,
    search_games,
    search_news,
    search_team_squad
)

from file2 import save_to_csv


app = Flask(__name__)


# 크롤링한 데이터를 잠시 저장하는 공간
db = {
    "all_games": [],
    "status": {},

    "games": [],
    "news": [],
    "squad": {},

    "news_cache": {},
    "squad_cache": {}
}


@app.route("/")
def home():
    return render_template("index2.html")


@app.route("/search")
def search():
    keyword = request.args.get("keyword", "").strip()

    # 검색어가 없으면 처음 화면으로 이동
    if keyword == "":
        return redirect("/")

    # 첫 검색 때만 네 리그 전체 일정을 수집
    if len(db["all_games"]) == 0:
        all_games, status = collect_all_games()

        db["all_games"] = all_games
        db["status"] = status

    # 일정 검색
    games = search_games(
        db["all_games"],
        keyword
    )

    # 같은 검색어의 뉴스와 스쿼드는 다시 크롤링하지 않음
    cache_key = keyword.lower()

    if cache_key not in db["news_cache"]:
        db["news_cache"][cache_key] = search_news(
            keyword
        )

    if cache_key not in db["squad_cache"]:
        db["squad_cache"][cache_key] = search_team_squad(
            keyword
        )

    news = db["news_cache"][cache_key]
    squad = db["squad_cache"][cache_key]

    # CSV 다운로드를 위해 현재 검색 결과 저장
    db["games"] = games
    db["news"] = news
    db["squad"] = squad

    return render_template(
        "result2.html",
        keyword=keyword,
        games=games,
        news=news,
        squad=squad,
        total_count=len(db["all_games"]),
        status=db["status"]
    )


@app.route("/download")
def download():
    csv_path = (
        Path(__file__).parent
        / "football_results2.csv"
    )

    save_to_csv(
        db["games"],
        db["news"],
        db["squad"],
        csv_path
    )

    return send_file(
        csv_path,
        as_attachment=True
    )


@app.route("/refresh")
def refresh():
    # 저장된 데이터와 캐시를 모두 비움
    db["all_games"] = []
    db["status"] = {}

    db["games"] = []
    db["news"] = []
    db["squad"] = {}

    db["news_cache"] = {}
    db["squad_cache"] = {}

    return redirect("/")


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5002
    )
