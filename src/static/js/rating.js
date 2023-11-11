function updateDropdown(maxScore) {
    let dropdownOptions = '';
    const step = 10;
    dropdownOptions += '<option value="all" selected>Все</option>'
    for (let i = 0; i <= maxScore; i += step) {
        dropdownOptions += '<option value="' + i + '-' + (i + step - 1) + '">' + i + '-' + (i + step - 1) + '</option>';
    }

    $("#scoreDropdown").html(dropdownOptions);
}

function updateRatingDropdown(maxRating) {
    let dropdownOptions = '';
    const step = 10;
    dropdownOptions += '<option value="all" selected>Все</option>'
    for (let i = 0; i <= maxRating; i += step) {
        dropdownOptions += '<option value="' + i + '-' + (i + step - 1) + '">' + i + '-' + (i + step - 1) + '</option>';
    }

    $("#ratingDropdown").html(dropdownOptions);
}

$(document).ready(function () {
    let initialRating = $("#ratingDropdown").val();
    let initialSexSelection = $("#sexDropdown").val();
    let initialNameSearch = $("#nameSearch").val();
    let initialScore = $("#scoreDropdown").val();
    let initialType = $("#typeDropdown").val();
    let urlParts = window.location.href.split('/');
    let paramValue = decodeURIComponent(urlParts[urlParts.length - 1]);
    loadData(paramValue, initialRating, initialType, initialSexSelection, initialNameSearch, initialScore, false);
});

