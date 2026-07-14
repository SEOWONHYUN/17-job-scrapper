import csv
from pathlib import Path


def save_to_csv(
    games,
    news,
    squad,
    csv_path
):
    """
    현재 검색한 일정, 뉴스, 스쿼드를
    하나의 CSV 파일에 저장합니다.
    """

    csv_path = Path(csv_path)

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "구분",
            "리그",
            "시즌",
            "날짜",
            "시간",
            "홈팀",
            "원정팀",
            "팀",
            "등번호",
            "포지션",
            "국적",
            "선수명",
            "선수 사진",
            "뉴스 제목",
            "언론사",
            "게시일",
            "링크"
        ])

        # 경기 일정 저장
        for game in games:
            writer.writerow([
                "경기 일정",
                game["league"],
                game["season"],
                game["date"],
                game["time"],
                game["home_team"],
                game["away_team"],
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                game["source_url"]
            ])

        # 뉴스 저장
        for article in news:
            writer.writerow([
                "관련 뉴스",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                article["title"],
                article["source"],
                article["published"],
                article["link"]
            ])

        # 팀 스쿼드 저장
        for player in squad.get(
            "players",
            []
        ):
            writer.writerow([
                "팀 스쿼드",
                "",
                "",
                "",
                "",
                "",
                "",
                squad.get(
                    "team_name",
                    ""
                ),
                player["number"],
                player["position"],
                player["nationality"],
                player["name"],
                player["image_url"],
                "",
                "",
                "",
                squad.get(
                    "source_url",
                    ""
                )
            ])

    return csv_path
