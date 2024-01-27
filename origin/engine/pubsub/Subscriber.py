# coding=utf-8


#
# Base class for all subscribers
#
class Subscriber(object):

    #
    # Override this event receive method in a subclass
    #
    def event(self, topicname, event):
        raise NotImplementedError("Implement event in a subclass.")

    #
    # Raise this exception from event if you are not ready to defer processing the event.
    #
    class defer(Exception):
        pass