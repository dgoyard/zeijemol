##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import division
import collections

# Cubicweb import
from cubicweb.web.views.startup import IndexView
from cubicweb.web.httpcache import NoHTTPCacheManager
from cubicweb.view import View


class SnapIndexView(IndexView):
    """ Class that defines the piws index view.
    """
    http_cache_manager = NoHTTPCacheManager

    def call(self, **kwargs):
        """ Create the 'index' like page of our site that contain a rating
        summary for the current user.
        """
        # Create a pie chart summarizing the global rate status:
        # only the managers have accessed to this functionality
        rset = self._cw.execute(
            "Any X Where X is CWUser, X login '{0}', "
            "X in_group G, G name 'managers'".format(self._cw.session.login))
        if rset.rowcount > 0:
            # Display a title
            self.w(u'<h1>Rate global summary...</h1>')

            # For each wave: get the number of scores associated to each snap
            rset = self._cw.execute(
                "Any S, N Where S is SubjectMeasure, S wave W, W name N")
            struct = {}
            for index, row in enumerate(rset):
                wave_name = row[1]
                snap_entity = rset.get_entity(index, 0)
                nb_scores = len(snap_entity.scores)
                struct.setdefault(wave_name, []).append(nb_scores)

            # Build an histogram like structure with the number of rates
            # as bins
            container_id = 0
            nb_columns = 3
            self.w(u'<table class="table table-bordered">')
            self.w(u'<tbody>')
            for wave_name, scores in struct.items():
                data = {}
                nb_elements = sum(scores)
                if nb_elements == 0:
                    data["0"] = 100
                else:
                    counter = collections.Counter(scores)
                    for nb_scores, frequency in counter.items():
                        title = "{0}".format(nb_scores)
                        data[title] = frequency / nb_elements * 100

                # Call PieChart for html generation of the summary
                print container_id, nb_columns, container_id % nb_columns
                if container_id % nb_columns == 0:
                    self.w(u'<tr>')
                self.w(u'<td class="col-md-3">')
                self.wview("pie-highcharts", None, "null", data=data,
                           title="Number of rates: {0}".format(wave_name),
                           container_id=container_id)
                self.w(u'</td>')
                if container_id % nb_columns == nb_columns - 1:
                    self.w(u'</tr>')
                container_id += 1

            # Close properly the table
            if (container_id - 1) % nb_columns != nb_columns - 1:
                self.w(u'</tr>')
            self.w(u'</tr>')
            self.w(u'</tbody>')
            self.w(u'</table>')

        # Build summary in memory ordered by category and wave name
        rset = self._cw.execute(
            "Any S, W, N, C Where S is SubjectMeasure, S wave W, W name N, W category C")
        struct = {}
        for index, row in enumerate(rset):
            wave_name = row[2]
            category = row[3]
            struct.setdefault(category, {}).setdefault(wave_name, []).append(
                rset.get_entity(index, 0))

        # Display the summary table: one progress bar for each wave
        self.w(u'<h1>Progress...</h1>')
        self.w(u'<table class="table">')
        for category, wave_struct in struct.items():
            self.w(u'<thead>')
            self.w(u'<tr>')
            self.w(u'<th>')
            self.w(u'<h2>Category: {0}</h2>'.format(category))
            self.w(u'</th>')
            self.w(u'<tr>')
            self.w(u'</thead>')
            self.w(u'<tbody>')

            # Go through all waves
            for wave_name, snaps in wave_struct.items():

                # Compute the progress score for the logged user
                nb_of_snaps = len(snaps)
                nb_rates = 0
                for entity in snaps:
                    scores = [
                        e for e in entity.scores
                        if e.scored_by[0].login == self._cw.session.login]
                    if len(scores) == 1:
                        nb_rates += 1
                    if len(scores) > 1:
                        raise Exception(
                            "We expect one score per user for one snap.")
                progress = int(nb_rates / nb_of_snaps * 100)

                self.w(u'<tr>')
                self.w(u'<td>')
                self.w(u'<h2>&#9820;{0}</h2>'.format(wave_name))
                self.w(u'</td>')
                self.w(u'<tr>')
                self.w(u'<tr class="danger">')
                self.w(u'<td>')
                self.w(u'<div class="progress">')
                self.w(u'<div class="progress-bar" role="progressbar" '
                       'aria-valuenow="{0}" aria-valuemin="0" aria-valuemax='
                       '"100" style="width:{0}%">'.format(progress))
                self.w(u'{0}%'.format(progress))
                self.w(u'</div>')
                self.w(u"</div>")
                self.w(u'</td>')
                self.w(u'</tr>')
            self.w(u'</tbody>')
        self.w(u'</table>')


class PieChart(View):
    """ Create a pie chart representing the user rates with HighCharts.
    """
    __regid__ = "pie-highcharts"
    paginable = False
    div_id = "pie-highcharts"

    def call(self, data, title, container_id=0,
             highcharts_js="https://code.highcharts.com/highcharts.js",
             exporting_js="https://code.highcharts.com/modules/exporting.js"):
        """ Method that will create a pie chart from the user rates.

        Parameters
        ----------
        data: dict
            a dictionnary with title as keys and occurence (in percent) as
            values.
        title: str
            a title for the chart.
        container_id: int
            an identifier for the chart container.
        """
        # Add js resources
        self._cw.add_js(highcharts_js, localfile=False)
        self._cw.add_js(exporting_js, localfile=False)

        # Create the highcharts string representation of the data
        sdata = '['
        for key, value in data.items():
            sdata += '["{0}", {1}], '.format(key, value)
        sdata += ']'

        # Generate the script
        # > headers
        self.w(u'<script type="text/javascript">')
        self.w(u'$(function () {{ $("#hc_container_{0}").highcharts({{'.format(
            container_id))
        # > configure credit
        self.w(u'credits : {enabled : false}, ')
        # > configure chart
        self.w(u'chart: {plotBackgroundColor: null, plotBorderWidth: 1, '
               'plotShadow: false}, ')
        # > configure title
        self.w(u'title: {{text: "{0}"}}, '.format(title))
        # > configure tooltip
        self.w(u'tooltip: {pointFormat: "{series.name}: '
               '<b>{point.percentage:.1f}%</b>" }, ')
        # > configure plot
        self.w(u'plotOptions: {')
        self.w(u'pie: {allowPointSelect: true, cursor: "pointer", '
               'dataLabels: { enabled: true, format: "<b>{point.name}</b>: '
               '{point.percentage:.1f} %", style: {color: (Highcharts.theme '
               '&& Highcharts.theme.contrastTextColor) || "black"}}}')
        self.w(u'}, ')
        # > configure series
        self.w(u'series: [{{type: "pie", name: "Rate", '
               'data: {0}}}] '.format(sdata))
        # > close headers
        self.w(u'}); ')
        self.w(u'}); ')
        self.w(u'</script>')

        # Add a container in the body to display the pie chart
        self.w(u'<div id="hc_container_{0}" class="hc_container">'
               '</div>'.format(container_id))


def registration_callback(vreg):
    vreg.register_and_replace(SnapIndexView, IndexView)
    vreg.register(PieChart)
