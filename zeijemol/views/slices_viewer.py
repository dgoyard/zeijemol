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
from PIL import Image

# CW import
from cubicweb.view import View
from cubicweb.web.views.ajaxcontroller import ajaxfunc


class TriplanarQCView(View):
    """ Dynamic volume slices viewer.
    """
    __regid__ = "triplanar-qc-view"

    def call(self, snaps_identifiers, formulas=None):

        if formulas is None:
            # Origin is the top left corner of the image
            formulas = {"sagittal": {"axial": "Math.round(y*nb_slices/im_length)",
                                     "coronal": "Math.round(x*nb_slices/im_length)"},
                        "coronal": {"sagittal": "Math.round(x*nb_slices/im_length)",
                                    "axial": "Math.round(y*nb_slices/im_length)"},
                        "axial": {"sagittal": "Math.round(x*nb_slices/im_length)",
                                  "coronal": "Math.round(nb_slices-y*nb_slices/im_length)"}}

        # Add JS and CSS resources for the slices viewer
        self._cw.add_js("slices_viewer.js")
        self._cw.add_css("slices_viewer.css")
        # Add JS and CSS resources for the slider used by the slices viewer
        self._cw.add_js("jquery-simple-slider/js/simple-slider.min.js")
        self._cw.add_css("jquery-simple-slider/css/simple-slider-volume.css")

        # Add an hidden loading image
        html = "<div id='loading-msg' style='display: none;' align='center'>"
        loading_img_url = self._cw.data_url('images/loadData-lg.gif')
        html += "<img src='{0}'/>".format(loading_img_url)
        html += "</div>"

        # Open the container div (hidden until the images are properly loaded)
        html += "<div id='viewer-container' style='visibility: hidden;'>"

        # Open the viewer div
        html += "<div>"
        # Add a brightness control bar
        html += "<div>"
        html += "<h5 style='color: white;'>Brightness</h5>"
        html += ("<input class='all-brightness-bar' type='text' "
                 "data-slider='true' data-slider-range='0,200' "
                 "value='100' data-slider-step='1' "
                 "data-slider-highlight='true' data-slider-theme='volume'>")
        html += "</div>"

        # Create the 3 viewer columns :  sagittal, coronal, axial
        filepaths = {}
        anat_planes = ["sagittal", "coronal", "axial"]
        nb_slices = None
        image_length = None
        for anat_plane in anat_planes:

            snap_id = snaps_identifiers[anat_plane]
            rql_images = ("Any F Where S is Snap, S identifier '{0}', "
                          "S filepaths F".format(snap_id))
            rset_images = self._cw.execute(rql_images)
            images = json.loads(rset_images[0][0].getvalue())

            if image_length is None:
                with Image.open(images[0]) as im:
                    width, height = im.size
                    assert width == height
                    image_length = width

            filepaths[anat_plane] = images

            if nb_slices is None:
                nb_slices = len(images)
            if len(images) != nb_slices:
                raise Exception("The number of slices per anatomical plane"
                                "must be constant")

            html += "<div id='{0}' class='col-fixed slicer' style='width: {1}px;'>".format(anat_plane, image_length)
            html += "<h4 style='color: white;'>{0}</h4>".format(
                anat_plane.upper())
            html += "<h5 style='color: white;'>Browse volume</h5>"
            html += ("<input class='slice-bar' type='text' data-slider='true' "
                     "data-slider-range='0,{0}' value='{1}' "
                     "data-slider-step='1' data-slider-highlight='true' "
                     "data-slider-theme='volume'>".format(
                         (nb_slices-1), round((nb_slices-1)/2)))
            html += "<div class='ui-corner-all slider-content'>"
            html += "<div class='viewer ui-corner-all'>"
            html += ("<div class='content-conveyor "
                     "ui-helper-clearfix slices-container'>")
            html += "</div>"
            html += "</div>"
            html += "</div>"
            html += "</div>"
        html += "</div>"
        html += "</div>"

        html += "<script>"
        html += "$(document).ready(function() {"
        html += "$('.btn').each(function () {"
        html += "$(this).prop('disabled', true);"
        html += "});"
        html += "$('#loading-msg').show();"
        ajax_url = self._cw.build_url("ajax", fname="get_b64_images")
        html += "$.post('{0}', {1})".format(
            ajax_url, json.dumps({'filepaths': json.dumps(filepaths)}))
        html += ".done(function(data) {"
        html += "$('#loading-msg').hide();"
        html += "var images_data = data['images'];"
        html += "var im_length = {0};".format(image_length)
        html += "var nb_slices = {0};".format(nb_slices)
        html += "for (var key in data) {"
        html += "if (data.hasOwnProperty(key)) {"
        html += "var images = '';"
        html += "for (var j = 0; j < nb_slices; j++) {"
        html += ("images += \"<div class='item'>"
                 "<img class='slice-img' "
                 "height='\"+im_length+\"' width='\"+im_length+\"' "
                 "src='data:image/png;base64,\"+ data[key][j] + \"' />"
                 "</div>\";")
        html += "}"
        html += "$('#'+key).find('.slices-container').each(function () {"
        html += "$(this).html(images);"
        html += "});"

        for anat_plane in anat_planes:
            compute_coords = "var x = e.pageX - $(this).parent().offset().left;"
            compute_coords += "var y = e.pageY - $(this).parent().offset().top;"
            # compute_coords += "console.log('Left: ' + x + ' Top: ' + y);"
            for other_plane, formula in formulas[anat_plane].iteritems():
                compute_coords += "$('#{0}').find('.slice-bar')".format(
                    other_plane)
                compute_coords += ".each(function () {"
                compute_coords += "$(this).simpleSlider('setValue', {0});".format(
                    formula)
                compute_coords += "});"
            html += "$('#{0}').find('img')".format(anat_plane)
            html += ".each(function () {})"
            html += ".mousedown(function (e) {"
            html += compute_coords
            html += "$(this).mousemove(function (e) {"
            html += compute_coords
            html += "});"
            html += "}).mouseup(function () {"
            html += "$(this).unbind('mousemove');"
            html += "}).mouseout(function () {"
            html += "$(this).unbind('mousemove');"
            html += "});"
        html += "}"
        html += "}"
        html += "$('#fold-viewer').css('height', (im_length+300)+'px');"
        html += "init_slices_viewer();"
        html += "$('#viewer-container').css('visibility', 'visible');"
        html += "$('.btn').each(function () {"
        html += "$(this).prop('disabled', false);"
        html += "});"
        html += "})"
        html += ".fail(function() {"
        html += "alert('error');"
        html += "});"
        html += "});"
        html += "</script>"

        self.w(unicode(html))

@ajaxfunc(output_type="json")
def get_b64_images(self):
    snaps_filepaths = json.loads(self._cw.form["filepaths"])
    output = {}
    for anat_plane in ["sagittal", "coronal", "axial"]:
        output[anat_plane] = {}
        images = snaps_filepaths[anat_plane]
        encoded_images = []
        for image in images:
            with open(image, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read())
                encoded_images.append(encoded_image)
        output[anat_plane] = encoded_images
    return output
