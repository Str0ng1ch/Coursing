var count = 0;
var SelectedID, SelectedDate, SelectedType, SelectedSex, NameSearch, SelectedRating, SelectedLocation, SelectedBreed,
    AllRows;

var lastSubmitTime = 0;

function submitFormWithDelay(delay) {
    var currentTime = new Date().getTime();
    if (currentTime - lastSubmitTime >= delay) {
        lastSubmitTime = currentTime;
        return true;
    } else {
        alert("Пожалуйста, подождите не менее 2 секунд перед следующей отправкой.");
        return false;
    }
}


function saveFormValues() {
    const form = document.querySelector('form');
    form.addEventListener('input', function (event) {
        const inputElement = event.target;
        const id = inputElement.id;
        if (id === 'date' || id === 'type' || id === 'sex' || id === 'max_position' || id === 'link' || id === 'location' || id === 'breed') {
            localStorage.setItem(id, inputElement.value);
        }
    });
}

function loadFormValues() {
    const form = document.querySelector('form');
    form.querySelectorAll('input, select').forEach(function (inputElement) {
        const id = inputElement.id;
        if (id === 'date' || id === 'type' || id === 'sex' || id === 'max_position' || id === 'link' || id === 'location' || id === 'breed') {
            const savedValue = localStorage.getItem(id);
            if (savedValue !== null) {
                inputElement.value = savedValue;
            }
        }
    });
}

saveFormValues();
loadFormValues();

document.addEventListener("DOMContentLoaded", function () {
    let messageElement = document.getElementById("message");
    if (messageElement) {
        setTimeout(function () {
            messageElement.style.display = "none";
        }, 5000);
    }
});

function calculateScore() {
    let maxPosition = parseInt(document.getElementById("max_position").value);
    let position = parseInt(document.getElementById("position").value);
    let score = maxPosition - position + 1;
    if (!isNaN(score)) {
        document.getElementById("score").value = score;
    }
}

document.getElementById("max_position").addEventListener("input", calculateScore);
document.getElementById("position").addEventListener("input", calculateScore);

function updateDropdown(maxScore) {
    let dropdownOptions = '';
    const step = 10;
    dropdownOptions += '<option value="all" selected>Все</option>'
    for (let i = 0; i <= maxScore; i += step) {
        dropdownOptions += '<option value="' + i + '-' + (i + step - 1) + '">' + i + '-' + (i + step - 1) + '</option>';
    }

    $("#ratingDropdown").html(dropdownOptions);
}

$("#dogData").on("blur", "td[contenteditable='true']", function () {
    const cell = $(this);
    const row = $(this).closest("tr");
    const updatedData = {
        id: row.find("td:eq(0)").text(),
        date: row.find("td:eq(1)").text(),
        position: row.find("td:eq(2)").text(),
        type: row.find("td:eq(3)").text(),
        sex: row.find("td:eq(4)").text(),
        nickname: row.find("td:eq(5)").text(),
        max_position: row.find("td:eq(6)").text(),
        score: row.find("td:eq(7)").text(),
        link: row.find("td:eq(8)").text(),
        BreedLink: row.find("td:eq(9)").text(),
        location: row.find("td:eq(10)").text(),
        breed: row.find("td:eq(11)").text(),
    };

    $.ajax({
        url: "/update-data",
        type: "POST",
        data: JSON.stringify(updatedData),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            cell.addClass("bg-success");
            setTimeout(function () {
                cell.removeClass("bg-success");
            }, 1500);
        },
        error: function (error) {
            cell.addClass("bg-danger");
            setTimeout(function () {
                cell.removeClass("bg-danger");
            }, 1500);
        },
    });
});

$(document).ready(function () {
    $('.column-checkbox').each(function () {
        let columnName = $(this).attr('id');
        let isColumnVisible = $(this).is(':checked');

        if (isColumnVisible) {
            $(`th[data-column="${columnName}"]`).show();
        } else {
            $(`th[data-column="${columnName}"]`).hide();
        }
    });

    let initialSexSelection = $("#sexDropdown").val();
    let initialNameSearch = $("#nameSearch").val();
    let initialRatingSelection = $("#ratingDropdown").val();
    let initialType = $("#typeDropdown").val();
    loadData('', '', initialType, initialSexSelection, initialNameSearch, initialRatingSelection, 'all', 'all', false);
});

