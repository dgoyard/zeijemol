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
from numpy.random import choice
import json
import os

# CW import
from urlparse import parse_qs
from cubicweb.view import View


class Gallery(View):
    """ Custom view to score snapSet files.
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

        # Get the snapset to rate
        self.w(u'<h1>{0}</h1>'.format(title))
        rset = self._cw.execute("Any E Where W is Wave, W name '{0}', "
                                "W extra_answers E".format(wave_name))
        extra_answers = json.loads(rset[0][0])
        rset = self._cw.execute("Any S Where W is Wave, W name '{0}', "
                                "W snapsets S".format(wave_name))
        # find minimum rating
        _min = float("inf")
        for index in range(rset.rowcount):
            snapset_entity = rset.get_entity(index, 0)
            nb_rate = 1
            for escore in snapset_entity.scores:
                nb_rate += 1
            if nb_rate < _min:
                _min = nb_rate

        rset_indices = []
        rset_weights = []
        nb_snapsets_to_rate = 0
        for index in range(rset.rowcount):
            snapset_entity = rset.get_entity(index, 0)
            nb_rate = 1
            already_rated = False
            for escore in snapset_entity.scores:
                nb_rate += 1
                if escore.scored_by[0].login == self._cw.session.login:
                    already_rated = True
                    break
            if not already_rated:
                nb_snapsets_to_rate += 1
                if nb_rate < _min + 2:
                    rset_indices.append(index)
                    rset_weights.append(1. / nb_rate)
        rset_weights_norm = [
            float(x) / sum(rset_weights) for x in rset_weights]

        if len(rset_indices) == 0:
            error = "No more snapSet to rate, thanks."
            self.w(u"<p class='label label-danger'>{0}</p>".format(error))
            return
        nb_of_snapsets = rset.rowcount
        rand_index = choice(rset_indices, p=rset_weights_norm)
        snapset_entity = rset.get_entity(rand_index, 0)

        # Dispaly status
        progress = int((1 - nb_snapsets_to_rate / nb_of_snapsets) * 100)
        self.w(u'<div class="progress">')
        self.w(u'<div class="progress-bar" role="progressbar" '
               'aria-valuenow="{0}" aria-valuemin="0" aria-valuemax='
               '"100" style="width:{0}%">'.format(progress))
        self.w(u'{0}%'.format(progress))
        self.w(u'</div>')
        self.w(u"</div>")

        # Display the image to rate

        # Display/Send a form
        href = self._cw.build_url("rate-controller", eid=snapset_entity.eid)
        self.w(u'<div id="gallery-form">')
        self.w(u'<form action="{0}" method="post">'.format(href))
        self.w(u'<input type="hidden" name="wave_name" value="{0}">'.format(
            wave_name))
        self.w(u'<input class="btn btn-success gallery-btn" type="submit" '
               'name="rate" value="Accept"/>')
        self.w(u'<input class="btn btn-warning gallery-btn" type="submit" '
               'name="rate" value="Prescribe manual edits"/>')
        self.w(u'<input class="btn btn-danger gallery-btn" type="submit" '
               'name="rate" value="Exclude"/>')
        self.w(u'<input class="btn btn-info gallery-btn" type="submit" '
               'name="rate" value="Rate later"/>')

        if len(extra_answers) > 0:
            self.w(u'<h5><u>Exclude due to:</u></h5>')
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

        triplanar_snaps_identifiers = {snap.name: snap.identifier
                                       for snap in snapset_entity.snaps
                                       if snap.dtype == "triplanar"}
        self.w(u"<div id='leftgrid'>")
        if len(triplanar_snaps_identifiers):
            self.w(u'<div id="fold-viewer" class="leftblock">')
            self.wview('triplanar-qc-view', None, 'null',
                       snaps_identifiers=triplanar_snaps_identifiers)
            self.w(u'</div>')

        for snap in snapset_entity.snaps:
            if snap.dtype != "triplanar":

                snap_filepaths = json.loads(snap.filepaths.getvalue())

                if len(snap_filepaths) != 1:
                    error = ("This subject seems to be missing, please contact"
                             " an administrator and refresh the page, thank "
                             "you")
                    self.w(u"<p class='label label-danger'>{0}</p>".format(
                        error))
                    return

                assert len(snap_filepaths) == 1
                filepath = snap_filepaths[0]
                self.w(u'<div id="gallery-img" class="leftblock">')

                if snap.dtype == "CTM":
                    json_stats = self._cw.vreg.config["json_population_stats"]
                    if not os.path.isfile(json_stats):
                        json_stats = os.path.join(self._cw.vreg.config.CUBES_DIR,
                                                  "zeijemol", "data", "qcsurf",
                                                  "population_mean_sd.json")
                    fsdir = os.path.join(os.path.dirname(filepath),
                                         os.pardir)
                    self.wview("mesh-qcsurf", None, "null", fsdir=fsdir,
                               header=[snapset_entity.name],
                               populationpath=json_stats)
                else:
                    with open(filepath, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read())
                    if snap.dtype.lower() == "pdf":
                        self.w(u'<embed class="gallery-pdf" alt="Embedded PDF" '
                               'src="data:application/pdf;base64, {0}" />'.format(
                                   encoded_string))
                    else:
                        self.w(u'<img class="gallery-img" alt="Embedded Image" '
                               'src="data:image/{0};base64, {1}" />'.format(
                                   snap.dtype.lower(), encoded_string))
                self.w(u'</div>')
        self.w(u'</div>')

        self.w(u'<div id="floating-clear"/>')
        self.w(u'</div>')
