/**
 * Created by Sayem on 02 January, 2020
 * @author sayem
 */


function BaseTemplate() {
}

BaseTemplate.prototype = {
    hideHeader: function () {
        let $headerNode = $("#brdtitle");
        $headerNode.css({
            display: "none"
        });
    },
    hideFooterExtraTags: function () {
        let pTagCls = ["conr", "lofi"];
        $.each(pTagCls, function (idx, elem) {
            $("p[class=" + elem + "]").css({
                display: "none"
            });
        });
    }
};

$(function () {
    let baseTemplateInstance = new BaseTemplate();
    if (HIDE_DJANGOBB_HEADER) {
        baseTemplateInstance.hideHeader();
    }
    if (HIDE_DJANGOBB_TAGLINE) {
        baseTemplateInstance.hideFooterExtraTags();
    }
});