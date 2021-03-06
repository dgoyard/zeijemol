##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CW import
from logilab.common.registry import yes
from cubicweb.predicates import anonymous_user
from cubicweb.predicates import match_user_groups
from cubicweb.predicates import authenticated_user
from cubicweb.web import component
from cubicweb.web.views.boxes import SearchBox
from cubicweb.web.views.bookmark import BookmarksBox
from cubicweb.web.views.basecomponents import HeaderComponent
from cubicweb.web.views.basecomponents import AnonUserStatusLink
from cubicweb.web.views.basecomponents import AuthenticatedUserStatus
from logilab.common.decorators import monkeypatch
from cubicweb.web.views.basecontrollers import LogoutController


class CWWaveBox(component.CtxComponent):
    """ Class that generate a left box on the web browser to access all the
    score waves.

    It will appear on the left and contain the wave names.
    """
    __regid__ = "browse-waves"
    __select__ = (component.CtxComponent.__select__ & ~anonymous_user())
    title = u"Waves"
    context = "left"
    order = 0

    def render_body(self, w, **kwargs):
        """ Method that creates the wave navigation box.

        This method displays also the user status for each wave.
        """
        # Sort waves by categories
        rset = self._cw.execute(
            "Any W, C Where W is Wave, W category C")
        struct = {}
        for index, (_, category) in enumerate(rset):
            struct.setdefault(category, []).append(rset.get_entity(index, 0))

        # Display a wave selection component
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        for category, waves in struct.items():

            # Find unfinished waves
            wave_to_display = []
            for wave_entity in waves:
                wave_name = wave_entity.name
                wave_rset = self._cw.execute(
                    "Any S Where W is Wave, W name '{0}', W snapsets S, "
                    "S scores SC, SC scored_by U, U login '{1}'".format(
                        wave_name, self._cw.session.login))
                snapsets_rset = self._cw.execute(
                    "Any COUNT(S) Where W is Wave, W name '{0}', "
                    "W snapsets S".format(wave_name))
                display_wave_button = True
                if len(wave_rset) != snapsets_rset[0][0]:
                    wave_to_display.append(wave_entity)

            # Display category only if one wave is not finished in this
            # category
            if len(wave_to_display) > 0:
                w(u'<div id="category-component">')
                w(u'<b>Category:</b> {0}'.format(category))

                # Create two buttons, one for the wave selection and one
                # for the wave documentation
                for wave_entity in wave_to_display:
                    # > buttons
                    wave_name = wave_entity.name
                    href = self._cw.build_url(
                        "view", vid="gallery-view", wave=wave_name,
                        title=self._cw._("Please rate this item..."))
                    w(u'<div id="wave">')
                    w(u'<div id="wave-rate">')
                    w(u'<a class="btn fullbtn btn-default" href="{0}">'.format(
                        href))
                    w(u'{0}</a>'.format(wave_name))
                    w(u'</div>')
                    w(u'<div id="wave-help">')
                    dochref = self._cw.build_url(
                        "view", vid="zeijemol-documentation",
                        wave_eid=wave_entity.eid)
                    w(u'<a class="btn fullbtn btn-warning" href="{0}">'.format(
                        dochref))
                    w(u'help</a>')
                    w(u'</div>')
                    w(u'</div>')

                # End category
                w(u'</div>')

        # End wave selection
        w(u'</div>')
        w(u'</div>')


class StatusButton(HeaderComponent):
    """ Build a status button displayed in the header.
    """
    __regid__ = "status-snapview"
    __select__ = authenticated_user()
    context = u"header-right"

    def render(self, w):
        w(u"<a href='{0}' class='button icon-status'>status</a>".format(
            self._cw.build_url("view", vid="status-view")))


class RatingsButton(HeaderComponent):
    """ Build a ratings button displayed in the header.

    Only the managers have accessed to this functionality.
    """
    __regid__ = "ratings-snapview"
    __select__ = authenticated_user() & match_user_groups("managers")
    context = u"header-right"

    def render(self, w):
        rset = self._cw.execute(
            "Any X Where X is CWUser, X login '{0}', "
            "X in_group G, G name 'managers'".format(self._cw.session.login))
        if rset.rowcount > 0:
            w(u"<a href='{0}' class='button icon-status'>ratings</a>".format(
                self._cw.build_url("view", vid="ratings-view")))


class LogOutButton(AuthenticatedUserStatus):
    """ Close the current session.
    """
    __select__ = authenticated_user()

    def render(self, w):
        self._cw.add_css("cubicweb.pictograms.css")
        w(u"<a href='{0}' class='button icon-user'>{1}</a>".format(
            self._cw.build_url("logout"), self._cw.session.login))


@monkeypatch(LogoutController)
def goto_url(self):
    """ In http auth mode, url will be ignored
    In cookie mode redirecting to the index view is enough : either
    anonymous connection is allowed and the page will be displayed or
    we'll be redirected to the login form.
    """
    msg = self._cw._('you have been logged out')
    return self._cw.base_url()



def registration_callback(vreg):
    vreg.register(RatingsButton)
    vreg.register(CWWaveBox)
    vreg.register(StatusButton)
    vreg.register(LogOutButton)
    vreg.unregister(BookmarksBox)
    vreg.unregister(SearchBox)
    vreg.unregister(AnonUserStatusLink)
    vreg.unregister(AuthenticatedUserStatus)
