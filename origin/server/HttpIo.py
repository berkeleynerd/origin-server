# coding=utf-8

import sys

from origin.engine.Engine import Engine


#
# WSGI XHR IO implementation
# Functions as a compliant WSGI application with built-in HTTP(S) server
#
class HttpIo(object):


    def __init__(self, player_connection):

        self.player_connection = player_connection
        self.html_to_browser = []     # the lines that need to be displayed in the player's browser
        self.out_of_band = []         # special out of band actions (such as 'clear')
        self.last_output_line = None
        self.dont_echo_next = False   # used to hide password or generally prevent echoing of input back to the client


    #
    # Called on server shutdown
    #
    def destroy(self):
        pass

    #
    # Clear the player's screen
    #
    def clear_screen(self):
        self.out_of_band.append("clear")
        self.dont_echo_next = True


    #
    # Format internal text if necessary
    #
    def render_output(self, paragraphs, **params):
        for text in paragraphs:
            self.html_to_browser.append(text)


    #
    # Write specified text to the client
    #
    def output(self, *lines):
        self.last_output_line = lines[-1]
        for line in lines:
            self.output_no_newline(line)


    #
    # Write only a single line of text to the client without adding a new-line
    #
    def output_no_newline(self, text):
        self.last_output_line = text
        self.html_to_browser.append(text)


    #
    # Called by the PlayerConnection object if something terrible happens
    # and we need to kill the session
    #
    def critical_error(self):
        trace = "".join(Engine.formatTraceback())
        print(trace, file=sys.stderr)