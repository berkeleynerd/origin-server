# coding=utf-8

from origin import context
from origin.engine.Context import Context


#
# Handles the player and their associated connection and provides high level input and output processing
#
class PlayerConnection(object):


    def __init__(self, player=None, io=None):

        self.player = player
        self.io = io


    #
    # Retrieves pending output, formats it if applicable, then clears the buffer.
    # If there is nothing to output return None.
    #
    def get_output(self):

        formatted = self.io.render_output(self.player._output.get_paragraphs())

        return formatted or None


    @property
    def last_output_line(self):
        return self.io.last_output_line


    @property
    def idle_time(self):
        return self.player.idle_time


    @property
    def me(self):
        return self.player


    #
    # Send buffered output to the player's client device
    #
    def write_output(self):

        if not self.io:
            return

        output = self.get_output()

        if output:
            self.io.output(output.rstrip())


    #
    # Send data directly to the player's device without buffering or formatting
    #
    def output(self, *lines):
        self.io.output(*lines)


    #
    # As with output() but sends only a single line of text without appending a newline.
    #
    def output_no_newline(self, line):
        self.io.output_no_newline(line)


    def clear_screen(self):
        self.io.clear_screen()


    def critical_error(self):
        self.io.critical_error()


    def destroy(self):

        if self.io:
            self.io.destroy()
            self.io = None

        if self.player:
            ctx = Context(context.engine, None, context.config, self)
            self.player.destroy(ctx)
            self.player = None
