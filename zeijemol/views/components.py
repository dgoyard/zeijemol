#! /usr/bin/env python
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
from cubicweb.web import component
from cubicweb.web.views.boxes import SearchBox
from cubicweb.web.views.bookmark import BookmarksBox
from cubicweb.web.views.basecomponents import HeaderComponent


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
            "Any N, W, C Where W is Wave, W name N, W category C")
        struct = {}
        for index, (name, eid, category) in enumerate(rset):
            struct.setdefault(category, []).append({
                "name": name,
                "description": rset.get_entity(index, 1).description
            })

        # Display a wave selection component
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        index = 0
        for category, waves in struct.items():
            w(u'<div id="category-component">')
            w(u'<b>Category:</b> {0}'.format(category))
            for wave_srtruct in waves:
                wave_name = wave_srtruct["name"]
                wave_description = wave_srtruct["description"]
                wave_rset = self._cw.execute(
                    "Any S Where W is Wave, W name '{0}', W subject_measures S".format(
                        wave_name))
                display_wave_button = False
                for index_wave in range(wave_rset.rowcount):
                    snap_entity = wave_rset.get_entity(index_wave, 0)
                    scores = [
                        e for e in snap_entity.scores
                        if e.scored_by[0].login == self._cw.session.login]
                    if len(scores) == 0:
                        display_wave_button = True
                        break
                wave_rset = [
                    item for index_wave, item in enumerate(wave_rset)
                    if len(wave_rset.get_entity(index_wave, 0).scores) == 0]
                if display_wave_button:
                    # Create two buttons, one for the wave selection and one
                    # for the wave documentation
                    href = self._cw.build_url(
                        "view", vid="gallery-view", wave=wave_name,
                        title=self._cw._("Please rate this item..."))
                    w(u'<div id="wave-rate">')
                    w(u'<a class="btn fullbtn btn-default" href="{0}">'.format(
                        href))
                    w(u'{0}</a>'.format(wave_name))
                    w(u'</div>')
                    w(u'<div id="wave-help">')
                    w(u'<a class="btn fullbtn btn-warning" data-toggle='
                      '"collapse" data-target="#doc-{0}">'.format(index))
                    w(u'help</a>')
                    w(u'</div>')
                    w(u'<div id="floating-clear"/>')

                    # Create a div that will be show or hide when the doc
                    # button is clicked
                    w(u'<div id="doc-{0}" class="collapse">'.format(index))
                    w(u'<a>{0}</a>'.format(wave_description))
                    w(u"</div>")

                    # Increment index
                    index += 1
            w(u'</div>')
        w(u'</div>')
        w(u'</div>')


class StatusButton(HeaderComponent):
    """ Build a status button displayed in the header.
    """
    __regid__ = "status-snapview"
    __select__ = yes()  # no need for a cnx
    context = u"header-right"

    def render(self, w):
        w(u"<a href='{0}' class='button icon-status'>status</a>".format(
            self._cw.build_url("view", vid="status-view")))


class RatingsButton(HeaderComponent):
    """ Build a ratings button displayed in the header.

    Only the managers have accessed to this functionality.
    """
    __regid__ = "ratings-snapview"
    __select__ = yes()  # no need for a cnx
    context = u"header-right"

    def render(self, w):
        rset = self._cw.execute(
            "Any X Where X is CWUser, X login '{0}', "
            "X in_group G, G name 'managers'".format(self._cw.session.login))
        if rset.rowcount > 0:
            w(u"<a href='{0}' class='button icon-status'>ratings</a>".format(
                self._cw.build_url("view", vid="ratings-view")))


def registration_callback(vreg):
    vreg.register(RatingsButton)
    vreg.register(CWWaveBox)
    vreg.register(StatusButton)
    vreg.unregister(BookmarksBox)
    vreg.unregister(SearchBox)
