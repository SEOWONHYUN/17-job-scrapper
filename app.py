from flask import Flask, render_template, request, send_file, redirect
from scrapper import search_incruit, search_work24
from file import save_to_csv


app = Flask(__name__)

db = {}
page = 2


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

    jobs = incruit_jobs + work24_jobs

    db[keyword] = jobs

    return render_template(
    	"search.html",
    	incruit_jobs=enumerate(incruit_jobs),
    	work24_jobs=enumerate(work24_jobs),
    	keyword=keyword,
    	count=len(jobs),
    	incruit_count=len(incruit_jobs),
    	work24_count=len(work24_jobs)
)


@app.route("/file")
def file():
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
    app.run(debug=True, port=5001)