from flask import Flask, render_template, request, send_file, redirect
from scrapper import search_incruit, search_work24
from file import save_to_csv


app = Flask(__name__)

db = {}
page = 5

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():
    keyword = request.args.get("keyword")

    if keyword == "":
        return redirect("/")

    incruit_jobs = search_incruit(keyword, page)
    work24_jobs = search_work24(keyword)

    if keyword in db:
        jobs = db[keyword]
    else:
        jobs = incruit_jobs + work24_jobs
        db[keyword] = jobs

    return render_template(
        "search.html",
        jobs=enumerate(jobs),
        keyword=keyword,
        count=len(jobs)
    )


@app.route("/file")
def file():  # 키워드가 있으면 if문으로 처리 빠르게 하기
    keyword = request.args.get("keyword")

    if keyword == "":
        return redirect("/")

    if keyword in db:
        jobs = db[keyword]
    else:
        jobs = search_incruit(keyword, page)

    save_to_csv(jobs)

    return send_file(
        "./downloads.csv",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)