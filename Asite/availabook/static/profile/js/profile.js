$(document).ready(function() {

    console.log("profile ready");


    $("#file-input").on("change", function() {
        $("#formid").submit();
});
    // document.getElementById('fn').innerHTML=response.fname;
    // document.getElementById('ln').innerHTML=response.lname;
    // document.getElementById('age').innerHTML=response.age;
    // document.getElementById('ct').innerHTML=response.city;
    // document.getElementById('zip').innerHTML=response.zipcode;

    $('#userForm').formValidation({
            framework: 'bootstrap',
            icon: {
                valid: 'glyphicon glyphicon-ok',
                invalid: 'glyphicon glyphicon-remove',
                validating: 'glyphicon glyphicon-refresh'
            },
            fields: {
                fname: {
                    validators: {
                        notEmpty: {
                            message: 'The first name is required'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z\s]+$/,
                            message: 'The full name can only consist of alphabetical characters'
                        }
                    }
                },
                lname: {
                    validators: {
                        notEmpty: {
                            message: 'The first name is required'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z\s]+$/,
                            message: 'The full name can only consist of alphabetical characters'
                        }
                    }
                },
                age: {
                    validators: {
                        notEmpty: {
                            message: 'The first name is required'
                        },
                        regexp: {
                            regexp: /^[0-9\s]+$/,
                            message: 'The full name can only consist of number'
                        }
                    }
                },
                city: {
                    validators: {
                        notEmpty: {
                            message: 'The first name is required'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z\s]+$/,
                            message: 'The full name can only consist of number'
                        }
                    }
                },
                zipcode: {
                    validators: {
                        notEmpty: {
                            message: 'The first name is required'
                        },
                        regexp: {
                            regexp: /^[0-9\s]+$/,
                            message: 'The full name can only consist of number'
                        }
                    }
                },
            }
        })
        .on('success.form.fv', function(e) {
            // Save the form data via an Ajax request
            console.log("form.fv");
            console.log(e);
            e.preventDefault();

            var $form = $(e.target),
                id    = $form.find('[name="id"]').val();

            // The url and method might be different in your application
            $.ajax({
                url: "/availabook/edit/",
                method: 'POST',
                data: $form.serialize()
            }).success(function(response) {
                // Get the cells
                console.log(response);
                var $button = $('button[data-id=1]')
                    // $tr     = $button.closest('tr'),
                    // $cells  = $tr.find('td');

                document.getElementById('fn').innerHTML=response.fname
                document.getElementById('ln').innerHTML=response.lname
                document.getElementById('age').innerHTML=response.age
                document.getElementById('ct').innerHTML=response.city
                document.getElementById('zip').innerHTML=response.zipcode
                // Update the cell data
                // $cells
                //     .eq(1).html(response.name).end()
                //     .eq(2).html(response.email).end()
                //     .eq(3).html(response.website).end();

                // Hide the dialog
                $form.parents('.bootbox').modal('hide');

                // You can inform the user that the data is updated successfully
                // by highlighting the row or showing a message box
                // bootbox.alert('The user profile is updated');
            });
        });

    $('.editButton').on('click', function() {
        // Get the record's ID via attribute
        console.log("editing");
        var id = $(this).attr('data-id');
		console.log("editing2");
        $.ajax({
            url: "/availabook/info/",
            method: 'GET',
        }).success(function(response) {
            // Populate the form fields with the data returned from server
            console.log(response);
            $('#userForm')
                .find('[name="id"]').val(response.id).end()
                .find('[name="fname"]').val(response.fname).end()
                .find('[name="lname"]').val(response.lname).end()
                .find('[name="age"]').val(response.age).end()
                .find('[name="city"]').val(response.city).end()
                .find('[name="zipcode"]').val(response.zipcode).end();
             console.log("bootbox");
            // Show the dialog
            bootbox.dialog({
                    title: 'Edit the user profile',
                    message: $('#userForm'),
                    show: false // We will show it manually later
                }).on('shown.bs.modal', function() {
                	console.log("dialog");
                    $('#userForm')
                        .show()                             // Show the login form
                        .formValidation('resetForm'); // Reset form
                })
                .on('hide.bs.modal', function(e) {
                	console.log("dialog2");
                    // Bootbox will remove the modal (including the body which contains the login form)
                    // after hiding the modal
                    // Therefor, we need to backup the form
                    $('#userForm').hide().appendTo('body');
                })
                .modal('show');
        });
        console.log("edit end");
    });
});

