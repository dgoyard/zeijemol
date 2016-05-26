# coding: utf-8
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
            formulas = {
                "sagittal": {
                    "axial": "Math.round(y*nb_slices/im_length)",
                    "coronal": "Math.round(x*nb_slices/im_length)"
                },
                "coronal": {
                    "sagittal": "Math.round(x*nb_slices/im_length)",
                    "axial": "Math.round(y*nb_slices/im_length)"
                },
                "axial": {
                    "sagittal": "Math.round(x*nb_slices/im_length)",
                    "coronal": "Math.round(nb_slices-y*nb_slices/im_length)"
                }
            }

        # Add JS and CSS resources for the sliders
        self._cw.add_js("jquery-simple-slider/js/simple-slider.min.js")
        self._cw.add_css("jquery-simple-slider/css/simple-slider-volume.css")
        self._cw.add_css("slices_viewer.css")

        # Add an hidden loading image
        html = "<div id='loading-msg' style='display: none;' align='center'>"
        loading_img_url = self._cw.data_url('images/loadData-lg.gif')
        html += "<img src='{0}'/>".format(loading_img_url)
        html += "</div>"

        # Create the 3 viewer columns :  sagittal, coronal, axial
        filepaths = {}
        anat_planes = ["sagittal", "coronal", "axial"]
        nb_slices = None
        im_length = None
        for anat_plane in anat_planes:

            snap_id = snaps_identifiers[anat_plane]
            rql_images = ("Any F Where S is Snap, S identifier '{0}', "
                          "S filepaths F".format(snap_id))
            rset_images = self._cw.execute(rql_images)
            images = json.loads(rset_images[0][0].getvalue())

            if im_length is None:
                with Image.open(images[0]) as im:
                    width, height = im.size
                    assert width == height
                    im_length = width

            filepaths[anat_plane] = images

            if nb_slices is None:
                nb_slices = len(images)
            if len(images) != nb_slices:
                raise Exception("The number of slices per anatomical plane"
                                "must be constant")

        html += "<style>"
        html += ".slider-volume {"
        html += "width: {0}px;".format(int(95*im_length/100))
        html += "}"
        html += "</style>"

        max_slice_index = nb_slices - 1
        default_slice_index = int(max_slice_index/2)

        anat_planes = ["sagittal", "coronal", "axial"]
        html += "<div class='container'>"
        for idx, anat_plane in enumerate(anat_planes):
            html += "<div id='{0}' class='subdiv'>".format(anat_plane)
            if idx == 1:
                html += "<h4 style='color: white;'>BRIGHTNESS</h4>"
                html += ("<input id='brightness-bar' type='text' "
                         "data-slider='true' data-slider-range='0,200' "
                         "value='100' data-slider-step='1' "
                         "data-slider-highlight='true' "
                         "data-slider-theme='volume'>")
                html += ("<p id='brightness-bar-text' style='color: "
                         "white;margin-bottom: 50px;'>100 %</p>")
            html += "<h4 style='color: white;'>{0}</h4>".format(
                anat_plane.upper())
            html += ("<input class='slice-bar' type='text' data-slider='true' "
                     "data-slider-range='0,{0}' value='{1}' "
                     "data-slider-step='1' data-slider-highlight='true' "
                     "data-slider-theme='volume'>".format(
                         max_slice_index, default_slice_index))
            html += ("<p class='slice-bar-text' style='color: white;'>"
                     "{0} / {1}</p>".format(
                         default_slice_index, max_slice_index))
            html += ("<canvas class='slice-img' width='{0}' height='{0}'>"
                     "</canvas>".format(im_length))
            html += "</div>"
        html += "</div>"

        html += "<script>"
        html += "$(document).ready(function() {"
        html += "$('.gallery-btn').each(function () {"
        html += "$(this).prop('disabled', true);"
        html += "});"

        html += "var formulas = {0};".format(json.dumps(formulas))
        ajax_url = self._cw.build_url("ajax", fname="get_b64_images")
        html += "var nb_slices = {0};".format(nb_slices)
        html += "var im_length = {0};".format(im_length)
        html += "var anat_planes = {0};".format(json.dumps(anat_planes))
        html += "var brightness = 100;"

        html += "function draw_img(canvas_context, encoded_img) {"
        html += "var image = new Image();"
        html += "image.onload = function() {"
        html += "canvas_context.drawImage(image, 0, 0);"
        html += "};"
        html += "image.src = 'data:image/  png;base64,' + encoded_img;"
        html += "};"

        html += "function getMousePos(canvas_el, evt) {"
        html += "var rect = canvas_el.getBoundingClientRect();"
        html += "return {"
        html += "x: evt.clientX - rect.left,"
        html += "y: evt.clientY - rect.top"
        html += "};"
        html += "}"

        html += "function cursor_changed(evt, canvas_el, plane){"
        html += "var pos = getMousePos(canvas_el, evt);"
        html += "x = pos.x;"
        html += "y = pos.y;"
        html += "$.each(formulas[plane], function( other_plane, formula ) {"
        html += "$('#'+other_plane).find('.slice-bar').each(function () {"
        html += "$(this).simpleSlider('setValue', eval(formula));"
        html += "});"
        html += "});"
        html += "}"

        html += "function set_brightness(canvas_el, brightness) {"
        html += "var filter = 'brightness('+brightness+'%)';"
        html += ("var filter_targets = ['filter', '-webkit-filter', "
                 "'-moz-filter', '-o-filter', '-ms-filter'];")
        html += "$.each(filter_targets, function( _, target ){"
        html += "canvas_el.css(target, filter);"
        html += "});"
        html += "}"

        html += "$('#loading-msg').show();"
        html += "$.post('{0}', {{'filepaths': JSON.stringify({1})}})".format(
            ajax_url, json.dumps(filepaths))
        html += ".done(function(ajax_data) {"

        html += "$.each(anat_planes, function( index, plane_name ) {"
        html += "var canvas = $('#'+plane_name).children('canvas');"
        html += "var canvas_el = canvas.get(0);"

        html += "canvas.mousedown(function (e) {"
        html += "cursor_changed(e, canvas_el, plane_name);"
        html += "$(this).mousemove(function (e) {"
        html += "cursor_changed(e,canvas_el, plane_name);"
        html += "});"
        html += "}).mouseup(function () {"
        html += "$(this).unbind('mousemove');"
        html += "}).mouseout(function () {"
        html += "$(this).unbind('mousemove');"
        html += "});"

        html += "var ctx = canvas_el.getContext('2d');"
        html += "$('#'+plane_name).children('.slice-bar').each(function () {"
        html += "$('<span>').addClass('output').insertAfter($(this));"
        html += "draw_img(ctx, ajax_data[plane_name][{0}]);".format(
            default_slice_index)
        html += "set_brightness(canvas, brightness);"
        # Close slice-bar each
        html += "})"
        html += (".bind('slider:ready slider:changed', "
                 "function (event, data) {")
        html += "var slice_index = data.value;"
        html += ("$('#'+plane_name).children('.slice-bar-text').html("
                 "slice_index + ' / ' + {0});".format(max_slice_index))
        html += "draw_img(ctx, ajax_data[plane_name][slice_index]);"
        html += "set_brightness(canvas, brightness);"
        # Close bind
        html += "});"
        # Close iteration over anat planes
        html += "});"

        html += "$('#brightness-bar').each(function () {"
        html += ("}).bind('slider:ready slider:changed', "
                 "function (event, data) {")
        html += "brightness = data.value;"
        html += "$('#brightness-bar-text').html(brightness + ' %');"
        html += "$('.slice-img').each(function () {"
        html += "set_brightness($(this), brightness);"
        html += "});"
        html += "});"

        html += "$('#loading-msg').hide();"

        html += "$('.container').show();"

        html += "$('.gallery-btn').each(function () {"
        html += "$(this).prop('disabled', false);"
        html += "});"

        # Close ajax done
        html += "});"
        # close document
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
