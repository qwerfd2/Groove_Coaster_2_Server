let userCoin = 0;
let stageList = [];
let avatarList = [];
let itemList = [];
let fmaxPurchased = false;
let extraPurchased = false;

let shopMode = 0; // 0: Stages, 1: Avatars, 2: Items
let stagePage = 0;
let avatarPage = 0;
let pageItemCount = 40;

on_initialize = () => {
    fetch(HOST_URL + 'api/shop/player_data?' + PAYLOAD + '&_=' + new Date().getTime())
        .then(response => response.json())
        .then(data => {
            if (data.state) {
                userCoin = data.data.coin;
                stageList = data.data.stage_list;
                avatarList = data.data.avatar_list;
                itemList = data.data.item_list;
                fmaxPurchased = data.data.fmax_purchased;
                extraPurchased = data.data.extra_purchased;
                loadUI();
            } else {
                document.getElementById('content').innerText = data.message;
                document.getElementById('coinCounter').innerText = 'Error';
            }
        });
};

function loadUI() {
    document.getElementById('ttl').src = "/files/web/ttl_shop.png";
    document.getElementById('ttl').alt = "SHOP";
    document.getElementById('coinCounter').innerText = userCoin;
    document.getElementById('menuList').innerHTML = generateMenuList();
    document.getElementById('content').innerHTML = generateMenuContent();
}

function generateMenuList() {
    const options = {
        0: [
            { cnt_type: 1, label: "Avatar" },
            { cnt_type: 2, label: "Item" }
        ],
        1: [
            { cnt_type: 0, label: "Tracks" },
            { cnt_type: 2, label: "Item" }
        ],
        2: [
            { cnt_type: 0, label: "Tracks" },
            { cnt_type: 1, label: "Avatar" }
        ]
    };

    const modeOptions = options[shopMode] || [];

    return modeOptions.map(option => `
        <li style="display: inline-block; margin: 0 30px;">
            <a onclick="changeShopMode(${option.cnt_type})" class="bt_bg01_narrow">${option.label}</a>
        </li>
    `).join('');
}

function generateMenuContent() {
    useList = [];
    prefix = "";
    suffix = "";
    if (shopMode === 0) {
        useList = stageList;
        prefix = "shop";
        suffix = "jpg";
    } else if (shopMode === 1) {
        useList = avatarList;
        prefix = "avatar";
        suffix = "png";
    } else if (shopMode === 2) {
        useList = itemList;
        prefix = "item";
        suffix = "png";
    }
    
    html = '';

    generatePrevButton = false;
    generateNextButton = false;

    if (shopMode !== 2) {
        const currentPage = shopMode === 0 ? stagePage : avatarPage;
        useList = useList.slice(currentPage * pageItemCount, currentPage * pageItemCount + pageItemCount);

        if (currentPage > 0) {
            generatePrevButton = true;
        }
        if ((currentPage + 1) * pageItemCount < (shopMode === 0 ? stageList.length : avatarList.length)) {
            generateNextButton = true;
        }

    }

    if (shopMode === 0 && stagePage === 0) {
        html += `
        <a onclick="showFMax()">
            <img src="/files/web/dlc_4max.jpg" style="width: 90%; margin-bottom: 110px; margin-top: -80px;" />
        </a><br>
        <a onclick="showExtra()">
            <img src="/files/web/dlc_extra.jpg" style="width: 90%; margin-bottom: 20px; margin-top: -80px;" />
        </a><br>
        `;
    }

    if (generatePrevButton) {
        html += `
            <button class="pagination-button-shop"
                    onclick="prevPage(${shopMode})">
                Prev Page
            </button>
        `;
    }

    if (generateNextButton) {
        html += `
            <button class="pagination-button-shop"
                    onclick="nextPage(${shopMode})">
                Next Page
            </button>
        `;
    }

    if (generatePrevButton || generateNextButton) {
        html += '<br>';
    }

    useList.forEach((item, index) => {
        html += `
            <button style="width: 170px; height: 170px; margin: 10px; background-color: black; background-size: contain; background-repeat: no-repeat; background-position: center center;background-image: url('/files/image/icon/${prefix}/${item}.${suffix}');"
                    onclick="showItemDetail(${shopMode}, ${item})">
            </button>
        `
        if ((index + 1) % 4 === 0) {
            html += '<br>';
        }
    });

    if (generatePrevButton) {
        html += `
            <button class="pagination-button-shop"
                    onclick="prevPage(${shopMode})">
                Prev Page
            </button>
        `;
    }

    if (generateNextButton) {
        html += `
            <button class="pagination-button-shop"
                    onclick="nextPage(${shopMode})">
                Next Page
            </button>
        `;
    }

    return html;
}

