import requests
from bs4 import BeautifulSoup
from html2text import HTML2Text
import json
import os
import multiprocessing

h = HTML2Text()
h.images_to_alt = True


def request_timeout(url):
    while True:
        try:
            return requests.get(url, timeout=15)
        except:
            print("!", end="", flush=True)
            continue


def get_entries():

    for page in range(0, 134):
        print("Page " + str(page))
        r = request_timeout("https://opengameart.org/art-search-advanced?"
                            "field_art_tags_tid_op=or"
                            "&sort_by=count"
                            "&sort_order=DESC"
                            "&items_per_page=144"
                            "&page=" + str(page))

        print("Parsing...")
        soup = BeautifulSoup(r.text, "html.parser")

        for entry in soup.find_all("span", attrs={"class": "art-preview-title"}):
            for child in entry.children:
                with open("entries.txt", "a") as f:
                    f.write(child.get("href") + "\n")
                break


def download_entry(url):

    r = request_timeout("https://opengameart.org" + url)
    soup = BeautifulSoup(r.text, "html.parser")

    simple_title = os.path.split(url)[1]

    if not os.path.exists(simple_title + os.sep + "metadata.json"):

        metadata = dict()

        metadata["title"] = list(soup.find("div", attrs={"property": "dc:title"}).children)[0].text
        metadata["tags"] = list()
        for tag in soup.find_all("a", attrs={"property": "rdfs:label skos:prefLabel"}):
            metadata["tags"].append(tag.text)

        metadata["description"] = h.handle(str(soup.find("div", attrs={"class": "field-item even", "property": "content:encoded"}))).strip()
        metadata["attribution"] = h.handle(str(soup.find("div", attrs={"class": "field field-name-field-art-attribution field-type-text-long field-label-above"}))).strip()
        metadata["license"] = soup.find("div", attrs={"class": "license-name"}).text
        metadata["type"] = soup.find("a", attrs={"property": "rdfs:label skos:prefLabel", "typeof": "skos:Concept"}).text

        path = "entries" + os.sep + simple_title
        if not os.path.exists(path):
            os.mkdir(path)

        for file in soup.find_all("span", attrs={"class", "file"}):
            link = file.find("a").get("href")

            if not os.path.exists(path + os.sep + os.path.split(link)[1]):
                print(link)

                while True:
                    try:
                        response = requests.get(link, stream=True, timeout=8)

                        with open(path + os.sep + os.path.split(link)[1], 'wb') as f:
                            for chunk in response.iter_content(chunk_size=1024):
                                if chunk:
                                    f.write(chunk)
                        break
                    except:
                        print("!")

        with open(path + os.sep + "metadata.json", "w") as f:
            json.dump(metadata, f)


def download_all():
    pool = multiprocessing.Pool(processes=25)

    with open("entries.txt", "r") as f:
        pool.map(download_entry, f.read().splitlines())


if not os.path.exists("entries"):
    os.mkdir("entries")


get_entries()
download_all()
