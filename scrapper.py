import requests
from bs4 import BeautifulSoup


def search_incruit(keyword, page=1):
    # 1 -> 0
	# 2 -> 30
	# 3 -> 60
	jobs = []
	for i in range(page): #page에 3이 들어가면 i는 0, 1, 2가 들어감 
		page = 30 * i
		url = f"https://search.incruit.com/list/search.asp?col=job&kw={keyword}&startno={page}"
		r = requests.get(url)
		soup = BeautifulSoup(r.text, "html.parser")
		lis = soup.find_all("li", class_="c_col")

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

if __name__ == "__main__":
	result = search_incruit("간호사", 2)
	print(result)
	print(len(result))

def search_work24(keyword):

    url = f"https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do?searchMode=Y&srcKeyword={keyword}&pageIndex=1&resultCnt=60"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    trs = soup.select("tr:has(a.cp_name)") #선택 조건

    jobs = []

    for tr in trs:

        company = (
            tr.find("a", class_="cp_name")
            .text.strip()
        ) #여기서 a는 태그 찾기  
        
        title = (
            tr.find("a", class_="t3_sb")
            .text.strip()
        )

        location = (
            tr.find("li", class_="site")
            .find("p")
            .text.strip()
        )

        link = (
            "https://www.work24.go.kr"
            + tr.find("a", class_="t3_sb")
            .get("href") #주소 가져오는 함수
        )

        job_data = {
            "company": company,
            "title": title,
            "location": location,
            "link": link
        }

        jobs.append(job_data)

    return jobs