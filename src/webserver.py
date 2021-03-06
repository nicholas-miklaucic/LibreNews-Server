import datetime
import httplib
import json

import tornado
import tornado.ioloop
import tornado.web

import arrow
import configuration
import flashes
import stats
from userio import error, ok, say


"""
You probably don't need to touch this file. Instead, hack away on the
templates and on `flashes.py`. But keep your hands away from this file
unless you're absolutely sure!
"""


def get_ip(request):
    x_real_ip = request.headers.get("X-Real-IP")
    remote_ip = x_real_ip or request.remote_ip
    return remote_ip


class IndexHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.render("pages/error.html", message=httplib.responses[status_code], error=status_code)

    def get(self):
        try:
            req_resp = stats.request(str(get_ip(self.request)))
        except:
            error("Errored while handling request IP -- still served...")
        say("Received INDEX request (" + req_resp + ")")
        flash = flashes.get_latest_flashes(1)[0]
        flash['text'] = tornado.escape.xhtml_unescape(flash['text'])
        time = str(flash['time'])

        if isinstance(flash['time'], basestring):
            time = arrow.Arrow.strptime(flash['time'], "%a %b %d %H:%M:%S +0000 %Y").humanize()
        elif isinstance(flash['time'], datetime.datetime):
            time = arrow.get(flash['time']).humanize()
        self.render("pages/index.html", flash=flash, time=time)


class StatsHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.render("pages/error.html", message=httplib.responses[status_code], error=status_code)

    def get(self):
        try:
            req_resp = stats.request(str(get_ip(self.request)))
            say("Received STATS request (" + req_resp + ")")
        except:
            error("Errored while handling request IP -- still served...")
        self.render("pages/stats.html", countries=stats.top_countries(), last_restart=stats.time(),
                    devices=stats.unique_devices(), total_requests=stats.requests,
                    requests_per_second=stats.requests_per_second())


class ApiHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.render("pages/error.html", message=httplib.responses[status_code], error=status_code)

    def get(self):
        try:
            req_resp = stats.request(str(get_ip(self.request)))
            say("Received API request (" + req_resp + ")")
        except:
            error("Errored while handling request IP -- still served...")
        self.set_header("Content-Type", "application/json")
        latest = -1
        try:
            latest = int(self.get_argument('latest'))
        except:
            pass  # no latest flash specified
        data = {
            "server": "LibreNews Central",
            "channels": [k[2] for k in configuration.get_accounts()],
            "latest": [flash for flash in flashes.get_latest_flashes(25)
                       if int(flash['id']) > int(latest)]
        }
        self.write(unicode(json.dumps(data, sort_keys=True, separators=(',', ':'))))


class ErrorHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        try:
            stats.request(str(get_ip(self.request)))
        except:
            error("Errored while handling request IP -- still served...")
        self.render("pages/error.html", message=httplib.responses[status_code], error=status_code)

    def get(self):
        try:
            stats.request(str(get_ip(self.request)))
        except:
            error("Errored while handling request IP -- still served...")
        self.render("pages/error.html", message="Page not found", error="404")


application = tornado.web.Application([
    (r"/", IndexHandler),
    (r"/api", ApiHandler),
    (r"/stats", StatsHandler),
    (r'/static/(.*)$', tornado.web.StaticFileHandler, {'path': "pages/static"})
    ], default_handler_class=ErrorHandler)
if __name__ == "__main__":
    flashes.go()
    ok("Starting webserver...")
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
