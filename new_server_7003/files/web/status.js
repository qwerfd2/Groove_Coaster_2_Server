let titleList = {};
let userObject = {};
let titleMode = 0;

on_initialize = () => {
    fetch(HOST_URL + 'api/status/title_list?' + PAYLOAD + '&_=' + new Date().getTime())
        .then(response => response.json())
        .then(data => {
            if (data.state) {
                titleList = data.data.title_list;
                userObject = data.data.player_info;
                loadUI();
            } else {
                document.getElementById('status_content').innerText = data.message;
            }
        });
};

function loadUI() {
    let html = `
        <div class="player-element">
            <img src="/files/image/icon/avatar/${userObject['avatar']}.png" class="avatar" alt="Player Avatar">
            <div class="player-info">
                <div class="name">${userObject['username']}</div>
                <img src="/files/image/title/${userObject['title']}.png" class="title" alt="Player Title">
            </div>
            <div class="player-score">Level ${userObject['lvl']}</div>
        </div>
    `;

    let titleTypes = ["Special", "Normal", "Master", "God"];

    let buttonsHtml = '<div class="button-row">';

    for (let i = 0; i < titleTypes.length; i++) {
        if (i === titleMode) {
            buttonsHtml += `<div class="bt_bg01_ac">${titleTypes[i]}</div>`;
        } else {
            buttonsHtml += `<a onclick="setPage(${i})" class="bt_bg01_xnarrow">${titleTypes[i]}</a>`;
        }
    }

    buttonsHtml += '</div>';
    html += `<div style='text-align: center; margin-top: 20px;'>${buttonsHtml}</div>`;

    let selectedTitles = titleList[titleMode] || [];
    
    let titlesHtml = '<div class="title-list">';

    for (let i = 0; i < selectedTitles.length; i++) {
        let title = selectedTitles[i];
        if (i % 2 === 0) {
            if (i !== 0) {
                titlesHtml += '</div>';
            }
            titlesHtml += '<div class="title-row">';
        }
        if (title === userObject['title']) {
            titlesHtml += `
                <img src="/files/image/title/${title}.png" alt="Title ${title}" class="title-image-selected">
            `;
        } else {
            titlesHtml += `
                <a onclick="setTitle(${title})" class="title-link">
                    <img src="/files/image/title/${title}.png" alt="Title ${title}" class="title-image">
                </a>
            `;
        }
    }
    titlesHtml += '</div></div>';
    html += titlesHtml;

    document.getElementById('status_content').innerHTML = html;
}

function setPage(mode) {
    titleMode = mode;
    restoreBaseStructure();
}

function setTitle(title) {
    html = `
        <p>Would you like to change your title?<br>Current Title:</p>
        <img src="/files/image/title/${userObject['title']}.png" alt="Current Title" class="title-image">
        <p>New Title:</p>
        <img src="/files/image/title/${title}.png" alt="New Title" class="title-image">
        <div class="button-container">
            <a onclick="submitTitle(${title})" class="bt_bg01">Confirm</a>
            <a onclick="restoreBaseStructure()" class="bt_bg01">Go back</a>
        </div>
    `;

    document.getElementById('status_content').innerHTML = html;
}

function submitTitle(title) {
    const postData = {
        title: title
    };

    const controller = new AbortController();
    const signal = controller.signal;

    let html = `
        <p>Submitting...</p>
        <button id="backButton" class="loading-back-button">
            Back
        </button>
    `;

    document.getElementById('status_content').innerHTML = html;

    document.getElementById('backButton').onclick = () => {
        controller.abort();
        restoreBaseStructure();
    };

    fetch(HOST_URL + 'api/status/set_title?' + PAYLOAD + '&_=' + new Date().getTime(), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData),
        signal: signal // Pass the abort signal
    })
        .then(response => response.json())
        .then(payload => {
            if (payload.state === 1) {
                userObject['title'] = title;
                restoreBaseStructure();
            } else {
                let html = `
                    <p>Failed. ${payload.message}</p>
                    <div class="button-container">
                        <a onclick="restoreBaseStructure()" class="bt_bg01">Go back</a>
                    </div>
                `;
                document.getElementById('status_content').innerHTML = html;
            }
        }
        )
        .catch(error => {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted');
            } else {
                let html = `

                    <p>Network error. Please try again.</p>
                    <div class="button-container">
                        <a onclick="restoreBaseStructure()" class="bt_bg01">Go back</a>
                    </div>
                `;
                document.getElementById('status_content').innerHTML = html;
            }
        });
}

function restoreBaseStructure() {
    document.getElementById('status_content').innerHTML = ``;
    loadUI();
}


window.onload = function(){
    restoreBaseStructure();
    on_initialize();
};