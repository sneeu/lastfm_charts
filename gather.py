"""
"""
import datetime
import json
import logging
import pickle
import pprint
from Queue import Queue
import sys
import threading
import urllib2

import delay_lock


API_KEY = 'be29db3a53352325ef37a2cab10ca63d'
URL = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&format=json&user=%s&from=1291183200&api_key=%s&limit=200&page=%d'


class Worker(threading.Thread):
    def __init__(self, tasks):
        threading.Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception, e:
                logging.warning(e)
            self.tasks.task_done()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()


def main(user):
    logging.basicConfig(level=logging.DEBUG)

    days = {}
    days_lock = threading.Lock()
    api_lock = delay_lock.DLock(0.2)

    api_lock.acquire()
    api_lock.release()

    pool = ThreadPool(20)

    def lastfm(user, page):
        url = URL % (user, API_KEY, page, )

        with api_lock:
            response = json.loads(urllib2.urlopen(url).read())

        days_lock.acquire()

        try:
            data = response.get('recenttracks')
            if data is None:
                logging.debug(pprint.pformat(response))

            for track in data.get('track', {}):
                if 'date' in track:
                    date = datetime.date.fromtimestamp(int(track['date']['uts']))
                    days.setdefault(date, 0)
                    days[date] += 1
        except Exception, e:
            logging.warning('-' * 72)
            logging.warning('Page: %d' % page)
            logging.warning(e)
        finally:
            days_lock.release()
            logging.debug('Lock released %d' % page)

    url = URL % (user, API_KEY, 1, )
    response = json.loads(urllib2.urlopen(url).read())
    pages = int(response.get('recenttracks', {}).get('@attr', {}).get('totalPages'))

    if pages:
        logging.info('Pages: %d' % pages)
        for page in range(1, int(pages) + 1):
            pool.add_task(lastfm, user, page)

        pool.wait_completion()

        pickle.dump(days, open('%s.pickle' % user, 'w'))

    api_lock.destroy()


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        for username in sys.argv[1:]:
            main(username)
