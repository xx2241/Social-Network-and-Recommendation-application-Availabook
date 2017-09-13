$(document).ready(function() {
    $(window).load(function() {
        $(".loader").fadeOut("slow");
    });

    console.log("ready!");

    $("#home_logout_btn").on("click", function() {
        console.log("logout!");
        $.ajax({
            url : "/availabook/logout/",
            type : "GET",

            success : function(msg) {
                //$("body").html(msg);
                console.log("logout success!");
                window.location.href = "/availabook/home";
                //window.location.reload();
            },

            error : function(xhr,errmsg,err) {
                console.log("logout " + errmsg);
            }
        })
    })

    $("#home_profile_btn").on("click", function() {
        console.log("profile!");
        $.ajax({
            url : "/availabook/profile/",
            type : "GET",

            success : function(msg) {
                //$("body").html(msg);
                console.log("profile success!");
                window.location.reload();
            },

            error : function(xhr,errmsg,err) {
                console.log("profile " + errmsg);
            }
        })
    });

    // Get the modal and when the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        var modals = document.getElementsByClassName('modal');
        for (var i = 0; i <  modals.length; i++) {
            if (event.target == modals[i]) {
            modals[i].style.display = "none";
            }
        }
    };
});

$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

$(function () {
  $('[data-toggle="popover"]').popover()
})
