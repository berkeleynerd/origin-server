# coding=utf-8

import collections
import datetime
import heapq
import inspect
import sys
import threading
import time
import traceback

from origin.parser import Lang
from origin.common.errors.RetryVerb import RetryVerb
from origin.common.errors.RetryParse import RetryParse
from origin.common.errors.AsyncDialog import AsyncDialog
from origin.common.errors.ActionRefused import ActionRefused
from origin.common.errors.ParseError import ParseError

from origin.common.errors.SessionExit import SessionExit

from origin import context
from origin.actions.Actions import Actions
from origin.engine.Deferred import Deferred
from origin.engine.GameTime import GameTime
from origin.engine.Context import Context
from origin.engine.pubsub.Subscriber import Subscriber
from origin.engine.pubsub.Topic import Topic
from origin.objects.creatures.players import Player
from origin.objects.creatures.players.Accounts import Accounts
from origin.objects.creatures.players.PlayerConnection import PlayerConnection
from origin.objects.creatures.players.PlayerNaming import PlayerNaming
from origin.common.errors.NotDefaultVerb import NotDefaultVerb
from origin.common.errors.UnknownVerbException import UnknownVerbException
from origin.server.App import App

from origin.adventure.adventure import Game
import origin.adventure.regions


#
# The game engine initializes and processes game artifacts including the main loop, connections, and state
#
class Engine(Subscriber):


    topic_actions = Topic.static_topic("actions")
    topic_tells = Topic.static_topic("tells")
    topic_dialogs = Topic.static_topic("dialogs")


    def __init__(self):

        self.heartbeats = set()
        self.unbound_exits = []
        self.deferreds_lock = threading.Lock()
        self.server_started = datetime.datetime.now().replace(microsecond=0)
        self.server_loop_durations = collections.deque(maxlen=10)
        self.actions = Actions()
        self.regions = origin.adventure.regions
        self.game = Game()
        self.config = self.game.get_config()
        self.game_clock = GameTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        self.__stop_mainloop = True

        # Using heapq for heap management
        self.deferreds = []

        # Map all player connection objects to a tuple of (dialog, validator, echo_input)
        self.waiting_for_input = {}

        # Map all player names to their respective connection objects.
        self.all_players = {}

        Engine.topic_actions.subscribe(self)
        Engine.topic_tells.subscribe(self)
        Engine.topic_dialogs.subscribe(self)

        self.accounts = Accounts()


    #
    # Start the game engine main loop
    # The main loop executes in the primary thread
    # The WSGI HTTP server runs as a background thread thanks to ThreadingMixIn
    #
    def start(self):

        context.engine = self
        context.config = self.config

        self.game.init(self)

        self.config.player_start = self.game.player_start
        self.config.sysop_start = self.game.sysop_start

        wsgi_server = App.create_server(self)
        wsgi_thread = threading.Thread(name="wsgi", target=wsgi_server.serve_forever)
        wsgi_thread.daemon = True
        wsgi_thread.start()

        self.__print_game_intro(None)
        self._start_main_loop()


    #
    # Start the game engine main loop
    #
    def _start_main_loop(self):

        self.__stop_mainloop = False
        while not self.__stop_mainloop:

            try:

                while not self.__stop_mainloop:
                    self.__main_loop()

            except:

                print("Error processing main loop : \n", "".join(Engine.formatTraceback()), file=sys.stderr)
                exit(0)


    #
    # Process player input and output until the server terminates
    #
    def __main_loop(self):

        loop_duration = 0
        previous_server_tick = 0

        while not self.__stop_mainloop:

            # Push all pending events to subscribers
            Topic.static_sync("dialogs")

            # Send any buffered output to the player's client device
            for conn in self.all_players.values():
                conn.write_output()

            # Wait for server tick
            wait_time = max(0.01, self.config.server_tick_time - loop_duration)
            while wait_time > 0:

                # If we have player input break to process it
                if any(conn.player.input_is_available.is_set() for conn in self.all_players.values()):
                    break

                # Try to never block more than a tenth of a second without checking for player input
                sub_wait = min(0.1, wait_time)
                time.sleep(sub_wait)

                wait_time -= sub_wait

            # We track loop duration to dynamically adjust tick wait time
            loop_start = time.time()

            # Process player input
            for conn in list(self.all_players.values()):

                # Any input pending for this player?
                if conn.player.input_is_available.is_set():

                    try:

                        # Are we processing direct input sent from the user?
                        if conn in self.waiting_for_input:

                            dialog, validator, echo_input = self.waiting_for_input.pop(conn)
                            response = conn.player.get_pending_input()[0]

                            if validator:

                                try:

                                    response = validator(response)

                                except ValueError as x:

                                    # We didn't like the user's response so reprompt them using the ValueError message
                                    # payload or a standard reprompt if none was provided.
                                    prompt = conn.last_output_line
                                    conn.io.dont_echo_next = not echo_input
                                    conn.output(str(x) or "That does not appear to be a valid response. Please try again.")

                                    # Display the input prompt again and reschedule processing the response.
                                    conn.output_no_newline(prompt)
                                    self.waiting_for_input[conn] = (dialog, validator, echo_input)

                                    continue

                            self.__continue_dialog(conn, dialog, response)

                        # No, just a standard action
                        else:

                            self._process_player_input(conn)

                    # Usually happens when someone uses ctrl-c to end the game server
                    except (KeyboardInterrupt, EOFError):
                        print("PROCESSING KEYBOARD INTERRUPT or EOF ERROR")
                        exit(0)

                    # If player is wrapping up and logging out say goodbye and send them any last
                    # messages pending for them.
                    except SessionExit as e:
                        self.game.goodbye(conn.player)
                        Engine.topic_tells.send(lambda conn=conn: self._disconnect(conn))

                    # Something unexpected has gone terribly wrong.
                    except Exception:

                        tb = "".join(Engine.formatTraceback())
                        txt = "\n* A Serious internal error has occurred :\n" + tb
                        print(txt)
                        conn.player.tell("A serious error has occurred on the server. Someone will notice and take "
                                         "care of it as soon as possible.")

            # Send any pending messages
            Topic.static_sync("tells")

            # Process a server tick and keep track of length of execution
            now = time.time()
            if now - previous_server_tick >= self.config.server_tick_time:
                self._tick()
                previous_server_tick = now

            loop_duration = time.time() - loop_start

            # Store some metrics about engine performance that can be reported to a Sysop using the server action.
            self.server_loop_durations.append(loop_duration)


    #
    # Process a server tick event, including:
    #
    # Advancing the game clock
    # Processing heartbeats
    # Processing deferred functions
    # Fullfilling subscriptions
    # Emptying output buffers
    # Kicking idle players
    # Cleaning up monitor topics
    #
    def _tick(self):

        # Advance the game clock
        self.game_clock.add_realtime(datetime.timedelta(seconds=self.config.server_tick_time))

        # Process heartbeats
        ctx = Context(self, self.game_clock, self.config, None)
        for obj in self.heartbeats:
            obj.heartbeat(ctx)

        # Process deferreds
        while self.deferreds:

            deferred = None
            with self.deferreds_lock:
                if self.deferreds:
                    deferred = self.deferreds[0]
                    if deferred.due <= self.game_clock.clock:
                        deferred = heapq.heappop(self.deferreds)
                    else:
                        deferred = None
                        break

            # Actually calling the deferred function must be handled outside the lock
            # so it can schedule a new deferred.
            if deferred:

                try:
                    deferred(ctx=ctx)
                except Exception:
                    self.__report_deferred_exception(deferred)

        # Sync all topics (fulfill all subscriptions)
        Topic.static_sync()

        # Send pending messages to players
        for name, conn in list(self.all_players.items()):

            # Does this connection still look good?
            if conn.player and conn.io and conn.player.location:

                # Sysop timeout can be different from that of a standard player
                idle_limit = 3 * 60 * 60 if conn.player.isSysOp else 30 * 60

                # Has the player timed out? If so, we'll kick them but give them a polite notice.
                if conn.idle_time > idle_limit:
                    conn.player.tell("\n")
                    conn.player.tell("You've been idle for quite a while so we've ended your session for now."
                                     "Feel free to log back in at your convenience.")
                    conn.player.tell("\n")
                    self._disconnect(conn)

                conn.write_output()

            # Nope, the connection is fubar so clean it up
            else:

                self._disconnect(conn)

        # Are there any idle monitor topics we need to destroy?
        topicinfo = Topic.pending()
        for topicname in topicinfo:
            if isinstance(topicname, tuple) and topicname[0].startswith("monitor-"):
                events, idle_time, subbers = topicinfo[topicname]
                if events == 0 and not subbers and idle_time > 30:
                    Topic.static_topic(topicname).destroy()


    def __report_deferred_exception(self, deferred):
        print("\n* Exception while executing deferred action {0}:".format(deferred), file=sys.stderr)
        print("".join(Engine.formatTraceback()), file=sys.stderr)
        print("(Please report this problem)", file=sys.stderr)


    #
    # Create a new connection object when a new session begins
    #
    def _connect(self):

        # Create the connection value and provide some some temporary values
        # to represent the player until they sign in.
        connection = PlayerConnection()
        connect_name = "_%d" % id(connection)  # unique temporary name
        new_player = Player.Player(connect_name, "n", "possibly a human", "an http session not yet signed in")
        connection.player = new_player

        # Associate the new HTTP session with the player connection object
        from origin.server.HttpIo import HttpIo
        connection.io = HttpIo(connection)

        # Add the player connection object to the list of players
        self.all_players[new_player.name] = connection

        # Clear the client screen and announce the user to the server console
        connection.clear_screen()
        connection.output("\n")

        self.__print_game_intro(connection)

        # Make sure there's already at least one admin user. If not, we'll assume this session represents the
        # admin making their first sign in attempt.
        all_accounts = self.accounts.all_accounts()

        if not any("True" in str(acc["isSysop"]) for acc in all_accounts.values()):
            Engine.topic_dialogs.send((connection, self._create_sysop(connection)))
            return connection

        # Prompt the user to login
        Engine.topic_dialogs.send((connection, self._login(connection)))

        return connection


    #
    # Deallocate a player connection when he or she signs off or the connection is otherwise terminated
    #
    def _disconnect(self, conn_or_player):

        if type(conn_or_player) is PlayerConnection:

            print("DISCONNECTING PLAYER CONNECTION OBJECT")
            name = conn_or_player.player.name
            conn = conn_or_player

        elif type(conn_or_player) is Player.Player:

            print("DISCONNECTING PLAYER OBJECT")
            name = conn_or_player.name
            conn = self.all_players[name]

        else:

            raise TypeError("connection or player object expected")

        assert self.all_players[name] is conn
        conn.player.tell_others("%s has left." % Lang.capital(conn.player.subjective))
        del self.all_players[name]
        conn.write_output()

        # Wait for a bit to allow the player's screen to display the goodbye message
        # before actually destroying the connection
        self.defer(1, conn.destroy)


    #
    # Create the System Operator (Sysop) account.
    # Generally the first account created. The first person to use the server will be prompted to create this
    # account so either pre-populate the database with a Sysop account or make sure you're the first one loggin in!
    #
    def _create_sysop(self, conn):

        conn.write_output()
        conn.output("Create the initial System Operator (Sysop) account.")
        conn.output("\n")

        while True:

            name = yield "input", ("By what name will you be known to us?", Accounts.accept_name)
            password = yield "input-noecho", ("Please provide us with a secret word or phrase so we can verify your identity when you return.<password>", Accounts.accept_password)
            conn.output("\n")

            email = Accounts.accept_email("root@localhost")
            gender = Lang.validate_gender("f")

            if not (yield "input", ("Do you want to create the System Operator (Sysop) account?", Lang.yesno)):
                continue
            else:
                break

        self.accounts.create(name, password, email, gender[0], self.game.sysop_start, isSysop=True)
        conn.clear_screen()
        conn.output("\n")

        # Now we can proceed with the normal login screen
        Engine.topic_dialogs.send((conn, self._login(conn)))


    #
    # Returns a location object given the location's name.
    # For example, location_name = "regions.convent.cupola" or "convent.cupola" or just "cupola"
    #
    def _find_location(self, location_name):

        location = self.regions

        for name in location_name.split('.'):

            # Maybe we've been given the full object path
            if hasattr(location, name):
                location = getattr(location, name)

        return location


    #
    # Present the supplicant to our system with a sign in screen
    #
    def _login(self, conn):

        conn.output("<esoteric-iconic>𓅓</esoteric-iconic>")  # &#x13153;
        conn.output("\n")
        conn.output("Welcome to ORIGIN")
        conn.output("\n")

        # Loop until we have a new name leading to a new player character or we have a valid name and password
        while True:

            name = yield "input", ("By what name are you known to us?")

            # Is a player with this name already logged in?
            existing_player = self.search_player(name)

            try:

                Accounts.accept_name(name)

            except ValueError as x:

                conn.output("\n")
                conn.output("%s" % x)
                conn.output("\n")

                continue

            account = self.accounts.get(name)

            # If we don't know the name provided we'll ask the player if they'd like to create an account.
            if account is None:

                if not (yield "input", ("That name is not known to us. Do you wish to be known by this name?", Lang.yesno)):
                    conn.output("\n")
                    continue

                gender = yield "input", ("What is the gender of your player character (m)ale or (f)emale?", Lang.validate_gender)
                password = yield "input-noecho", ("Please provide us with a secret word or phrase so we can verify your identity when you return.<password>")
                conn.output("\n")
                email = yield "input", ("Please type in an email address.", Accounts.accept_email)

                try:

                    Accounts.accept_password(password)

                except ValueError as x:

                    conn.output("\n")
                    conn.output("%s" % x)
                    conn.output("\n")

                    continue

                conn.output("\n")
                response = yield "input", ("Are you sure this is the name you would like to be known by?")

                proceed = Lang.yesno(response)

                if not proceed:

                    conn.output("\n")
                    conn.output("Ok, let's start over.")
                    conn.output("\n")
                    continue

                else:

                    account = self.accounts.create(name, password, email, gender[0], self.game.player_start)

            # If we do recognize this account we'll ask for the password
            else:

                password = yield "input-noecho", "What secret do we share?<password>"


            # Try to log in with the credentials provided
            try:

                self.accounts.valid_password(name, password)

            except ValueError as x:

                conn.output("\n")
                conn.output("%s" % x)
                conn.output("\n")
                continue

            else:

                # If the player is already logged in handle that scenario by disallowing the duplicate login
                if existing_player:

                    existing_player.tell("\n")
                    existing_player.tell("Your account is attempting to log in from elsewhere. Terminating that session.")
                    existing_player.tell("\n")

                    conn.output("\n")
                    conn.output("You are already logged in elsewhere. This session is terminating.")
                    conn.output("\n")

                    Engine.topic_dialogs.send((conn, self._login(conn)))  # Try again

                    return

                # get the account and log in
                account = self.accounts.get(name)
                self.accounts.logged_in(name)

                break

        # A new login requires renaming the transitional PlayerObject instance created by _connect
        # to the corrent account name and restoring player state including their last recorded location.
        if not existing_player:

            name_info = PlayerNaming()
            name_info.name = account["name"]
            name_info.gender = account["gender"]
            self.__rename_player(conn.player, name_info)

            conn.player.isSysOp = account["isSysop"]
            conn.output("\n")

            # Return player to their last known location
            location = account["location"]

            try:
                target = self._find_location(location)
            except:
                print("Failed to find location specified...defaulting to start location.")
                if conn.player.isSysOp:
                    target = self.config.sysop_start
                else:
                    target = self.config.player_start

            conn.player.move(target)

        # Display the welcome message and allow the game to initialize player state if necessary
        self.game.greet(conn.player)
        self.game.init_player(conn.player)

        conn.clear_screen()
        conn.output("\n")

        # show room description
        conn.player.look(short=False)


    #
    # Perform a graceful stop of the main loop by first flushing output to the players
    #
    def _stop(self):

        self.__stop_mainloop = True

        for conn in self.all_players.values():
            conn.write_output()
            conn.destroy()

        self.all_players.clear()
        time.sleep(0.1)


    #
    # Similar to _process_player_input. Continues a interaction with a player.
    #
    def __continue_dialog(self, conn, dialog, message):

        try:

            why, what = dialog.send(message)

        # Send any pending messages to the user if a dialog session is complete
        except StopIteration:

            if conn.player:
                conn.write_output()

        # Player's action was refused
        except ActionRefused as x:

            conn.player.remember_parsed()
            conn.player.tell(str(x))
            conn.write_output()

        # We didn't understand the player's input
        except ParseError as x:
            conn.player.tell(str(x))
            conn.write_output()

        # Everything looks OK
        else:

            if why in ("input", "input-noecho"):

                if type(what) is tuple:
                    prompt, validator = what
                else:
                    prompt, validator = what, None

                if prompt:

                    # Always pad the end of the prompt
                    if not prompt.endswith(" "):
                        prompt += " "

                    # Write pending output
                    conn.write_output()

                    # Send along a new input prompt
                    conn.output_no_newline(prompt)

                assert conn not in self.waiting_for_input, "Only one async dialog can run at a time."

                # Don't echo input if so indicated
                conn.io.dont_echo_next = why == "input-noecho"
                self.waiting_for_input[conn] = (dialog, validator, why != "input-noecho")

            else:

                raise ValueError("Invalid generator: " + why)


    #
    # Just tell the server console what's going down
    #
    def __print_game_intro(self, player_connection):
        if not player_connection:
            print("%s, v%s started on %s" % (self.config.game, self.config.version, time.ctime()))


    #
    # Handles renaming temp (pre-signin) objects once a user is authenticated
    #
    def __rename_player(self, player, name_info):

        conn = self.all_players[player.name]
        del self.all_players[player.name]

        old_monitor = player.get_monitor()
        old_monitor.destroy()

        self.all_players[name_info.name] = conn
        name_info.apply_to(player)


    #
    # Handle normal player actions
    #
    def _process_player_input(self, conn):

        p = conn.player

        assert p.input_is_available.is_set()

        for action in p.get_pending_input():

            if not action:
                continue

            # Process the action
            try:

                # p.tell("\n")
                self.__process_player_action(action, conn)
                p.remember_parsed()

                # stop the loop after processing one action
                break

            # If that didn't work we need to give the player some insight as to what went wrong.
            except UnknownVerbException as x:

                # If the verb is a direction just let them know they can't go that way
                if x.verb in {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest",
                              "north east", "north west", "south east", "south west", "up", "down"}:

                    p.tell("You can't go in that direction.")

                # Otherwise let them know we don't support the verb they tried to use and remind them
                # to always format input as lowercase
                else:

                    p.tell("The verb '%s' is unrecognized." % x.verb)
                    if x.verb[0].isupper():
                        p.tell("Just type in lowercase ('%s')." % x.verb.lower())

            # If the action w
            except ActionRefused as x:

                p.remember_parsed()
                p.tell(str(x))

            except ParseError as x:
                p.tell(str(x))


    #
    # Process player actions. All actions are first submitted to the general parser
    # even if they're to be handled as custom actions since the parser will break down the sentence structure for
    # us.
    #
    def __process_player_action(self, action, conn):

        if not action:
            return

        player = conn.player

        action_verbs = Actions.get(player.isSysOp)
        custom_verbs = set(self.current_custom_verbs(player))

        # Try to parse the action.
        # If there is no error it's an unreconized verb. This should be handled differently I think
        # but for legacy reasons we'll stick with this somewhat non-intuitive approach for now...
        # TODO: Better integrate the LPC derived parser
        try:

            all_verbs = set(action_verbs) | custom_verbs
            parsed = player.parse(action, external_verbs=all_verbs)
            player.turns += 1

            raise ParseError("I don't understand what you're asking me to do. Try to rephrase your request.")

        # We seemed to understand enough to move forward but it wasn't a default verb the LPC derived parser
        # understands (very limited at this point thanks to a lot of refactoring) so we'll try to interpret
        # it as a custom action.
        except NotDefaultVerb as x:

            parsed = x.parsed
            player.turns += 1

            # If it's not a normal verb, abort with "please be more specific".
            try:

                parse_error = "I don't understand what you're asking me to do. Try to rephrase your request."
                handled = False

                # Are we dealing with a custom action?
                if parsed.verb in custom_verbs:

                    # We can't deal with yields directly so we use errors.AsyncDialog
                    # in process_action to do that for us.
                    handled = player.location.process_action(parsed, player)

                    if handled:
                        Engine.topic_actions.send(lambda actor=player: actor.location.notify_action(parsed, actor))
                    else:
                        parse_error = "I don't understand. Please be more specific."

                # If it's not a custom action is it a standard action?
                if not handled:

                    # If the verb matches the name of an exit then we'll assume the player wants to use the exit
                    if parsed.verb in player.location.exits:
                        self._go_through_exit(player, parsed.verb)

                    # If the verb is action (or sysop) annotated we'll process it
                    elif parsed.verb in action_verbs:

                        func = action_verbs[parsed.verb]
                        ctx = Context(self, self.game_clock, self.config, conn)

                        # If we're dealing with a generator function we'll queue the dialog for async processing
                        if getattr(func, "is_generator", False):

                            dialog = func(player, parsed, ctx)
                            Engine.topic_dialogs.send((conn, dialog))

                        # Execute the action
                        else:
                            func(player, parsed, ctx)

                        # If we're annotated to enable notify we'll queue the notification
                        if func.enable_notify_action:
                            print(player, "action notify for", parsed.verb)
                            Engine.topic_actions.send(lambda actor=player: actor.location.notify_action(parsed, actor))

                    else:
                        raise ParseError(parse_error)

            except RetryVerb:

                raise ParseError("I don't understand what you're asking me to do.")

            # Let's try to parse again with the modified action
            except RetryParse as x:

                return self.__process_player_action(x.action, conn)

            # The action completed but is letting us know we need to show an async dialog
            except AsyncDialog as x:

                Engine.topic_dialogs.send((conn, x.dialog))


    #
    # Convenience function for sending a player through an exit
    #
    def _go_through_exit(self, player, direction):

        xt = player.location.exits[direction]
        xt.allow_passage(player)
        player.move(xt.target)
        player.look()


    #
    # Provides a dict containing all custom verbs and their help messages
    #
    def current_custom_verbs(self, player):

        verbs = player.verbs.copy()
        verbs.update(player.location.verbs)

        for creature in player.location.creatures:
            verbs.update(creature.verbs)

        for item in player.inventory:
            verbs.update(item.verbs)

        for item in player.location.items:
            verbs.update(item.verbs)

        for exit in set(player.location.exits.values()):
            verbs.update(exit.verbs)

        return verbs

    #
    # Provides a dict containing all recognized verbs and their help messages
    #
    def current_verbs(self, player):

        normal_verbs = Actions.get(player.isSysOp)
        verbs = {v: (f.__doc__ or "") for v, f in normal_verbs.items()}
        verbs.update(self.current_custom_verbs(player))

        return verbs


    #
    # Print the Message of the Day (motd)
    #
    def show_motd(self, player, notify_no_motd=False):

        try:

            message = "Exploration A scheduled for December 20th, 2016 UDT"

        except IOError:

            message = None

        if message:

            player.tell("Message-Of-The-Day")
            player.tell("")
            player.tell(message)
            player.tell("")
            player.tell("")

        elif notify_no_motd:

            player.tell("There's currently no message-of-the-day.")
            player.tell("")


    #
    # Return the connection associated with a particular player by name
    #
    def search_player(self, name):

        conn = self.all_players.get(name)

        return conn.player if conn else None


    def register_heartbeat(self, gameobj):

        self.heartbeats.add(gameobj)


    def unregister_heartbeat(self, gameobj):

        self.heartbeats.discard(gameobj)


    def register_exit(self, exit):
        if not exit.bound:
            self.unbound_exits.append(exit)


    #
    # Registers a deferred callable action with optional arguments.
    #
    # All vargs and kwargs must be serializable.
    #
    # Due time is a datetime.datetime value and should be experssed in game-time (not real-time)
    # and determines when the defered should execute. Alternatively, it can be a simple integer
    # representing the number of seconds in the future the deferred should execute.
    #
    # Optionally, deferreds get the kwarg 'ctx' representing the Context object if it is represented in the
    # parameter signature.
    #
    # Receiving the context is useful if you need to register another deferred.
    #
    def defer(self, due, action, *vargs, **kwargs):

        assert callable(action)

        if isinstance(due, datetime.datetime):
            assert due >= self.game_clock.clock
        else:
            due = float(due)
            assert due >= 0.0
            due = self.game_clock.plus_realtime(datetime.timedelta(seconds=due))

        deferred = Deferred(due, action, vargs, kwargs)

        with self.deferreds_lock:
            heapq.heappush(self.deferreds, deferred)


    def event(self, topicname, event):

        if topicname == "actions":

            assert callable(event), "Action events must be 'callables'"
            event()

        elif topicname == "tells":

            assert callable(event), "Tell events should be 'callables'"
            event()

        elif topicname == "dialogs":

            assert type(event) is tuple
            conn, dialog = event
            assert type(conn) is PlayerConnection
            assert inspect.isgenerator(dialog)
            self.__continue_dialog(conn, dialog, None)

        else:

            raise ValueError("An unknown topic was provided: " + topicname)


    def remove_deferreds(self, owner):
        with self.deferreds_lock:
            self.deferreds = [d for d in self.deferreds if d.owner is not owner]
            heapq.heapify(self.deferreds)


    #
    # Provides up-time as an immutable list : (hours, mins, secs)
    # Used by "Server" Sysop action
    #
    @property
    def uptime(self):

        realtime = datetime.datetime.now()
        realtime = realtime.replace(microsecond=0)
        uptime = realtime - self.server_started
        hours, seconds = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(seconds, 60)
        return hours, minutes, seconds


    #
    # Provides an exception traceback even if exception information is not provided by calling sys.exc_info()
    #
    @staticmethod
    def formatTraceback(ex_type=None, ex_value=None, ex_tb=None):

        if ex_type is None and ex_tb is None:
            ex_type, ex_value, ex_tb = sys.exc_info()

        result = traceback.format_exception(ex_type, ex_value, ex_tb)

        return result
