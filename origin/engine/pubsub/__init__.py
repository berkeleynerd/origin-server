# coding=utf-8


"""

Pubsub supports immediate (synchronous) sending of messages to 
subscribers of supported topics as well as store-and-forward sending
of messages when sync() is invoked.

We use weakrefs so as to avoid unnecessary locking of topics and
subscribers in memory. Topics can be subscribed to but the engine
is responsible for firing the events. 

Topics available:

  "actions"
      Events are callables (e.g., __call__) which are executed
      in the server tick loop. They are similar to object heartbeats
      but not the same.

  "tells"
      Messages queued be delivered to actors after all other messages
      are processed.

  "dialogs"
      Actions that spawn async dialogs (generators). It may be interesting
      to revisit this implementation with the introduction of PEP525 --
      Asynchronous Generators.

  ("monitor-location", <location name>)
      Used to monitor a location

  ("monitor-creature", <creature name>)
      Used to monitor a creature
      
"""