function loadData(paramValue, selectedRating, selectedType, selectedSex, nameSearch, selectedScore, allRows = false) {
    $.ajax({
        url: "/get-partial-data",
        type: "POST",
        data: JSON.stringify({
            selectedRating: selectedRating,
            selectedType: selectedType,
            selectedSex: selectedSex,
            paramValue: paramValue,
            allRows: allRows
        }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            let tableContent = '';
            let maxScore = 0;
            let maxRating = 0;
            let selectedRating = document.getElementById("ratingDropdown").value;
            if (data.length === 0) {
                $("#noResultsMessage").show();
                $("#showAllButton").hide();
                $("#showLessButton").hide();
                $("#dogData").html(tableContent);
            } else {
                $("#noResultsMessage").hide();
                let rating = 0;
                let visible_rating = 1;
                let rows_count = 0;

                for (let i = 0; i < data.length; i++) {
                    rating += 1;
                    if (i !== 0 && data[i - 1].TotalScore !== data[i].TotalScore) {
                        visible_rating = rating
                    }

                    let currentScore = parseInt(data[i].TotalScore);
                    if (currentScore > maxScore) {
                        maxScore = currentScore;
                    }
                    if ((i + 1) > maxRating) {
                        maxRating = (i + 1);
                    }
                    let min_score;
                    let max_score;
                    if (selectedScore === 'all') {
                        min_score = 0;
                        max_score = 1000;
                    } else {
                        min_score = parseInt(selectedScore.split('-')[0]);
                        max_score = parseInt(selectedScore.split('-')[1]);
                    }

                    if (data[i].name.includes(nameSearch.toUpperCase()) &&
                        (currentScore <= max_score && currentScore >= min_score)) {
                        rows_count += 1
                        if (allRows === false && rows_count === 10)
                            break;

                        let breed_link = data[i].breedLink;
                        let name = data[i].name.replace("/", "<br>");
                        let genderClass = data[i].sex === 'Сука' ? 'female-row' : 'male-row';

                        tableContent += '<tr class="' + genderClass + '">';
                        if (selectedRating === 'all' || (parseInt(selectedRating.split('-')[1]) >= (i + 1) && (i + 1) >= parseInt(selectedRating.split('-')[0]))) {
                            tableContent += '<td>' + visible_rating + '</td>';
                            tableContent += '<td>' + data[i].sex + '</td>';
                            tableContent += '<td>' + data[i].type + '</td>';
                            tableContent += '<td><a href="' + breed_link + '" style="text-decoration: underline" target="_blank">' + name + '</a></td>';
                            tableContent += '<td><div class="d-flex align-items-center">' + data[i].TotalScore + ' (' + data[i].RecordCount + ')' + '<a href="#" class="score-info ml-2" data-toggle="modal" data-target="#infoModal" data-score="' + name + ', ' + data[i].type + '"><i class="fas fa-question-circle" style="font-size: 27px"></i></a></div></td>';
                            tableContent += '</tr>';
                        }
                    }
                }
                if (maxScore > $("#maxScoreHolder").text()) {
                    updateDropdown(maxScore);
                    $("#maxScoreHolder").text(maxScore);
                }
                if (maxRating > $("#maxRatingHolder").text()) {
                    updateRatingDropdown(maxRating);
                    $("#maxRatingHolder").text(maxRating);
                }

                if (allRows) {
                    $("#showAllButton").hide();
                    $("#showLessButton").show();
                } else {
                    if (rows_count === 10) {
                        tableContent += '<tr><td> ... </td><td> ... </td><td> ... </td><td> ... </td><td> ... </td></tr>';
                    }
                    $("#showAllButton").show();
                    $("#showLessButton").hide();
                }

                if (rows_count < 10) {
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
                        let max_rating = 0;
                        let max_position = 0;
                        for (let i = 0; i < scoreDetails.length; i++) {
                            if (parseInt(scoreDetails[i][3]) > max_rating) {
                                max_rating = parseInt(scoreDetails[i][3]);
                                max_position = parseInt(scoreDetails[i][2]);
                            }
                            if (parseInt(scoreDetails[i][3]) === max_rating && parseInt(scoreDetails[i][2]) > max_position) {
                                max_position = parseInt(scoreDetails[i][2]);
                            }
                        }
                        for (let i = 0; i < scoreDetails.length; i++) {
                            let genderClass = scoreDetails[i][7] === 'Сука' ? 'female-row' : 'male-row';
                            let inputDate = new Date(scoreDetails[i][0]);
                            let day = inputDate.getUTCDate().toString().padStart(2, '0');
                            let month = (inputDate.getUTCMonth() + 1).toString().padStart(2, '0');
                            let year = inputDate.getUTCFullYear();
                            let formattedDate = `${day}.${month}.${year}`;
                            if (parseInt(scoreDetails[i][3]) === max_rating && parseInt(scoreDetails[i][2]) === max_position) {
                                modalTableContent += '<tr class="' + genderClass + '"><td>' + (i + 1) + '</td><td>' + formattedDate + '</td><td>' + scoreDetails[i][8] + '</td><td>' + scoreDetails[i][1] + '</td><td>' + scoreDetails[i][2] + '</td><td>' + scoreDetails[i][3] + '</td><td><a href="' + scoreDetails[i][4] + '" style="font-weight: normal" target="_blank">Ссылка</a></td></tr>';
                            } else {
                                modalTableContent += '<tr><td>' + (i + 1) + '</td><td>' + formattedDate + '</td><td>' + scoreDetails[i][8] + '</td><td>' + scoreDetails[i][1] + '</td><td>' + scoreDetails[i][2] + '</td><td>' + scoreDetails[i][3] + '</td><td><a href="' + scoreDetails[i][4] + '" style="font-weight: normal" target="_blank">Ссылка</a></td></tr>';
                            }
                        }
                        $("#modalTableBody").html(modalTableContent);
                        $("#infoModalLabel").html('Информация о баллах <br>' + '<a href="' + scoreDetails[0][6] + '" style="text-decoration: underline" target="_blank">' + scoreDetails[0][5] + '</a>');

                        $("#infoModal").modal('show');
                    }
                });
            });
        }
    });
}

function updateData(allRows) {
    let initialRating = $("#ratingDropdown").val();
    let selectedType = $("#typeDropdown").val();
    let selectedSex = $("#sexDropdown").val();
    let nameSearch = $("#nameSearch").val();
    let selectedScore = $("#scoreDropdown").val();
    let urlParts = window.location.href.split('/');
    let paramValue = decodeURIComponent(urlParts[urlParts.length - 1]);
    loadData(paramValue, initialRating, selectedType, selectedSex, nameSearch, selectedScore, allRows);
}

$("#nameSearch").on('input', function () {
    updateData(false);
});

$("#sexDropdown").change(function () {
    updateData(false);
});

$("#scoreDropdown").change(function () {
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
