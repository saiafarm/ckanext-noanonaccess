import logging

from pylons import config
from pylons.controllers.util import redirect_to

import ckan.plugins as plugins
import ckan.lib.base as base


logger = logging.getLogger(__name__)


class AuthMiddleware(object):
    def __init__(self, app, app_conf):
        self.app = app
    def __call__(self, environ, start_response):
        # if logged in via browser cookies or API key, all pages accessible
        if 'repoze.who.identity' in environ or self._get_user_for_apikey(environ):
            return self.app(environ,start_response)
        else:
            # otherwise only login/reset are accessible
            if (environ['PATH_INFO'] == '/user/login' or environ['PATH_INFO'] == '/user/_logout'
                                or '/user/reset' in environ['PATH_INFO'] or environ['PATH_INFO'] == '/user/logged_out'
                                or environ['PATH_INFO'] == '/user/logged_in' or environ['PATH_INFO'] == '/user/logged_out_redirect'
                                or environ['PATH_INFO'] == '/user/register'):
                return self.app(environ,start_response)
            else:
                return redirect_to('/user/login')

    def _get_user_for_apikey(self, environ):
        # Adapted from https://github.com/ckan/ckan/blob/625b51cdb0f1697add59c7e3faf723a48c8e04fd/ckan/lib/base.py#L396
        apikey_header_name = config.get(base.APIKEY_HEADER_NAME_KEY,
                                        base.APIKEY_HEADER_NAME_DEFAULT)
        apikey = environ.get(apikey_header_name, '')
        if not apikey:
            # For misunderstanding old documentation (now fixed).
            apikey = environ.get('HTTP_AUTHORIZATION', '')
        if not apikey:
            apikey = environ.get('Authorization', '')
            # Forget HTTP Auth credentials (they have spaces).
            if ' ' in apikey:
                apikey = ''
        if not apikey:
            return None
        apikey = unicode(apikey)
        # check if API key is valid by comparing against keys of registered users
        query = model.Session.query(model.User)
        user = query.filter_by(apikey=apikey).first()
        return user


class NoanonaccessPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IMiddleware, inherit=True)

    def make_middleware(self, app, config):
        return AuthMiddleware(app, config)
