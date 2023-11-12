function loadTableData(tableId, data, genderClass) {
    let rating = 0;
    let visible_rating = 1;
    let tableContent = '';

    let tableBody = document.getElementById(tableId);
    tableBody.innerHTML = '';
    data.forEach(function (item, index) {
        rating += 1;
        if (index !== 0 && data[index - 1][1] !== data[index][1]) {
            visible_rating = rating
        }
        let name = item[0].replace("/", "<br>");
        tableContent += '<tr class="' + genderClass + '">';
        tableContent += '<td>' + visible_rating + '</td>';
        tableContent += '<td><a href="' + item[2] + '" style="text-decoration: underline" target="_blank">' + name + '</a></td>';
        tableContent += '<td><div class="d-flex align-items-center">' + item[1] + ' (' + item[5] + ')' + '<a href="#" class="score-info ml-2" data-toggle="modal" data-target="#infoModal" data-score="' + name + ', ' + item[3] + '"><i class="fas fa-question-circle" style="font-size: 27px"></i></a></div></td>';
        tableContent += '</tr>';
    });
    $("#" + tableId).html(tableContent);
}

function getParamValue() {
    let urlParts = window.location.href.split('/');
    let paramValue = decodeURIComponent(urlParts[urlParts.length - 1]);
    return {
        breed: paramValue
    };
}

$.ajax({
    url: '/get-score-details-section1',
    method: 'GET',
    data: getParamValue(),
    success: function (data) {
        loadTableData('section1-data', data, 'male-row');
    }
});

$.ajax({
    url: '/get-score-details-section2',
    method: 'GET',
    data: getParamValue(),
    success: function (data) {
        loadTableData('section2-data', data, 'female-row');
    }
});

$.ajax({
    url: '/get-score-details-section3',
    method: 'GET',
    data: getParamValue(),
    success: function (data) {
        loadTableData('section3-data', data, 'male-row');
    }
});

$.ajax({
    url: '/get-score-details-section4',
    method: 'GET',
    data: getParamValue(),
    success: function (data) {
        loadTableData('section4-data', data, 'female-row');
    }
});

$(document).on("click", ".score-info", function () {
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