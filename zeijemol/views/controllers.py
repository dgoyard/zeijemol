##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import hashlib
import json

# Cubicweb import
from cubicweb.web import Redirect
from cubicweb.web.controller import Controller


class RateController(Controller):
    """ Create a score entity from input form data.
    """
    __regid__ = "rate-controller"

    def publish(self, rset=None):
        """ Deal with the form.
        """
        # Give me another subject_measure
        if self._cw.form["rate"] != "Rate later":

            # Get the extra answers if specified
            if "extra_answers" in self._cw.form:
                extra_answers = self._cw.form["extra_answers"]
            else:
                extra_answers = []

            # Store my rate
            login = unicode(self._cw.session.login)
            identifier = login + self._cw.form["eid"]
            m = hashlib.md5()
            m.update(identifier)
            identifier = unicode(m.hexdigest())

            # Get the eid of the current user
            user_eid = self._cw.execute(
                "Any X Where X is CWUser, X login "
                "'{0}'".format(login))[0][0]

            # Save the score
            score_eid = self._cw.create_entity(
                "Score",
                identifier=identifier,
                uid=login,
                score=unicode(self._cw.form["rate"]),
                extra_scores=unicode(json.dumps(extra_answers)),
                subject_measure=unicode(self._cw.form["eid"]),
                scored_by=unicode(user_eid)).eid
            self._cw.execute("SET S scores R  WHERE S eid '{0}', R eid "
                             "'{1}'".format(self._cw.form["eid"], score_eid))
                             
        href = self._cw.build_url(
                    "view", vid="gallery-view", wave=self._cw.form["wave_name"],
                    title=self._cw._("Please rate this item..."))
        raise Redirect(href)
