# coding=utf-8

from http.cookies import SimpleCookie
from origin.common.errors.SessionClose import SessionClose


#
# Encapsulates session cookie functionality.
#
class Session(object):


    def __init__(self, app, factory):
        self.app = app
        self.factory = factory


    def __call__(self, environ, start_response):

        cookie = SimpleCookie()

        if 'HTTP_COOKIE' in environ:
            cookie.load(environ['HTTP_COOKIE'])

        sid = None

        # Get the session cookie if there is one
        if "session_id" in cookie:
            sid = cookie["session_id"].value

        environ["wsgi.session"] = self.factory.load(sid)

        # If the server runs behind a reverse proxy, you can configure the proxy
        # to pass along the uri that it exposes (our internal uri can be different)
        # via the X-Forwarded-Uri header.
        forwarded_uri = environ.get("HTTP_X_FORWARDED_URI", "/")
        cookie_path = "/" + forwarded_uri.split("/", 2)[1]


        def wrapped_start_response(_status, _response_headers, _exc_info=None):

            # This mess is needed for CORS - Cross Origin Resource Sharing
            # Preflight isn't getting called the way we're using it apparently. Might can get rid of * in Allow-Headers

            # Not to be confused with the game engine! :)
            origin = environ.get("HTTP_ORIGIN")

            if origin:
                _response_headers.extend([
                    ("Access-Control-Allow-Origin", origin),
                    ("Access-Control-Allow-Credentials", "true"),
                    ("Access-Control-Allow-Methods", "GET,POST"),
                    ("Access-Control-Allow-Headers", "Content-Type")
                ])

            _sid = self.factory.save(environ["wsgi.session"])

            _cookies = SimpleCookie()
            _cookies["session_id"] = _sid
            _cookie = _cookies["session_id"]
            _cookie["path"] = cookie_path
            _cookie["httponly"] = 1

            _response_headers.extend(("set-cookie", morsel.OutputString()) for morsel in _cookies.values())

            return start_response(_status, _response_headers, _exc_info)

        try:

            return self.app(environ, wrapped_start_response)

        except SessionClose as x:

            self.factory.delete(sid)

            # clear the browser cookies
            cookies = SimpleCookie()
            cookies["session_id"] = "deleted"
            cookie = cookies["session_id"]
            cookie["path"] = cookie_path
            cookie["httponly"] = 1
            cookie["expires"] = "Thu, 01-Jan-1970 00:00:00 GMT"

            response_headers = [('Content-Type', x.content_type)]
            response_headers.extend(("set-cookie", morsel.OutputString()) for morsel in cookies.values())

            start_response("200 OK", response_headers)

            return [str(x).encode("utf-8")]
