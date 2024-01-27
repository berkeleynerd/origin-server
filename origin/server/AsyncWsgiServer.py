# coding=utf-8

from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer

#
# ThreadingMixIn allows provides a multi-threaded wsgi server
#
class AsyncWsgiServer(ThreadingMixIn, WSGIServer):

    request_queue_size = 200    # Support more than default 50 threads
    daemon_threads = False      # Don't exit until all threads have exited