function prevPage(mode) {
    if (mode === 0 && stagePage > 0) {
        stagePage--;
    } else if (mode === 1 && avatarPage > 0) {
        avatarPage--;
    }
    document.getElementById('content').innerHTML = generateMenuContent();
}

function nextPage(mode) {
    if (mode === 0 && (stagePage + 1) * pageItemCount < stageList.length) {
        stagePage++;
    } else if (mode === 1 && (avatarPage + 1) * pageItemCount < avatarList.length) {
        avatarPage++;
    }
    document.getElementById('content').innerHTML = generateMenuContent();
}

function changeShopMode(mode) {
    shopMode = mode;
    document.getElementById('menuList').innerHTML = generateMenuList();
    document.getElementById('content').innerHTML = generateMenuContent();
}

function showItemDetail(mode, itemId) {
    document.getElementById('menuList').innerHTML = '';

    document.getElementById('ttl').src = "/files/web/ttl_buy.png";
    document.getElementById('ttl').alt = "BUY";

    const postData = {
        mode: mode,
        item_id: itemId
    };

    const controller = new AbortController();
    const signal = controller.signal;

    document.getElementById('content').innerHTML = `
        <p>Loading...</p>
        <button id="backButton" style="margin-top: 20px;" class="bt_bg01">
            Back
        </button>
    `;

    document.getElementById('backButton').onclick = () => {
        controller.abort();
        loadUI();
    };

    fetch(HOST_URL + 'api/shop/item_data?' + PAYLOAD, {
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
                let html = '';
                if (mode === 0) {
                    // Song purchase
                    html = `
                        <div class="image-container">
                            <img src="/files/image/icon/shop/${itemId}.jpg" alt="Item Image" style="width: 180px; height: 180px;" />
                        </div>
                        <p class="f80">Would you like to purchase this song?</p>
                        <div>
                            <p class="f80">${payload.data.property_first} - ${payload.data.property_second}</p>
                            <p class="f80">Difficulty Levels: ${payload.data.property_third}</p>
                        </div>
                        <div>
                            <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                            <span style="color: #FFFFFF; font-size: 44px; font-family: Hiragino Kaku Gothic ProN, sans-serif;">${payload.data.price}</span>
                        </div>
                    `;
                } else if (mode === 1) {
                    // Avatar purchase
                    html = `
                        <div class="image-container">
                            <img src="/files/image/icon/avatar/${itemId}.png" alt="Item Image" style="width: 180px; height: 180px; background-color: black; object-fit: contain;" />
                        </div>
                        <p class="f80">Would you like to purchase this avatar?</p>
                        <div>
                            <p class="f80">${payload.data.property_first}</p>
                            <p class="f80">Effect: ${payload.data.property_second}</p>
                        </div>
                        <div>
                            <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                            <span>${payload.data.price}</span>
                        </div>
                    `;
                } else if (mode === 2) {
                    // Item purchase
                    html = `
                        <div class="image-container">
                            <img src="/files/image/icon/item/${itemId}.png" alt="Item Image" style="width: 180px; height: 180px;" />
                        </div>
                        <p class="f80">Would you like to purchase this item?</p>
                        <div>
                            <p class="f80">${payload.data.property_first}</p>
                            <p class="f80">Effect: ${payload.data.property_second}</p>
                        </div>
                        <div>
                            <img src="/files/web/coin_icon.png" class="coin-icon" style="width: 40px; height: 40px;" alt="Coin Icon" />
                            <span>${payload.data.price}</span>
                        </div>
                    `;
                }

                // Add purchase and back buttons
                html += `
                    <div style="margin-top: 20px;">
                        <a onclick="purchaseItem(${mode}, ${itemId})" class="bt_bg01">Buy</a><br>
                        <a class="bt_bg01" onclick="loadUI();">Go Back</a>
                    </div>
                `;

                document.getElementById('content').innerHTML = html;
            } else {
                document.getElementById('content').innerHTML = `
                    <p>Error: ${payload.message}</p>
                    <div style="margin-top: 20px;">
                        <a class="bt_bg01" onclick="loadUI();">Go Back</a>
                    </div>
                `;
            }
        })
        .catch(error => {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted');
            } else {
                console.error('Error fetching item details:', error);
                document.getElementById('content').innerHTML = '<p>Failed to load item details. Please try again later.</p>';
            }
        });
}

