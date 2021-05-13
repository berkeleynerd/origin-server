# coding=utf-8

#
# Call to remove a session
# The exception is the last message sent to the player
#
class SessionClose(Exception):

    def __init__(self, message, content_type="text/html"):
        print("Session closing...")
        super(SessionClose, self).__init__(message)
        self.content_type = content_type