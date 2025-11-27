let searchTerm = '';
let songList = [];
let userStage = [];
let tmpSongList = [];
let individualMode = 2;
let totalMode = 0;

on_initialize = () => {
    fetch(HOST_URL + 'api/ranking/song_list?' + PAYLOAD + '&_=' + new Date().getTime())
        .then(response => response.json())
        .then(data => {
            if (data.state) {
                songList = data.data.song_list;
                userStage = data.data.my_stage;
                loadUI();
                filterList();
                loadList();
            } else {
                document.getElementById('ranking_content').innerText = data.message;
            }
        });
};

function loadUI() {
    const searchBar = document.getElementById('ranking_searchbar');
    searchBar.addEventListener('input', (event) => {
        searchTerm = event.target.value.toLowerCase();
        filterList();
    });

    const sortSelect = document.getElementById('ranking_sort');
    sortSelect.addEventListener('change', (event) => {
        sortList(event.target.value);
    });
}

function loadList() {
    let html = `
        <li class="song-item">
            <a onclick="showDetailTotal(0, 0);" class="song-button-owned">Total Score</a>
        </li>
    `;
    for (let i = 0; i < tmpSongList.length; i++) {
        const song = tmpSongList[i];
        if (userStage.includes(song.id)) {
            html += `
                <li class="song-item">
                    <a onclick="showDetailIndividual(${song.id}, ${individualMode}, 0);" class="song-button-owned">
                        <div class="song-name">${song.name_en}</div>
                        <div class="composer-name-owned">${song.author_en}</div>
                    </a>
                </li>
            `;
        } else {
            html += `
                <li class="song-item">
                    <a onclick="showDetailIndividual(${song.id}, ${individualMode}, 0);" class="song-button-unowned">
                        <div class="song-name">${song.name_en}</div>
                        <div class="composer-name-unowned">${song.author_en}</div>
                    </a>
                </li>
            `;
        }
        
    }
    document.getElementById('song_list').innerHTML = html;
}

function filterList() {
    if (searchTerm.trim() === '') {
        tmpSongList = [...songList];
    } else {
        tmpSongList = songList.filter(song => 
            song.name_en.toLowerCase().includes(searchTerm) || 
            song.author_en.toLowerCase().includes(searchTerm)
        );
    }
    loadList();
}

function sortList(criteria) {
    switch (criteria) {
        case 'name':
            tmpSongList.sort((a, b) => a.name_en.localeCompare(b.name_en));
            break;
        case 'name_inverse':
            tmpSongList.sort((a, b) => b.name_en.localeCompare(a.name_en));
            break;
        case 'author':
            tmpSongList.sort((a, b) => a.author_en.localeCompare(b.author_en));
            break;
        case 'author_inverse':
            tmpSongList.sort((a, b) => b.author_en.localeCompare(a.author_en));
            break;
        case 'default':
            tmpSongList = [...songList];
            break;
        case 'default_inverse':
            tmpSongList = [...songList].reverse();
            break;
        case 'ownership':
            tmpSongList.sort((a, b) => {
                const aOwned = userStage.includes(a.id) ? 1 : 0;
                const bOwned = userStage.includes(b.id) ? 1 : 0;
                return bOwned - aOwned;
            });
            break;
    }
    loadList();
}

