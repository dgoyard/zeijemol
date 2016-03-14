##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import division
import base64
import random
import json
import os

# CW import
from cgi import parse_qs
from cubicweb.view import View


class Gallery(View):
    """ Custom view to score snap files.
    """
    __regid__ = "gallery-view"

    def call(self, **kwargs):
        """ Create the rate form.
        """
        # Get some parameters
        path = self._cw.relative_path()
        if "?" in path:
            path, param = path.split("?", 1)
            kwargs.update(parse_qs(param))
        title = kwargs["title"][0]
        wave_name = kwargs["wave"][0]

        # Get the snap to rate
        self.w(u'<h1>{0}</h1>'.format(title))
        rset = self._cw.execute("Any E Where W is Wave, W name '{0}', "
                                "W extra_answers E".format(wave_name))
        extra_answers = json.loads(rset[0][0])
        rset = self._cw.execute("Any S Where W is Wave, W name '{0}', "
                                "W snapsets S".format(wave_name))
        rset_indices = []
        for index in range(rset.rowcount):
            snapset_entity = rset.get_entity(index, 0)
            scores = [
                e for e in snapset_entity.scores
                if e.scored_by[0].login == self._cw.session.login]
            if len(scores) == 0:
                rset_indices.append(index)
        if len(rset_indices) == 0:
            error = "No more snap to rate, thanks."
            self.w(u"<p class='label label-danger'>{0}</p>".format(error))
            return
        nb_of_snapsets = rset.rowcount
        nb_snaps_to_rate = len(rset_indices)
        rand_index = random.randint(0, nb_snaps_to_rate - 1)
        snapset_entity = rset.get_entity(rset_indices[rand_index], 0)

        # Dispaly status
        progress = int((1 - nb_snaps_to_rate / nb_of_snapsets) * 100)
        self.w(u'<div class="progress">')
        self.w(u'<div class="progress-bar" role="progressbar" '
               'aria-valuenow="{0}" aria-valuemin="0" aria-valuemax='
               '"100" style="width:{0}%">'.format(progress))
        self.w(u'{0}%'.format(progress))
        self.w(u'</div>')
        self.w(u"</div>")

        # Display the image to rate
        for snap_entity in snapset_entity.snaps:
            if snap_entity.dtype == "CTM":
                self.w(u'<div id="gallery-img">')
                json_stats = self._cw.vreg.config["json_population_stats"]
                if not os.path.isfile(json_stats):
                    json_stats = os.path.join(self._cw.vreg.config.CUBES_DIR,
                                              "zeijemol", "data", "qcsurf"
                                              "population_mean_sd.json")
                fsdir = os.path.join(os.path.dirname(snap_entity.filepath),
                                     os.pardir)
                self.wview("mesh-qcsurf", None, "null", fsdir=fsdir,
                           header=[snap_entity.code],
                           populationpath=json_stats)
                self.w(u'</div>')
            else:
                with open(snap_entity.filepath, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())
                self.w(u'<div id="gallery-img">')
                if snap_entity.dtype.lower() == "pdf":
                    self.w(u'<embed class="gallery-pdf" alt="Embedded PDF" '
                           'src="data:application/pdf;base64, {0}" />'.format(
                               encoded_string))
                else:
                    self.w(u'<img class="gallery-img" alt="Embedded Image" '
                           'src="data:image/{0};base64, {1}" />'.format(
                               snap_entity.dtype.lower(), encoded_string))
                self.w(u'</div>')

        # Display/Send a form
        href = self._cw.build_url("rate-controller", eid=snap_entity.eid,
                                  filepath=snap_entity.filepath)
        self.w(u'<div id="gallery-form">')
        self.w(u'<form action="{0}" method="post">'.format(href))
        self.w(u'<input class="btn btn-success" type="submit" '
               'name="rate" value="Good"/>')
        self.w(u'<input class="btn btn-danger" type="submit" '
               'name="rate" value="Bad"/>')
        self.w(u'<input class="btn btn-info" type="submit" '
               'name="rate" value="Rate later"/>')
        if len(extra_answers) > 0:
            self.w(u'<u>Optional observations:</u>')
        for extra in extra_answers:
            self.w(u'<div class="checkbox">')
            self.w(u'<label>')
            self.w(u'<input class="checkbox" type="checkbox" '
                   'name="extra_answers" value="{0}"/>'.format(extra))
            self.w(unicode(extra))
            self.w(u'</label>')
            self.w(u'</div>')
        self.w(u'</form>')
        self.w(u'</div>')

        self.w(u'<div id="floating-clear"/>')
