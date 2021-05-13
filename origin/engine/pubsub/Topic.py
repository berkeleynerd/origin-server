# coding=utf-8

import threading
import time
import weakref

from origin.engine.pubsub.Subscriber import Subscriber


#
# Represents a topic which may be subscribed to to send and receive events.
# Topics are provided by the static_topic function.
#
class Topic(object):


    topics = {}
    __lock = threading.Lock()


    def __init__(self, name):

        self.name = name
        self.subscribers = set()
        self.events = []
        self.last_event = time.time()


    @property
    def idle_time(self):
        return time.time() - self.last_event


    def destroy(self):

        self.sync()
        del Topic.topics[self.name]
        self.name = "<defunct>"
        del self.subscribers
        del self.events


    def subscribe(self, subscriber):

        if not isinstance(subscriber, Subscriber):
            raise TypeError("subscriber needs to be a Subscriber")

        self.subscribers.add(weakref.ref(subscriber))


    def unsubscribe(self, subscriber):

        self.subscribers.discard(weakref.ref(subscriber))


    def send(self, event, synchronous=False):

        self.events.append(event)
        self.last_event = time.time()

        if synchronous:
            return self.sync()


    def sync(self):

        events, self.events = self.events, []
        results = []

        for event in events:
            results.extend(self.__sync_event(event))

        return results


    def __sync_event(self, event):

        results = []

        for subber_ref in self.subscribers:

            subber = subber_ref()

            if subber is not None:

                try:
                    result = subber.event(self.name, event)
                    results.append(result)

                except Subscriber.defer:
                    pass

        return results


    #
    # Create a topic object as a singleton. Name should be either a string or a tuple.
    #
    @staticmethod
    def static_topic(name):

        with Topic.__lock:

            if name in Topic.topics:
                return Topic.topics[name]

            instance = Topic.topics[name] = Topic(name)

            return instance


    #
    # Push all pending events to subscribers.
    #
    @staticmethod
    def static_sync(topic=None):

        if topic:

            return Topic.topics[topic].sync()

        else:

            for t in list(Topic.topics.values()):
                t.sync()


    #
    # Returns a dictionary containing a topic's current count of pending events, idle time, and number of subscribers
    #
    @staticmethod
    def pending(topicname=None):

        with Topic.__lock:
            topics = [Topic.topics[topicname]] if topicname else Topic.topics.values()
            return {t.name: (len(t.events), t.idle_time, len(t.subscribers)) for t in topics}


    #
    # Unsubscribe an object from all topics
    #
    @staticmethod
    def unsubscribe_all(subscriber):

        for topic in list(Topic.topics.values()):
            topic.unsubscribe(subscriber)