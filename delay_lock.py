import logging
import Queue
import time
import threading


class DLock(threading.Thread):
    def __init__(self, delay, name=None):
        super(DLock, self).__init__()
        self.delay = delay

        self.name = ''
        if name:
            self.name = ' (%s)' % name

        self.the_lock = threading.Event()
        self.lock_requests = Queue.Queue()

        self.unlock = threading.Event()
        self.unlocked = threading.Event()

    def run(self):
        while True:
            self.unlocked.clear()

            logging.debug('Lock%s requests: %d' % (self.name, self.lock_requests.qsize()))
            self.acquiring_thread, locked_event = self.lock_requests.get()
            if self.acquiring_thread == locked_event == None:
                logging.debug('Destroying%s' % self.name)
                break

            self.the_lock.set()
            locked_event.set()

            self.unlock.wait()
            self.the_lock.clear()
            self.unlocked.set()

            self.unlock.clear()
            time.sleep(self.delay)

    def acquire(self):
        logging.debug('Acquiring%s' % self.name)
        if not self.is_alive():
            self.start()

        locked = threading.Event()
        self.lock_requests.put((threading.current_thread(), locked, ))
        locked.wait()
        logging.debug('Acquired%s' % self.name)

    def release(self):
        logging.debug('Releasing%s' % self.name)
        if self.acquiring_thread != threading.current_thread():
            raise RuntimeError

        self.unlock.set()
        self.unlocked.wait()
        logging.debug('Released%s' % self.name)

    def destroy(self):
        logging.debug('Destroy request%s' % self.name)
        self.lock_requests.put((None, None, ))

    def __enter__(self):
        return self.acquire()

    def __exit__(self, type, value, traceback):
        return self.release()


def main():
    """Shows how to set up a simple ThreadPool, and Worker."""
    log_format = '%(asctime)s %(levelname)s [%(threadName)s] %(msg)s'
    logging.basicConfig(format=log_format, level=logging.INFO)

    lock = DLock(5)

    class Example(threading.Thread):
        def __init__(self, n):
            super(Example, self).__init__()
            self.n = n

        def run(self):
            logging.info('(%d) Acquiring lock ...' % self.n)
            lock.acquire()
            logging.info('(%d) Lock acquired, sleeping.' % self.n)
            time.sleep(10)
            logging.info('(%d) Releasing lock ...' % self.n)
            lock.release()
            logging.info('(%d) Lock released.' % self.n)

    threads = []
    for i in range(0, 3):
        t = Example(i)
        t.start()
        threads.append(t)
        time.sleep(1)

    for t in threads:
        t.join()

    lock.destroy()


if __name__ == '__main__':
    main()
