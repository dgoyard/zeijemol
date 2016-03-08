##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import base64
import json

# CW import
from cubicweb.view import View
from cubicweb.web.views.ajaxcontroller import ajaxfunc
from PIL import Image


class SlicesViewer(View):
    """ Custom view to score subjectmeasure files.
    """
    __regid__ = "slices-viewer"
    templatable = False

    def call(self, volumes_slices):

        self._cw.add_js("slices_viewer.js")
        self._cw.add_js("jquery-simple-slider/js/simple-slider.min.js")

        self._cw.add_css("jquery-simple-slider/css/simple-slider-volume.css")

        html = "<div class='hero'>"
        html += "<div class='row' style='width: 100%;'>"
        slices_nbs = set([len(item) for item in volumes_slices.values()])
        assert len(slices_nbs) == 1, "Expected the same number of slices for each snap!"
        slices_nb = slices_nbs.pop()
        heights = []
        widths = []
        for volume_name, slices in volumes_slices.iteritems():
            with Image.open(slices[0]) as im:
                width, height = im.size
                heights.append(height)
                widths.append(width)
            volume_id = "_".join(volume_name.split())
            html += "<div id='{0}' class='col-md-4 slicer'>".format(volume_name)
            html += "<h4>{0}</h4>".format(volume_name)
            html += "<h5>Brightness</h5>"
            html += ("<input class='brightness-bar' type='text' data-slider='true' "
                     "data-slider-range='0,200' value='100' "
                     "data-slider-step='1' data-slider-highlight='true' data-slider-theme='volume'>")
            html += "<h5>Browse volume</h5>"
            html += ("<input class= 'slice-bar' type='text' data-slider='true' "
                     "data-slider-range='0,{0}' value='1' data-slider-step='1' "
                     "data-slider-highlight='true' data-slider-theme='volume'>".format(slices_nb-1, volume_id))
            html += ("<div class='ui-corner-all slider-content' "
                     "id='sliderContent_{0}'>".format(volume_id))
            
            html += "<div class='viewer ui-corner-all'>"
            html += ("<div id='slices_{0}' class='content-conveyor "
                     "ui-helper-clearfix'>".format(volume_id))
            for filepath in slices:
                with open(filepath, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read())
                html += ("<div class='item zoom'><img class='img-responsive' "
                         "src='data:image/png;base64,{0}' /></div>".format(encoded_image))
            html += "</div>"
            html += "</div>"
            html += "</div>"
            html += "</div>"
        html += "</div>"
        html += "</div>"
        
        html += "<style>"
        html += """[class^=slider] { display: inline-block; margin-bottom: 30px; }
    .output { color: #888; font-size: 14px; padding-top: 1px; margin-left: 5px; vertical-align: top;}
    .slider-volume {
        width: 100px;
    }
    .slider {
        width: 100px;
    }/*
    .zoom img {
        width:200px;
        height:200px;
    }*/
    .rotate90 {
        transform: rotate(90deg) translateY(-100%%);
        -webkit-transform: rotate(90deg) translateY(-100%%);
        -ms-transform: rotate(90deg) translateY(-100%%);
    }
    .rotate180 {
        transform: rotate(180deg) translate(-100%%, -100%%);
        -webkit-transform: rotate(180deg) translate(-100%%, -100%%);
        -ms-transform: rotate(180deg) translateX(-100%%, -100%%);
    }
    .rotate270 {
        transform: rotate(270deg) translateX(-100%%);
        -webkit-transform: rotate(270deg) translateX(-100%%);
        -ms-transform: rotate(270deg) translateX(-100%%);
    }"""
        for volume_name, _ in volumes_slices.iteritems():
            volume_id = "_".join(volume_name.split())
            html += """#sliderContent_%(volume_id)s .item {
            display: none;
            position: absolute;
        }
        #slices_%(volume_id)s img {
            transform-origin: top left;
            /* IE 10+, Firefox, etc. */
            -webkit-transform-origin: top left;
            /* Chrome */
            -ms-transform-origin: top left;
            /* IE 9 */
        }
        """ % {"volume_id": volume_id}
        html += "</style>"

        html += "<script>"
        html += "$(document).ready(function() {"
        html += "var slices_nb = {0};".format(slices_nb)
        # html += "var toto =$('.img-responsive').first().height();"
        # html += "console.log(toto);"
        html += "$('#fold-viewer').css('height', {0});".format(round(1.5*max(heights)))
        html += "init_slices_viewer(document, slices_nb);"
        html += "$('.hero').css('width', {0});".format(3*max(widths))
        html += "$('#gallery-img').css('width', {0});".format(3*max(widths))
        html += "});"
        html += "</script>"


        self.w(unicode(html))


# @ajaxfunc(output_type="json")
# def get_b64_images(self):
#
#     form = self._cw.form
#     snap_identifier = form["snap_identifier"]
#
#     rql_files = ("Any F Where S is Snap, S identifier '{0}', "
#                  "S filepaths F".format(snap_identifier))
#     rset_files = self._cw.execute(rql_files)
#     print rset_files
#     files = json.loads(rset_files[0][0].getvalue())
#     print files
#
#     output = []
#     for filepath in sorted(files):
#         print filepath
#         with open(filepath, "rb") as image_file:
#             encoded_string = base64.b64encode(image_file.read())
#         output.append(encoded_string)
#
#     return output