function purchaseItem(mode, itemId) {
    restoreBaseStructure();
    const contentElement = document.getElementById('content');
    document.getElementById('ttl').src = "/files/web/ttl_buy.png";
    document.getElementById('ttl').alt = "BUY";
    contentElement.innerHTML = `
        <p>Processing your purchase...</p>
    `;

    const postData = {
        mode: mode,
        item_id: itemId
    };

    fetch(HOST_URL + 'api/shop/purchase_item?' + PAYLOAD, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData)
    })
        .then(response => response.json())
        .then(payload => {
            if (payload.state === 1) {
                contentElement.innerHTML = `
                    <p>${payload.message}</p>
                    <div style="margin-top: 20px;">
                        <a onclick="on_initialize();" class="bt_bg01">Back</a><br>
                    </div>
                `;
                document.getElementById('coinCounter').innerText = payload.data.coin;
            } else {
                contentElement.innerHTML = `
                    <p>Purchase failed: ${payload.message}</p>
                    <div style="margin-top: 20px;">
                        <a onclick="on_initialize();" class="bt_bg01">Back</a><br>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error processing purchase:', error);
            contentElement.innerHTML = `
                <p>Failed to process your purchase. Please try again later.</p>
                <div style="margin-top: 20px;">
                    <a onclick="on_initialize();" class="bt_bg01">Back</a><br>
                </div>
            `;
        });
}

function restoreBaseStructure() {
    document.body.className = "";
    document.body.style.backgroundColor = "black";
    document.body.style.backgroundImage = "";
    document.body.innerHTML = `
    <body>
        <div id="header">
          <div style="position: fixed; top: 20px; left: 10px; display: flex; align-items: center; ">
            <img src="/files/web/coin_icon.png" alt="Coins" style="width: 40px; height: 40px; margin-right: 10px;">
            <span style="color: #FFFFFF; font-size: 24px; font-family: Hiragino Kaku Gothic ProN, sans-serif;" id="coinCounter">Loading</span>
          </div>
          <img class="ttl_height" id="ttl" src="/files/web/ttl_shop.png" alt="SHOP" />
        </div>
        <div id="wrapper">
            <div class="wrapper_box">
                <div class="a_left w100 d_ib mb10p">
                        <ul style="list-style-type: none; padding: 0; margin-top: 60px; text-align: center;" id="menuList">
                        </ul>
                    <div class="f90 a_center pt50" id="content">
                        Loading...
                    </div>
                </div>
            </div>
        </div>
    </body>
    `
}

function showFMax() {
    let htmlText = "Loading...";

    document.body.className = "dlc_body";
    document.body.style.backgroundColor = "black"; 
    document.body.innerHTML = `
        <div class="dlc_container">
            <img src="/files/web/gc4ex-logo.png" alt="GC4EX Logo" class="dlc_logo" 
                 onload="document.body.style.backgroundImage = 'url(/files/web/gc4ex_bg.jpg)';" 
                 onerror="this.style.display='none';" />
            <p style="color: white; font-size: 20px; text-align: center;">${htmlText}</p>
            <button id="backButton" class="quit-button">
                Go Back
            </button>
        </div>
    `;

    const controller = new AbortController();
    const signal = controller.signal;

    document.getElementById('backButton').onclick = () => {
        controller.abort();
        restoreBaseStructure();
        loadUI();
    };

    const postData = {
        mode: 3,
        item_id: 1
    };

    fetch(HOST_URL + 'api/shop/item_data?' + PAYLOAD, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData),
        signal: signal // Pass the abort signal
    })
        .then(response => response.json())
        .then(payload => {
            if (payload.state == 1) {
                let html = '';
                if (fmaxPurchased) {
                    html = `
                        <div class="text-content">
                            <p>You have unlocked the GC4MAX expansion!</p>
                            <p>Please report bugs/missing tracks to Discord: #AnTcfgss, or QQ 3421587952.</p>
                            <button class="quit-button" onclick="restoreBaseStructure(); loadUI();">
                                Go Back
                            </button><br><br>
                            <strong>This server has version ${payload.data.property_first}.</strong>
                            <p>Update log: </p>
                            <p>${payload.data.property_second}</p><br>
                        </div>
                    `;
                } else {
                    html = `
                        <div class="text-content">
                            <p>Experience the arcade with the GC4MAX expansion! This DLC unlocks 320+ exclusive songs for your 2OS experience.</p>
                            <p>Note that these songs don't have mobile difficulties. A short placeholder is used, and GCoin reward is not available for playing them. You must clear the Normal difficulty to unlock AC content.</p>
                            <p>After purchasing, you will have access to support information and update logs.</p>
                        </div>
                        <button class="buy-button" onclick="purchaseItem(3, 1);">
                            Buy
                            <div class="coin-container">
                                <img src="/files/web/coin_icon.png" alt="Coin Icon" class="coin-icon">
                                <span class="coin-price">${payload.data.price}</span>
                            </div>
                        </button>
                        <br><br>
                        <button class="quit-button" onclick="restoreBaseStructure(); loadUI();">
                            Go Back
                        </button>
                    `;
                }

                // Update the body content with the new HTML
                document.body.innerHTML = `
                    <div class="dlc_container">
                        <img src="/files/web/gc4ex-logo.png" alt="GC4EX Logo" class="dlc_logo">
                        ${html}
                    </div>
                `;
            } else {
                document.body.innerHTML = `
                    <div class="dlc_container">
                        <img src="/files/web/gc4ex-logo.png" alt="GC4EX Logo" class="dlc_logo">
                        <p style="color: white; font-size: 20px; text-align: center;">Error: ${payload.message}</p>
                        <button class="quit-button" onclick="restoreBaseStructure(); loadUI();">
                            Go Back
                        </button>
                    </div>
                `;
            }
        })
        .catch(error => {
            document.body.innerHTML = `
                <div class="dlc_container">
                    <img src="/files/web/gc4ex-logo.png" alt="GC4EX Logo" class="dlc_logo">
                    <p style="color: white; font-size: 20px; text-align: center;">Failed to load item details. Please try again later.</p>
                    <button class="quit-button" onclick="restoreBaseStructure(); loadUI();">
                        Go Back
                    </button>
                </div>
            `;
        });
}

function showExtra() {
    let htmlText = "Loading...";

    document.body.className = "dlc_body";
    document.body.style.backgroundColor = "black";
    document.body.style.backgroundImage = 'url(/files/web/extra_bg.jpg)';
    document.body.innerHTML = `
        <div class="dlc_container_extra">
            ${htmlText}
            <button id="backButton" class="quit-button-extra">
                Go Back
            </button>
        </div>
    `;

    const controller = new AbortController();
    const signal = controller.signal;

    document.getElementById('backButton').onclick = () => {
        controller.abort();
        restoreBaseStructure();
        loadUI();
    };

    const postData = {
        mode: 4,
        item_id: 1
    };

    fetch(HOST_URL + 'api/shop/item_data?' + PAYLOAD, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(postData),
        signal: signal
    })
        .then(response => response.json())
        .then(payload => {
            if (payload.state === 1) {
                let html = '';
                if (extraPurchased) {
                    html = `
                        <br><br><br><br><br><br><br><br><br>
                        <div class="text-content">
                            <p>You have unlocked the EXTRA Challenge!</p>
                            <p>Please report bugs/missing tracks to Discord: #AnTcfgss, or QQ 3421587952.</p>
                            <button class="quit-button-extra" onclick="restoreBaseStructure(); loadUI();">
                                Go Back
                            </button>
                        </div>
                    `;
                } else {
                    html = `
                        <div style="margin-top: 30vh;"></div>
                        <div class="text-content">
                            <p>Are you looking for a bad time?</p>
                            <p>If so, this is the Ultimate - Extra - Challenge.</p>
                            <p>180+ Arcade Extra difficulty charts await you.</p>
                            <p>You have been warned.</p>
                        </div>

                        <button class="buy-button-extra" onclick="purchaseItem(4, 1);">
                            Buy
                            <div class="coin-container">
                            <img src="/files/web/coin_icon.png" alt="Coin Icon" class="coin-icon">
                            <span class="coin-price">${payload.data.price}</span>
                            </div>
                        </button>
                        <br><br>
                        <button class="quit-button-extra" onclick="restoreBaseStructure(); loadUI();">
                            Go Back
                        </button>
                    `;
                }


                document.body.innerHTML = `
                    <div class="dlc_container">
                        ${html}
                    </div>
                `;;
            } else {
                document.body.innerHTML = `
                    <div class="dlc_container">
                        <p style="color: white; font-size: 20px; text-align: center;">Error: ${payload.message}</p>
                        <button class="quit-button-extra" onclick="restoreBaseStructure(); loadUI();">
                            Go Back
                        </button>
                    </div>
                `;
            }
        })
        .catch(error => {
            document.body.innerHTML = `
                <div class="dlc_container">
                    <p style="color: white; font-size: 20px; text-align: center;">Failed to load item details. Please try again later.</p>
                    <button class="quit-button-extra" onclick="restoreBaseStructure(); loadUI();">
                        Go Back
                    </button>
                </div>
            `;
        });
}

window.onload = function(){
    restoreBaseStructure();
    on_initialize();
};