# coding=utf-8

import datetime
import random
import re
import time
import sqlite3

from hashlib import sha1
from origin import context
from origin.parser.Lang import validate_gender


#
# Account class dealing with login, creation, database access, and other general accounting for players
#
class Accounts(object):


    def __init__(self, database="origin.db"):

        self.sqlite_dbpath = database
        self._create_database()


    def _sqlite_connect(self):
        urimode = self.sqlite_dbpath.startswith("file:")
        conn = sqlite3.connect(self.sqlite_dbpath, detect_types=sqlite3.PARSE_DECLTYPES, timeout=5, uri=urimode)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn


    def _create_database(self):
        try:
            with self._sqlite_connect() as conn:
                table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Account'").fetchone()
                if not table_exists:
                    print("%s: Creating new user accounts database." % context.config.name)
                    print("Location:", self.sqlite_dbpath, "\n")
                    # create the schema
                    conn.execute("""
                        CREATE TABLE Account(
                            id integer PRIMARY KEY,
                            name varchar NOT NULL,
                            email varchar NOT NULL,
                            pw_hash varchar NOT NULL,
                            pw_salt varchar NOT NULL,
                            isSysop varchar NOT NULL,
                            gender varchar NOT NULL,
                            location varchar NOT NULL,
                            created timestamp NOT NULL,
                            logged_in timestamp NULL
                        );""")
                    conn.execute("CREATE INDEX idx_account_name ON Account(name)")
                    conn.commit()
        except sqlite3.Error as x:
            print("%s: Can't open or create the user accounts database." % context.config.name)
            print("Location:", self.sqlite_dbpath)
            print("Error:", repr(x))
            raise SystemExit("Cannot launch mud mode without a user accounts database.")


    def get(self, name):

        with self._sqlite_connect() as conn:

            result = conn.execute("SELECT * FROM Account WHERE name=?", (name,)).fetchone()

            if not result:
                return None

            return {"name"      : result["name"],
                    "email"     : result["email"],
                    "pw_hash"   : result["pw_hash"],
                    "pw_salt"   : result["pw_salt"],
                    "isSysop"   : result["isSysop"],
                    "gender"    : result["gender"],
                    "location"  : result["location"],
                    "created"   : result["created"],
                    "logged_in" : result["logged_in"]}


    def update(self, account):

        with self._sqlite_connect() as conn:
            result = conn.execute("UPDATE Account SET name = ?, email = ?, pw_hash = ?, pw_salt = ?, isSysop = ?, gender = ?, location = ?, created = ?, logged_in = ? WHERE name = ?", (account["name"], account["email"], account["pw_hash"], account["pw_salt"], account["isSysop"], account["gender"], account["location"], account["created"], account["logged_in"], account["name"]))

        return result


    def all_accounts(self, isSysop=False):

        with self._sqlite_connect() as conn:

            if isSysop:
                result = conn.execute("SELECT name FROM Account WHERE isSysop='True'")
            else:
                result = conn.execute("SELECT name FROM Account").fetchall()

            accounts = {}

            for ar in result:
                accounts[ar["name"]] = self.get(ar["name"])

            return accounts


    def logged_in(self, name):
        timestamp = datetime.datetime.now().replace(microsecond=0)
        with self._sqlite_connect() as conn:
            conn.execute("UPDATE Account SET logged_in=? WHERE name=?", (timestamp, name))


    def valid_password(self, name, password):

        with self._sqlite_connect() as conn:
            result = conn.execute("SELECT pw_hash, pw_salt FROM Account WHERE name=?", (name,)).fetchone()

        if result:

            stored_hash, stored_salt = result["pw_hash"], result["pw_salt"]
            pwhash, _ = self._pwhash(password, stored_salt)

            if pwhash == stored_hash:
                return

        raise ValueError("That is not the secret we have on record.")


    def create(self, name, password, email, gender, location, isSysop=False):

        name = name.strip()
        email = email.strip()
        validate_gender(gender)

        self.accept_name(name)
        self.accept_password(password)
        self.accept_email(email)

        if isSysop:
            Sysop = "True"
        else:
            Sysop = "False"

        created = datetime.datetime.now().replace(microsecond=0)
        pwhash, salt = self._pwhash(password)

        with self._sqlite_connect() as conn:

            result = conn.execute("SELECT COUNT(*) FROM Account WHERE name=?", (name,)).fetchone()[0]
            if result > 0:
                raise ValueError("I'm sorry but that name is not available")

            target = location.region + "." + location.varname
            print(name, email, pwhash, salt, gender, target, created)
            result = conn.execute("INSERT INTO Account('name', 'email', 'pw_hash', 'pw_salt', 'isSysop', 'gender', 'location', 'created') VALUES (?,?,?,?,?,?,?,?)", (name, email, pwhash, salt, Sysop, gender, target, created))

        return {"name"      : name,
                "email"     : email,
                "pw_hash"   : pwhash,
                "pw_salt"   : salt,
                "isSysop"   : Sysop,
                "gender"    : gender,
                "location"  : location,
                "created"   : created,
                "logged_in" : created}


    def change_password(self, name, old_password, new_password):

        self.valid_password(name, old_password)
        self.accept_password(new_password)

        with self._sqlite_connect() as conn:

            result = conn.execute("SELECT id FROM Account WHERE name=?", (name,)).fetchone()
            if not result:
                raise KeyError("Unknown name.")

            account_id = result["id"]
            pwhash, salt = self._pwhash(new_password)
            conn.execute("UPDATE Account SET pw_hash=?, pw_salt=? WHERE id=?", (pwhash, salt, account_id))


    @staticmethod
    def _pwhash(password, salt=None):
        if not salt:
            salt = str(random.random() * time.time() + id(password)).replace('.', '')
        pwhash = sha1((salt + password).encode("utf-8")).hexdigest()
        return pwhash, salt


    @staticmethod
    def accept_password(password):
        if len(password) >= 8:
            if re.search("[a-zA-z]", password) and re.search("[0-9]", password):
                return password
        raise ValueError("The secret we share should be at least 8 characters long and contain letters, at least one number, and optionally other characters.")


    @staticmethod
    def accept_name(name):
        if re.match("[a-z]{3,16}$", name):
            if name in Accounts.blocked_names:
                raise ValueError("That name is not available.")
            return name
        raise ValueError("We do not recognize that name. Your name should be all lowercase letters and between 3 and 16 characters long.")


    @staticmethod
    def accept_email(email):
        user, _, domain = email.partition("@")
        if user and domain and user.strip() == user and domain.strip() == domain:
            return email
        raise ValueError("That doesn't appear to be a valid email address.")


    blocked_names = """
me
you
us
them
they
their
theirs
he
him
his
she
her
hers
it
its
yes
no
god
allah
jesus
jezus
hitler
neuk
fuck
cunt
cock
prick
pik
lul
kut
dick
pussy
twat
cum
milf
anal
sex
ass
asshole
neger
nigger
nigga
jew
muslim
moslim
binladen
chink
cancer
kanker
aids
bitch
motherfucker
fucker
""".split()
