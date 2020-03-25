from queue import Queue
from threading import Thread
from robobrowser import RoboBrowser
import re
import time
from requests import Session
from urllib.parse import unquote


class Downloader():
    def __init__(self, proxy=None, worker_num=0):
        self.worker_num = worker_num
        session = Session()
        if proxy is not None:
            session.proxies = {'http': proxy, 'https': proxy}
        self.browser = RoboBrowser(history=True,
                                   parser='html.parser',
                                   session=session)

    def get_book_page_list(self, page):
        self.browser.open(f'https://lelibros.online/page/{page}/')
        return [
            f"https://lelibros.online{book['href']}"
            for book in self.browser.find_all("a", class_="down")
        ]

    def get_download_link(self, book_link):
        self.browser.open(book_link)
        return self.browser.find('a', title="Download EPUB")['href']

    def download_book(self, url):
        try:
            filename = re.search(r"[0-9a-zA-z-.' ]*\.epub", unquote(url)).group(0)
            self.browser.open(url)
            with open(f"books/{filename}", "wb") as epub_file:
                epub_file.write(self.browser.response.content)
            return filename
        except:
            return "Error on download, file not available?"

    def download_full_page(self, page):
        print(f"Worker {self.worker_num} downloading Page: {page}")
        books = self.get_book_page_list(page)
        for book in books:
            download_url = self.get_download_link(book)
            print(f"Worker: {self.worker_num} on page: {page} ->",
                  self.download_book(download_url))


class Worker(Thread):
    def __init__(self, queue, worker_number, proxy=None):
        Thread.__init__(self)
        self.queue = queue
        self.downloader = Downloader(proxy, worker_number)
        self.wrk_num = worker_number

    def run(self):
        while True:
            page = self.queue.get()
            try:
                self.downloader.download_full_page(page)
            finally:
                self.queue.task_done()


def main():
    pages = [x + 1 for x in range(217)]
    proxies = [None, "https://188.168.75.254:56899"]
    queue = Queue()
    for x in range(10):
        worker = Worker(queue, x)
        worker.daemon = True
        worker.start()

    for page in pages:
        queue.put(page)

    queue.join()


if __name__ == '__main__':
    start_time = time.time()
    main()
    print(time.time() - start_time, "seconds")
