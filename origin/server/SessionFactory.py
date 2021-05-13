# coding=utf-8

import hashlib
import random
import sys
import time


#
# The SessionFactory class manages the lifecycle of session data
#
class SessionFactory(object):


    def __init__(self):
        self.storage = {}


    def new_id(self):
        string = "%d%d%f" % (random.randint(0, sys.maxsize), id(self), time.time())
        return hashlib.sha1(string.encode("ascii")).hexdigest()


    def load(self, sid):

        sid = sid or self.new_id()

        if sid not in self.storage:

            # Create a new session and store it if there isn't one already matching the provided key
            session = {
                "id": sid,
                "created": time.time()
            }

            self.storage[sid] = session

        return self.storage[sid]


    def save(self, session):

        # Create a new session id and store it if necessary
        if not session["id"]:
            sid = self.new_id()
            session["id"] = sid
        else:
            sid = session["id"]

        # session["id"] = sid = session["id"] or self.new_id()

        # store the provided session using the session id as the key
        self.storage[sid] = session

        return sid


    def delete(self, sid):

        if sid in self.storage:
            del self.storage[sid]