function loadData(selectedID, selectedDate, selectedType, selectedSex, nameSearch, selectedRating, selectedLocation, selectedBreed, allRows = false) {
    SelectedID = selectedID;
    SelectedDate = selectedDate;
    SelectedType = selectedType;
    SelectedSex = selectedSex;
    NameSearch = nameSearch;
    SelectedRating = selectedRating;
    SelectedLocation = selectedLocation;
    SelectedBreed = selectedBreed;
    AllRows = allRows;
    $.ajax({
        url: "/get-all-data",
        type: "POST",
        data: JSON.stringify({
            selectedID: selectedID,
            selectedDate: selectedDate,
            selectedType: selectedType,
            selectedSex: selectedSex,
            nameSearch: nameSearch,
            selectedRating: selectedRating,
            selectedLocation: selectedLocation,
            selectedBreed: selectedBreed,
            allRows: allRows
        }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            let tableContent = '';
            let maxScore = 0;
            if (data.length === 0) {
                $("#noResultsMessage").show();
                $("#showAllButton").hide();
                $("#showLessButton").hide();
                $("#dogData").html(tableContent);
            } else {
                $("#noResultsMessage").hide();
                let checkboxDate = document.getElementById("columnDate");
                let checkboxID = document.getElementById("columnID");
                let checkboxPosition = document.getElementById("columnPosition");
                let checkboxType = document.getElementById("columnType");
                let checkboxSex = document.getElementById("columnSex");
                let checkboxNickname = document.getElementById("columnNickname");
                let checkboxMaxPosition = document.getElementById("columnMaxPosition");
                let checkboxScore = document.getElementById("columnScore");
                let checkboxLink = document.getElementById("columnLink");
                let checkboxBreedLink = document.getElementById("columnBreedLink");
                let checkboxLocation = document.getElementById("columnLocation");
                let checkboxBreed = document.getElementById("columnBreed");

                for (let i = 0; i < data.length; i++) {
                    let currentScore = parseInt(data[i].score);

                    if (currentScore > maxScore) {
                        maxScore = currentScore;
                    }

                    let genderClass = data[i].sex === 'Сука' ? 'female-row' : 'male-row';
                    let inputDate = new Date(data[i].date);
                    let day = inputDate.getUTCDate().toString().padStart(2, '0');
                    let month = (inputDate.getUTCMonth() + 1).toString().padStart(2, '0');
                    let year = inputDate.getUTCFullYear();
                    let formattedDate = `${day}.${month}.${year}`;
                    tableContent += '<tr class="' + genderClass + '">';
                    if (checkboxID.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].id + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].id + '</td>';
                    }
                    if (checkboxDate.checked) {
                        tableContent += '<td contenteditable="true">' + formattedDate + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + formattedDate + '</td>';
                    }
                    if (checkboxPosition.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].position + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].position + '</td>';
                    }
                    if (checkboxType.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].type + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].type + '</td>';
                    }
                    if (checkboxSex.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].sex + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].sex + '</td>';
                    }
                    if (checkboxNickname.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].Nickname + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">>' + data[i].Nickname + '</td>';
                    }
                    if (checkboxMaxPosition.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].max_position + '</td>';
                    } else {
                        tableContent += '<td style="display: none" contenteditable="true">' + data[i].max_position + '</td>';
                    }
                    if (checkboxScore.checked) {
                        tableContent += '<td contenteditable="true"><div class="d-flex align-items-center">' + data[i].score + '<a href="#" class="score-info ml-2" data-toggle="modal" data-target="#infoModal" data-score="' + name + ', ' + data[i].type + '"><i class="fas fa-question-circle"></i></a></div></td->';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none"><div class="d-flex align-items-center">' + data[i].score + '<a href="#" class="score-info ml-2" data-toggle="modal" data-target="#infoModal" data-score="' + name + ', ' + data[i].type + '"><i class="fas fa-question-circle"></i></a></div></td>';
                    }
                    if (checkboxLink.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].link + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].link + '</td>';
                    }
                    if (checkboxBreedLink.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].breedLink + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].breedLink + '</td>';
                    }
                    if (checkboxLocation.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].location + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].location + '</td>';
                    }
                    if (checkboxBreed.checked) {
                        tableContent += '<td contenteditable="true">' + data[i].breed + '</td>';
                    } else {
                        tableContent += '<td contenteditable="true" style="display: none">' + data[i].breed + '</td>';
                    }
                    tableContent += '</tr>';
                }

                if (maxScore > $("#maxScoreHolder").text()) {
                    updateDropdown(maxScore);
                    $("#maxScoreHolder").text(maxScore);
                }

                let checkboxes = [
                    document.getElementById("columnDate"),
                    document.getElementById("columnID"),
                    document.getElementById("columnPosition"),
                    document.getElementById("columnType"),
                    document.getElementById("columnSex"),
                    document.getElementById("columnNickname"),
                    document.getElementById("columnMaxPosition"),
                    document.getElementById("columnScore"),
                    document.getElementById("columnLink"),
                    document.getElementById("columnBreedLink"),
                    document.getElementById("columnLocation"),
                    document.getElementById("columnBreed")
                ];
                let selectedCheckboxes = checkboxes.filter(checkbox => checkbox.checked);

                if (allRows) {
                    $("#showAllButton").hide();
                    $("#showLessButton").show();
                } else {
                    if (data.length === 9) {
                        tableContent += '<tr>';
                        selectedCheckboxes.forEach(checkbox => {
                            tableContent += '<td> ... </td>';
                        });
                        tableContent += '</tr>';
                    }
                    $("#showAllButton").show();
                    $("#showLessButton").hide();
                }

                if (data.length < 9) {
                    $("#showAllButton").hide();
                }

                $("#dogData").html(tableContent);
            }

            $(".score-info").click(function () {
                let score = $(this).data('score');
                $.ajax({
                    url: "/get-score-details",
                    type: "POST",
                    data: JSON.stringify({score: score}),
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    success: function (scoreDetails) {
                        let modalTableContent = '';
                        for (let i = 0; i < scoreDetails.length; i++) {
                            let inputDate = new Date(scoreDetails[i][0]);
                            let day = inputDate.getUTCDate().toString().padStart(2, '0');
                            let month = (inputDate.getUTCMonth() + 1).toString().padStart(2, '0');
                            let year = inputDate.getUTCFullYear();
                            let formattedDate = `${day}.${month}.${year}`;
                            modalTableContent += '<tr><td>' + formattedDate + '</td><td>' + scoreDetails[i][1] + '</td><td>' + scoreDetails[i][2] + '</td><td>' + scoreDetails[i][3] + '</td><td><a href="' + scoreDetails[i][4] + '" target="_blank">Источник</a></td></tr>';
                        }
                        $("#modalTableBody").html(modalTableContent);
                        $("#infoModal").modal('show');
                    }
                });
            });
        }
    });
}