function showDetailTotal(mode, page) {
    totalMode = mode;
    let songName = "Total Score";
    let buttonLabels = ["All", "Mobile", "Arcade"];
    let buttonModes = [0, 1, 2];

    const postData = {
        mode: mode,
        page: page
    };

    const controller = new AbortController();
    const signal = controller.signal;

    let html = `
        <p>Loading...</p>
        <button id="backButton" class="loading-back-button">
            Back
        </button>
    `;

    document.getElementById('ranking_box').innerHTML = html;

    document.getElementById('backButton').onclick = () => {
        controller.abort();
        restoreBaseStructure();
        loadUI();
        filterList();
        loadList();
    };

    fetch(HOST_URL + 'api/ranking/total?' + PAYLOAD + '&_=' + new Date().getTime(), {
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
                let rankingList = payload.data.ranking_list;
                let playerRanking = payload.data.player_ranking;
                let totalCount = payload.data.total_count;
                
                let pageCount = 50;
                let generatePrevButton = false;
                let generateNextButton = false;

                if (page > 0) {
                    generatePrevButton = true;
                }
                if ((page + 1) * pageCount < totalCount) {
                    generateNextButton = true;
                }

                // Mode boxes

                html = `<div id="ranking_content">
                    <div class="song-name">${songName}</div>
                `;

                rowStart = '<div class="button-row mode-buttons">'
                rowEnd = '</div>'
                rowContent = []

                for (let i = 0; i < buttonLabels.length; i++) {
                    const label = buttonLabels[i];
                    const modeValue = buttonModes[i];

                    if (modeValue === mode) {
                        rowContent.push(`<div class="bt_bg01_ac">${label}</div>`);
                    } else {
                        rowContent.push(
                            `<a onclick="showDetailTotal(${modeValue}, 0);" class="bt_bg01_xnarrow">${label}</a>`
                        );
                    }
                }

                html += rowStart + rowContent.join('') + rowEnd;

                // Player object
                let playerRank = parseInt(playerRanking['position']);
                if (playerRank < 1) {
                    playerRank = 'N/A';
                } else {
                    playerRank = "#" + playerRank;
                }

                html += `
                    <div class="player-element">
                        <span class="rank">You<br>${playerRank}</span>
                        <img src="/files/image/icon/avatar/${playerRanking['avatar']}.png" class="avatar" alt="Player Avatar">
                        <div class="player-info">
                            <div class="name">${playerRanking['username']}</div>
                            <img src="/files/image/title/${playerRanking['title']}.png" class="title" alt="Player Title">
                        </div>
                        <div class="player-score">${playerRanking['score']}</div>
                    </div>
                `;

                // generate pagination buttons
                html += `
                    <div class="pagination-container">
                        ${generatePrevButton ? `
                            <button class="pagination-button prev-button"
                                    onclick="showDetailTotal(${mode}, ${page - 1})">
                                Prev Page
                            </button>
                        ` : '<div class="placeholder"></div>'} <!-- Placeholder for alignment -->

                        <button onclick='restoreBaseStructure();loadUI();filterList();loadList();' class="pagination-button">
                            Back
                        </button>
                        ${generateNextButton ? `
                            <button class="pagination-button next-button"
                                    onclick="showDetailTotal(${mode}, ${page + 1})">
                                Next Page
                            </button>
                        ` : ''}
                    </div>
                `;

                // Loop leaderboard ranks
                html += `<div class="leaderboard-players">`;

                for (let i = 0; i < rankingList.length; i++) {
                    userData = rankingList[i];
                    html += `
                    <div class="leaderboard-player">
                        <div class="rank">#${userData['position']}</div>
                        <img class="avatar" src="/files/image/icon/avatar/${userData['avatar']}.png" alt="Avatar">
                        <div class="leaderboard-info">
                            <div class="name">${userData['username']}</div>
                            <div class="title"><img src="/files/image/title/${userData['title']}.png" alt="Title"></div>
                        </div>
                        <div class="leaderboard-score">${userData['score']}</div>
                    </div>
                    `;

                }

                html += `</div>`;

                document.getElementById('ranking_box').innerHTML = html;

            } else {
                html = `
                    <br>
                    <p>${payload.message}</p>
                    <button onclick='restoreBaseStructure();loadUI();filterList();loadList();' style="margin-top: 20px;" class="bt_bg01">
                        Back
                    </button>
                `;

                document.getElementById('ranking_box').innerHTML = html;
            }
    });
}

