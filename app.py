from flask import Flask, render_template, request

from scrapper import search_incruit, search_work24


app = Flask(__name__)


@app.route("/")
def home():
	return render_template("index.html")


@app.route("/search")
def search():

	keyword = request.args.get("keyword")

	incruit_jobs = search_incruit(keyword)
	work24_jobs = search_work24(keyword)

	jobs = incruit_jobs + work24_jobs

	return render_template(
		"search.html",
		jobs=enumerate(jobs)
	)


if __name__ == "__main__":
	app.run(debug=True)