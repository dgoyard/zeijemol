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

    def call(self, snaps_eids):
        
        self._cw.add_js("slices_viewer.js")
        self._cw.add_js("jquery-simple-slider/js/simple-slider.min.js")
        self._cw.add_css("jquery-simple-slider/css/simple-slider-volume.css")
        self._cw.add_css("jquery-simple-slider/css/simple-slider.css")
        html = "<div id='loading-message' style='display:none' align='center'><img src='{0}'/></div>".format(self._cw.data_url('images/loadData-lg.gif'))
        html += "<div id='slices-viewer-container' style='visibility: hidden;'>"
        html += "<div class='row' style='width: 100%;'>"
        for snap_eid in snaps_eids:
            rql = "Any S Where S is Snap, S eid '{0}'".format(snap_eid)
            rset = self._cw.execute(rql)
            snap_entity = rset.get_entity(0, 0)
            volume_name = snap_entity.name
            slices_nb = len(json.loads(snap_entity.filepaths.getvalue()))
            volume_id = "_".join(volume_name.split())
            html += "<div id='{0}' class='col-md-4 slicer'>".format(volume_name)
            html += "<h4 style='color: white;'>{0}</h4>".format(volume_name)
            html += "<h5 style='color: white;'>Brightness</h5>"
            html += ("<input class='brightness-bar' type='text' data-slider='true' "
                     "data-slider-range='0,200' value='100' "
                     "data-slider-step='1' data-slider-highlight='true' data-slider-theme='volume'>")
            html += "<h5 style='color: white;'>Browse volume</h5>"
            html += ("<input class= 'slice-bar' type='text' data-slider='true' "
                     "data-slider-range='0,{0}' value='{1}' data-slider-step='1' "
                     "data-slider-highlight='true' data-slider-theme='volume'>".format(slices_nb-1, round(slices_nb/2)))
            html += "<div class='ui-corner-all slider-content'>"
            html += "<div class='viewer ui-corner-all'>"
            html += "<div class='content-conveyor ui-helper-clearfix slices-container'>"
            html += "</div>"
            html += "</div>"
            html += "</div>"
            html += "</div>"
        html += "</div>"
        html += "</div>"
        
        html += "<style>"
        html += """
[class^=slider] { display: inline-block; margin-bottom: 30px; }
.output { color: #888; font-size: 14px; padding-top: 1px; margin-left: 5px; vertical-align: top;}
.slider-volume {
    width: 100px;
}
.slider {
    width: 100px;
}
.item {
    display: none;
    position: absolute;
}"""
        html += "</style>"

        html += "<script>"
        html += "$(document).ready(function() {"
        post_data = {"snaps_eids": snaps_eids}
        html += """
        $('.btn').each(function () {$(this).prop('disabled', true);}); 
$('#loading-message').show();
$.post("%s", %s)
  .done(function(data) {
  $('#loading-message').hide();
    
        var height_max = 0;
        for (var key in data) {
  if (data.hasOwnProperty(key)) {
    var images = '';
    for (var j = 0; j < data[key]['data'].length; j++) {
        images += "<div class='item zoom'><img class='img-responsive' src='data:image/png;base64," + data[key]['data'][j] + "' /></div>";
        }
    height_max = data[key]['max_dimensions'][1];
    $('#'+key).find('.slices-container').each(function () {$(this).html(images)});
    //document.getElementById('slices_' + j).innerHTML = images;
  }
}

    $('#fold-viewer').css('height', (height_max+200)+'px');
    init_slices_viewer();
    
    $('#slices-viewer-container').css('visibility', 'visible');
    $('.btn').each(function () {$(this).prop('disabled', false);}); 
  })
  .fail(function() {
    //alert( "error" );
  });
        """ % (self._cw.build_url("ajax", fname="get_b64_images"), json.dumps(post_data))
        html += "});"
        html += "</script>"

        self.w(unicode(html))

@ajaxfunc(output_type="json")
def get_b64_images(self):
    output = {}
    print self._cw.form
    snaps_eids = self._cw.form["snaps_eids[]"]
    print type(snaps_eids)
    heights = []
    widths = []
    for snap_eid in snaps_eids:
        rql = "Any S Where S is Snap, S eid '{0}'".format(snap_eid)
        rset = self._cw.execute(rql)
        snap_entity = rset.get_entity(0, 0)
        snap_name = snap_entity.name
        output[snap_name] = {}
        filepaths = json.loads(snap_entity.filepaths.getvalue())
        with Image.open(filepaths[0]) as im:
            width, height = im.size
            widths.append(width)
            heights.append(height)
        encoded_images = []
        for filepath in filepaths:
            with open(filepath, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read())
                encoded_images.append(encoded_image)
        output[snap_name]['data'] = encoded_images
        output[snap_name]['max_dimensions'] = [max(widths), max(heights)]
    return output
