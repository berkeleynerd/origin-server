# coding=utf-8

from wsgiref.simple_server import WSGIRequestHandler


#
# Suppresses log entries which, because of constant XHR polling, provide
# little useful information.
#
class NoLoggingRequestHandler(WSGIRequestHandler):


    def log_message(self, format, *args):
        pass