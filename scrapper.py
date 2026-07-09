import requests
from bs4 import BeautifulSoup


def search_incruit(keyword):

	url = f"https://search.incruit.com/list/search.asp?col=job&kw={keyword}"

	r = requests.get(url)

	soup = BeautifulSoup(r.text, "html.parser")

	lis = soup.find_all("li", class_="c_col")

	jobs = []

	for li in lis:

		company = li.find(
			"a",
			class_="cpname"
		).text.strip()

		title = (
			li.find("div", class_="cell_mid")
			.find("div", class_="cl_top")
			.find("a")
			.text.strip()
		)

		location = (
			li.find("div", class_="cl_md")
			.find_all("span")[0]
			.text.strip()
		)

		link = (
			li.find("div", class_="cell_mid")
			.find("div", class_="cl_top")
			.find("a")
			.get("href")
		)

		job_data = {
			"company": company,
			"title": title,
			"location": location,
			"link": link
		}

		jobs.append(job_data)

	return jobs



def search_work24(keyword):

	url = f"https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do?searchMode=Y&srcKeyword={keyword}&pageIndex=1&resultCnt=20

	r = requests.get(url)

	soup = BeautifulSoup(r.text, "html.parser")

	trs = soup.find_all("tr")

	jobs = []

	for tr in trs:

		company = tr.find("a", class_="cp_name")
		title = tr.find("a", class_="t3_sb")
		location = tr.find("li", class_="site")

		if company and title and location:

			job_data = {
				"company": company.text.strip(),
				"title": title.text.strip(),
				"location": location.find("p").text.strip(),
				"link": "https://www.work24.go.kr" + title.get("href")
			}

			jobs.append(job_data)

	return jobs