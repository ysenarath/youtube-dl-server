from __future__ import unicode_literals
import queue
import threading
import logging
from flask import Flask, request
import youtube_dl
import os

from config import Config
from response import SuccessResponse

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)

config = Config()

q = queue.Queue()
r = []


@app.route('/')
def youtube_dl_server():
    return SuccessResponse().build()


@app.route('/download')
def download():
    url = request.args.get('url', '')
    logger.info('Adding URL {} to the Queue'.format(url))
    item = {'url': url, 'status': 'queued', 'progress': 0}
    item['eta'] = 'N/A'
    item['speed'] = 0
    item['elapsed'] = 0
    q.put(item)
    queue_list = list(q.queue)
    return SuccessResponse(queue_list).build()


@app.route('/downloads/list')
def list_downloads():
    global r
    logger.info('Getting the Queues')
    queue_list = r + list(q.queue)
    return SuccessResponse(queue_list).build()


@app.route('/downloads/clear')
def clear_downloads():
    global r
    logger.info('Clearing the Lists')
    r = []
    queue_list = r + list(q.queue)
    return SuccessResponse(queue_list).build()


def download_dl(item):
    logger.info('Procesing URL {}'.format(item['url']))

    def progress_hook(d):
        item['status'] = d['status']
        item['eta'] = d['eta'] if 'eta' in d else 'N/A'
        item['speed'] = d['speed'] if 'speed' in d else 0
        item['elapsed'] = d['elapsed'] if 'elapsed' in d else item['elapsed']
        if 'fragment_index' in d and 'fragment_count' in d:
            item['progress'] = d['fragment_index'] / d['fragment_count']
        else:
            item['progress'] = 'N/A'
    ydl_opts = {
        'progress_hooks': [progress_hook],
        'outtmpl': os.path.join(config.download_path, '%(title)s.%(ext)s')
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([item['url']])
    except:
        pass


def worker():
    while True:
        item = q.get()
        r.append(item)
        download_dl(item)
        q.task_done()


for i in range(config.num_worker_threads):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()

q.join()

logger.info('Application is Starting... [OK]')