$("#checkDatabaseModalTableBody").on("click", ".delete-row", function () {
    let row = $(this).closest('tr');
    let id = $(this).data('id');
    let error = $(this).data('error');
    let updatedData = {id: id, error: error};

    $.ajax({
        url: "/ignore-data",
        type: "POST",
        data: JSON.stringify(updatedData),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (response) {
            row.remove();
        },
        error: function (error) {
            row.addClass("bg-danger");
            setTimeout(function () {
                row.removeClass("bg-danger");
            }, 1500);
        },
    });
});


$(".check-database-without-links").click(function () {
    let score = $(this).data('score');
    $.ajax({
        url: "/check-database-without-links",
        type: "POST",
        data: JSON.stringify({score: score}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            let modalTableContent = '';
            for (let i = 0; i < data.length; i++) {
                modalTableContent += '<tr>'
                modalTableContent += '<td> <a class="delete-row" data-error="' + data[i].error + '" data-id="' + data[i].id + '"> <i class="fas fa-times"></i> </a></td>';
                modalTableContent += '<td>' + data[i].id + '</td>';
                modalTableContent += '<td>' + data[i].error + '</td>';
                modalTableContent += '</tr>'
            }
            console.log(modalTableContent);
            $("#checkDatabaseModalTableBody").html(modalTableContent);
            $("#checkDatabase").modal('show');
        }
    });
});

$(".check-database-with-links").click(function () {
    let score = $(this).data('score');
    $.ajax({
        url: "/check-database-with-links",
        type: "POST",
        data: JSON.stringify({score: score}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            let modalTableContent = '';
            for (let i = 0; i < data.length; i++) {
                modalTableContent += '<tr>'
                modalTableContent += '<td> <a class="delete-row" data-error="' + data[i].error + '" data-id="' + data[i].id + '"> <i class="fas fa-times"></i> </a></td>';
                modalTableContent += '<td>' + data[i].id + '</td>';
                modalTableContent += '<td>' + data[i].error + '</td>';
                modalTableContent += '</tr>'
            }
            console.log(modalTableContent);
            $("#checkDatabaseModalTableBody").html(modalTableContent);
            $("#checkDatabase").modal('show');
        }
    });
});

$('.column-checkbox').change(function () {
    let columnName = $(this).attr('id');
    let isColumnVisible = $(this).is(':checked');

    if (isColumnVisible) {
        $(`th[data-column="${columnName}"]`).show();
    } else {
        $(`th[data-column="${columnName}"]`).hide();
    }
    loadData(SelectedID, SelectedDate, SelectedType, SelectedSex, NameSearch, SelectedRating, SelectedLocation, SelectedBreed, AllRows);
});

function updateData(allRows) {
    let selectedType = $("#typeDropdown").val();
    let selectedSex = $("#sexDropdown").val();
    let nameSearch = $("#nameSearch").val();
    let selectedRating = $("#ratingDropdown").val();
    let selectedDate = $("#dateSelection").val();
    let selectedID = $("#idSearch").val();
    // let selectedLocation = $("#idSearch").val();
    let selectedBreed = $("#breedDropdown").val();
    console.log(selectedBreed)
    loadData(selectedID, selectedDate, selectedType, selectedSex, nameSearch, selectedRating, 'all', selectedBreed, allRows);
}

$("#nameSearch").on('input', function () {
    updateData(false);
});

$("#idSearch").on('input', function () {
    updateData(false);
});

$("#sexDropdown").change(function () {
    updateData(false);
});

$("#ratingDropdown").change(function () {
    updateData(false);
});

$("#typeDropdown").change(function () {
    updateData(false);
});

$("#showAllButton").click(function () {
    updateData(true);
});

$("#showLessButton").click(function () {
    updateData(false);
});

$("#dateSelection").on("change", function () {
    updateData(false);
});

$("#breedDropdown").change(function () {
    updateData(false);
});