function showDetailIndividual(songId, mode, page = 0) {
    individualMode = mode;
    let songMeta = songList.find(song => song.id === songId);
    let songName = songMeta ? songMeta.name_en : "Error - No song name found";
    let songDiff = songMeta ? songMeta.difficulty_levels : [];
    let buttonLabels = [];
    let buttonModes = [];

    if (songId < 615) {
        buttonLabels = ["Easy", "Normal", "Hard"];
        buttonModes = [1, 2, 3];
    } else if (mode < 10) {
        mode += 10;
    }

    if (songDiff.length == 6) {
        buttonLabels.push("AC-Easy", "AC-Normal", "AC-Hard");
        buttonModes.push(11, 12, 13);
    } else if (mode > 10) {
        mode -= 10;
    }

    const postData = {
        song_id: songId,
        mode: mode,
        page: page
    };

    const controller = new AbortController();
    const signal = controller.signal;

    let html = `
        <p>Loading...</p>
        <button id="backButton" class="loading-back-button">
            Back
        </button>
    `;

    document.getElementById('ranking_box').innerHTML = html;

    document.getElementById('backButton').onclick = () => {
        controller.abort();
        restoreBaseStructure();
        loadUI();
        filterList();
        loadList();
    };

    fetch(HOST_URL + 'api/ranking/individual?' + PAYLOAD + '&_=' + new Date().getTime(), {
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
                let rankingList = payload.data.ranking_list;
                let playerRanking = payload.data.player_ranking;
                let totalCount = payload.data.total_count;
                
                let pageCount = 50;
                let generatePrevButton = false;
                let generateNextButton = false;

                if (page > 0) {
                    generatePrevButton = true;
                }

                if ((page + 1) * pageCount < totalCount) {
                    generateNextButton = true;
                }

                // Mode boxes

                html = `<div>${songName}</div>`;

                rowStart = '<div class="button-row">'
                rowEnd = '</div>'
                rowContent = []

                for (let i = 0; i < buttonLabels.length; i++) {
                    if (i == 3) {
                        rowContent.push(rowStart);
                    }
                    const label = buttonLabels[i];
                    const modeValue = buttonModes[i];

                    if (modeValue === mode) {
                        rowContent.push(`<div class="bt_bg01_ac">${label}</div>`);
                    } else {
                        rowContent.push(
                            `<a onclick="showDetailIndividual(${songId}, ${modeValue}, 0);" class="bt_bg01_xnarrow">${label}</a>`
                        );
                    }
                    if (i == 2 && buttonLabels.length > 3) {
                        rowContent.push(rowEnd);
                    }

                }

                html += rowStart + rowContent.join('') + rowEnd;

                // Player object
                let playerRank = parseInt(playerRanking['position']);
                if (playerRank < 1) {
                    playerRank = 'N/A';
                } else {
                    playerRank = "#" + playerRank;
                }

                html += `
                    <div class="player-element">
                        <span class="rank">You<br>${playerRank}</span>
                        <img src="/files/image/icon/avatar/${playerRanking['avatar']}.png" class="avatar" alt="Player Avatar">
                        <div class="player-info">
                            <div class="name">${playerRanking['username']}</div>
                            <img src="/files/image/title/${playerRanking['title']}.png" class="title" alt="Player Title">
                        </div>
                        <div class="player-score">${playerRanking['score']}</div>
                    </div>
                `;

                // generate pagination buttons
                html += `
                    <div class="pagination-container">
                        ${generatePrevButton ? `
                            <button class="pagination-button prev-button"
                                    onclick="showDetailIndividual(${songId}, ${mode}, ${page - 1})">
                                Prev Page
                            </button>
                        ` : '<div class="placeholder"></div>'}

                        <button onclick='restoreBaseStructure();loadUI();filterList();loadList();' class="pagination-button">
                            Back
                        </button>
                        ${generateNextButton ? `
                            <button class="pagination-button next-button"
                                    onclick="showDetailIndividual(${songId}, ${mode}, ${page + 1})">
                                Next Page
                            </button>
                        ` : '<div class="placeholder"></div>'}
                    </div>
                `;

                // Loop leaderboard ranks
                html += `<div class="leaderboard-players">`;

                for (let i = 0; i < rankingList.length; i++) {
                    userData = rankingList[i];
                    html += `
                    <div class="leaderboard-player">
                        <div class="rank">#${userData['position']}</div>
                        <img class="avatar" src="/files/image/icon/avatar/${userData['avatar']}.png" alt="Avatar">
                        <div class="leaderboard-info">
                            <div class="name">${userData['username']}</div>
                            <div class="title"><img src="/files/image/title/${userData['title']}.png" alt="Title"></div>
                        </div>
                        <div class="leaderboard-score">${userData['score']}</div>
                    </div>
                    `;

                }

                html += `</div>`;
                
                document.getElementById('ranking_box').innerHTML = html;

            } else {
                html = `
                    <br>
                    <p>${payload.message}</p>
                    <button onclick='restoreBaseStructure();loadUI();filterList();loadList();' style="margin-top: 20px;" class="bt_bg01">
                        Back
                    </button>
                `;

                document.getElementById('ranking_box').innerHTML = html;
            }
    });
}

function restoreBaseStructure() {
    document.getElementById('ranking_box').innerHTML = `
        <div id="ranking_content" class="d_ib w100">
            <!-- Search Bar -->
            <input 
                type="text" 
                id="ranking_searchbar" 
                placeholder="Search for songs or composers..." 
                style="width: 100%; padding: 10px; font-size: 30px; box-sizing: border-box;"
            />

            <!-- Sort Dropdown -->
            <select 
                id="ranking_sort" 
                style="width: 100%; padding: 10px; font-size: 30px; margin-top: 10px; box-sizing: border-box;"
            >
                <option value="default">Default</option>
                <option value="default_inverse">Default - Inverse</option>
                <option value="name">Sort by Name</option>
                <option value="name_inverse">Sort by Name - Inverse</option>
                <option value="author">Sort by Author</option>
                <option value="author_inverse">Sort by Author - Inverse</option>
                <option value="ownership">Sort by Ownership</option>
            </select>
        <ul class='song-list' id="song_list">
            Loading...
        </ul>
    </div>
    `;
}

window.onload = function(){
    restoreBaseStructure();
    on_initialize();
};