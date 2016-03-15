function init_slices_viewer() {

    function set_image_filters(slice_element, brightness) {
        var filter = "brightness("+brightness+"%)";
        var filter_targets = ['filter', '-webkit-filter', '-moz-filter', '-o-filter', '-ms-filter'];
        $.each(filter_targets, function( _, target ){
            slice_element.css(target, filter)
        });
    }

    var div_elements = {};

    $('.slicer').each(function () {

        var div_id = $(this).attr("id");

        div_elements[div_id] = {};

        var item_elements = $(this).find('.item');
        var slices_elements = $(this).children('.slider-content').find('img');

        var nb_slices = slices_elements.length;

        div_elements[div_id]["slice_index"] = undefined;
        div_elements[div_id]["brightness"] = undefined;

        $(this).children('.slice-bar').each(function () {

            $("<span>").addClass("output").insertAfter($(this));

            var default_slice_index = parseInt($(this).attr("value").split(','));
            div_elements[div_id]["slice_index"] = default_slice_index;

            item_elements.eq(default_slice_index).addClass('shown_'+div_id).show();
        }).bind("slider:ready slider:changed", function (event, data) {

            var parent_div_id = $(this).parent().attr("id");

            var slice_index = data.value;
            div_elements[parent_div_id]["slice_index"] = slice_index;

            $(this).nextAll(".output:first").html(slice_index + ' / ' + (nb_slices-1));

            set_image_filters(slices_elements.eq(slice_index), div_elements[parent_div_id]["brightness"]);

            $('.shown_'+parent_div_id).fadeOut(0).removeClass('shown_'+parent_div_id);
            item_elements.eq(slice_index).fadeIn(0).addClass('shown_'+parent_div_id);
        });

        $(this).children('.brightness-bar').each(function () {
            $("<span>").addClass("output").insertAfter($(this));
        }).bind("slider:ready slider:changed", function (event, data) {

            var parent_div_id = $(this).parent().attr("id");

            var brightness = data.value;
            div_elements[div_id]["brightness"] = brightness;

            $(this).nextAll(".output:first").html(brightness + ' %');

            var slice_index = div_elements[parent_div_id]["slice_index"];

            set_image_filters(slices_elements.eq(slice_index), brightness);
        });

    });

    $('.all-brightness-bar').each(function () {
            $("<span>").addClass("output").insertAfter($(this));
        }).bind("slider:ready slider:changed", function (event, data) {

            var brightness = data.value;
            $(this).nextAll(".output:first").html(brightness + ' %');
            
            $('.slicer').each(function () {
                
                var slices_elements = $(this).children('.slider-content').find('img');
                
                var div_id = $(this).attr("id");
                div_elements[div_id]["brightness"] = brightness;
                var slice_index = div_elements[div_id]["slice_index"];
                set_image_filters(slices_elements.eq(slice_index), brightness);
            });
        });

}
