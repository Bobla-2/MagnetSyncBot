
    let currentInfoNum = null;
    let currentDefaultJlName = "";
    let deleteNum = null;
    let deleteName = "";
    let currentMobilePanel = "results";
    let lastIsMobileView = window.innerWidth <= 900;

    function setStatus(text) {
        document.getElementById("statusBar").textContent = text || "";
    }

   function enableOutsideClickClose(dialog) {
    dialog.addEventListener("click", function (e) {
        const rect = dialog.getBoundingClientRect();

        const isInDialog =
            e.clientX >= rect.left &&
            e.clientX <= rect.right &&
            e.clientY >= rect.top &&
            e.clientY <= rect.bottom;

        if (!isInDialog) {
            dialog.close();
        }
    });
}

    async function api(url, options = {}) {
        const response = await fetch(url, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });

        let data = {};
        try {
            data = await response.json();
        } catch (e) {
            throw new Error("Некорректный ответ сервера");
        }

        if (!response.ok || !data.ok) {
            throw new Error(data.error || "Ошибка запроса");
        }

        return data;
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function renderResults(items) {
        const root = document.getElementById("results");

        if (!items.length) {
            root.innerHTML = '<div class="muted">Ничего не найдено</div>';
            updateMobilePanelsHeight();
            return;
        }

        root.innerHTML = items.map(item => `
            <div class="result-item">
                <div class="result-title">
                    ${escapeHtml(item.num)}) ${escapeHtml(item.name)}
                </div>
                <div class="result-bottom">
                    <div class="result-meta">Размер: ${escapeHtml(item.size)}<br>Категория: ${escapeHtml(item.category)}</div>
                    <div class="result-actions">
                        <button onclick="showInfo(${item.num})">🔍</button>
                        <button onclick="startDownload(${item.num}, false)">⬇️</button>
                        <button onclick="startDownload(${item.num}, true)">⬇️🔗</button>
                    </div>
                </div>
            </div>
        `).join("");
        updateMobilePanelsHeight();
    }

    function renderDownloads(items) {
        const root = document.getElementById("downloads");
        document.getElementById("downloadsInfo").textContent = `Активные: ${items.length}`;

        if (!items.length) {
            root.innerHTML = '<div class="muted">Нет активных торрентов</div>';
            return;
    }

    root.innerHTML = items.map(item => `
        <div class="download-item">
            <div class="download-title">${escapeHtml(item.num)}) ${escapeHtml(item.name)}</div>
            <div class="download-row">
                <div class="download-meta">Статус: ${escapeHtml(item.status)}<br>Прогресс: ${escapeHtml(item.progress)}</div>
                <div class="download-actions">
                    <button onclick='openDeleteDialog(${item.num}, ${JSON.stringify(item.name)})'>Удалить</button>
                </div>
            </div>
        </div>
    `).join("");
    updateMobilePanelsHeight();
}


    async function searchTorrents() {
        const query = document.getElementById("searchQuery").value.trim();
        const tracker = document.getElementById("trackerType").value;

        if (!query) {
            document.getElementById("searchInfo").textContent = `Пустой запрос`;
//            setStatus("Пустой запрос");
            return;
        }
        document.getElementById("searchInfo").textContent = `Поиск...`;
//        setStatus("Поиск...");

        try {
            const data = await api("/api/search", {
                method: "POST",
                body: JSON.stringify({
                    query: query,
                    tracker: tracker,
                }),
            });

            currentDefaultJlName = data.default_name_jellyfin || "";
            updateJlButton()
            document.getElementById("searchInfo").textContent = `Найдено: ${data.count}`;
            renderResults(data.items);
//            setStatus("Поиск завершён");
        } catch (e) {

            setStatus(e.message);
        }
    }

    async function showInfo(num) {
    setStatus("Загрузка информации...");

    try {
        const data = await api(`/api/torrent/${num}/info`);
        currentInfoNum = num;
        currentDefaultJlName = data.default_name_jellyfin || currentDefaultJlName || "";
        updateJlButton()
        const infoName = document.getElementById("infoName");
        const infoText = document.getElementById("infoText");
        const infoLinkWrap = document.getElementById("infoLinkWrap");

        infoName.textContent = data.name || "";
        infoText.textContent = data.info || "";
        infoLinkWrap.innerHTML = "";

        if (data.url) {
            const a = document.createElement("a");
            a.href = data.url;
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            a.textContent = "Открыть страницу";
            a.className = "link-btn";
            infoLinkWrap.appendChild(a);
        }

        document.getElementById("infoDialog").showModal();
        setStatus("");
    } catch (e) {
        setStatus(e.message);
    }
}

    async function startDownload(num, withAction) {
        let namePath = null;

        if (withAction) {
            const preset = currentDefaultJlName || "";
            const entered = prompt("Имя/путь для доп. действия:", preset);

            if (entered === null) {
                return;
            }

            namePath = entered.trim() || null;
        }

        setStatus("Запуск скачивания...");

        try {
            await api("/api/download", {
                method: "POST",
                body: JSON.stringify({
                    num: num,
                    mode: withAction ? "jl" : "normal",
                    name_path: namePath,
                }),
            });

            setStatus("Скачивание запущено");
            await loadDownloads();
        } catch (e) {
            openFatalErrorDialog(e.message)
            setStatus(e.message);
        }
    }

    async function loadDownloads() {
        try {
            const data = await api("/api/downloads");
            renderDownloads(data.items);
        } catch (e) {
            setStatus(e.message);
        }
    }

    async function loadLastError() {
        try {
            const data = await api("/api/last_error");

            const dialog = document.getElementById("errorDialog");
            const text = document.getElementById("errorText");

            text.textContent = data.error || "Ошибок нет";

            dialog.showModal();
        } catch (e) {
            setStatus(e.message);
        }
    }

    async function openFatalErrorDialog(text_error) {
        try {

            const dialog = document.getElementById("errorDialog");
            const text = document.getElementById("errorText");

            text.textContent = text_error || "Ошибок нет";

            dialog.showModal();
        } catch (e) {
            setStatus(e.message);
        }
    }

    const infoDialog = document.getElementById("infoDialog");
    const errorDialog = document.getElementById("errorDialog");
    const deleteDialog = document.getElementById("deleteDialog");

    if (infoDialog) enableOutsideClickClose(infoDialog);
    if (errorDialog) enableOutsideClickClose(errorDialog);
    if (deleteDialog) enableOutsideClickClose(deleteDialog);

    function openDeleteDialog(num, name) {
        deleteNum = num;
        deleteName = name;

        const text = document.getElementById("deleteText");
        text.textContent = `Удалить закачку:\n${name}?`;

        document.getElementById("deleteDialog").showModal();
    }

    async function deleteDownloadConfirmed() {
        if (deleteNum === null) {
            return;
        }

        setStatus("Удаление закачки...");

        try {
            await api("/api/download/delete", {
                method: "POST",
                body: JSON.stringify({
                    num: deleteNum,
                }),
            });

            setStatus("Закачка удалена");
            document.getElementById("deleteDialog").close();

            await loadDownloads();
        } catch (e) {
            openFatalErrorDialog(e.message)
            setStatus(e.message);
        }
    }

    async function loadLastSearchResults() {
        try {
            const data = await api("/api/search/last");
            currentDefaultJlName = data.default_name_jellyfin || "";
            updateJlButton()
            document.getElementById("searchInfo").textContent = `Найдено: ${data.count}`;
            if (data.query) {
                document.getElementById("searchQuery").value = data.query;
            }
            renderResults(data.items || []);
        } catch (e) {
            setStatus(e.message);
        }
    }

   function updateJlButton() {
    const btn = document.getElementById("btnUseJl");

    if (!btn) return;

    if (currentDefaultJlName) {
        btn.textContent = window.innerWidth <= 900 ? `Подск.: ${currentDefaultJlName}` : `Подсказка: ${currentDefaultJlName}`;
        btn.disabled = false;
    } else {
        btn.textContent = "Подсказка";
        btn.disabled = true;
    }
}

    document.getElementById("btnUseJl").addEventListener("click", function () {
    if (!currentDefaultJlName) {
        return;
    }

    const input = document.getElementById("searchQuery");
    input.value = currentDefaultJlName;

    searchTorrents();  // сразу поиск
});



    function isMobileView() {
        return window.innerWidth <= 900;
    }

    function setPanelState(panel, state) {
    panel.classList.remove(
        "panel-mobile-active",
        "panel-mobile-left",
        "panel-mobile-right"
    );
    panel.classList.add(state);
}

function updateMobilePanelsHeight() {
    if (!isMobileView()) {
        const wrap = document.querySelector(".mobile-panels");
        if (wrap) {
            wrap.style.height = "";
        }
        return;
    }

    const wrap = document.querySelector(".mobile-panels");
    const activePanel = document.querySelector(".panel-mobile-active");

    if (wrap && activePanel) {
        wrap.style.height = activePanel.offsetHeight + "px";
    }
    }

    function showMobilePanel(name) {
        const panelResults = document.getElementById("panelResults");
        const panelDownloads = document.getElementById("panelDownloads");
        const tabResults = document.getElementById("tabResults");
        const tabDownloads = document.getElementById("tabDownloads");

        if (!panelResults || !panelDownloads || !tabResults || !tabDownloads) {
            return;
        }

        currentMobilePanel = name;

        if (!isMobileView()) {
            panelResults.classList.remove(
                "panel-mobile-active",
                "panel-mobile-left",
                "panel-mobile-right"
            );
            panelDownloads.classList.remove(
                "panel-mobile-active",
                "panel-mobile-left",
                "panel-mobile-right"
            );

            tabResults.classList.remove("active");
            tabDownloads.classList.remove("active");

            updateMobilePanelsHeight();
            return;
        }

        if (name === "downloads") {
            setPanelState(panelResults, "panel-mobile-left");
            setPanelState(panelDownloads, "panel-mobile-active");
            tabResults.classList.remove("active");
            tabDownloads.classList.add("active");
        } else {
            setPanelState(panelResults, "panel-mobile-active");
            setPanelState(panelDownloads, "panel-mobile-right");
            tabResults.classList.add("active");
            tabDownloads.classList.remove("active");
        }

        setTimeout(updateMobilePanelsHeight, 260);
    }

   function enableSwipeSwitch() {
    const area = document.querySelector(".mobile-panels");
    if (!area) {
        return;
    }

    let touchStartX = 0;
    let touchStartY = 0;

    area.addEventListener("touchstart", function (e) {
        if (!isMobileView()) {
            return;
        }

        const t = e.changedTouches[0];
        touchStartX = t.clientX;
        touchStartY = t.clientY;
    }, { passive: true });

    area.addEventListener("touchend", function (e) {
        if (!isMobileView()) {
            return;
        }

        const t = e.changedTouches[0];
        const touchEndX = t.clientX;
        const touchEndY = t.clientY;

        const dx = touchEndX - touchStartX;
        const dy = touchEndY - touchStartY;

        const absDx = Math.abs(dx);
        const absDy = Math.abs(dy);

        if (absDx < 50 || absDx < absDy) {
            return;
        }

        if (dx < 0 && currentMobilePanel !== "downloads") {
            showMobilePanel("downloads");
        } else if (dx > 0 && currentMobilePanel !== "results") {
            showMobilePanel("results");
        }
    }, { passive: true });
}


//   авто скрытие клавиатуры
   document.getElementById("searchQuery").addEventListener("keyup", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            this.blur();
            searchTorrents();
        }
    });

    document.getElementById("tabResults").addEventListener("click", function () {
        showMobilePanel("results");
    });

    document.getElementById("tabDownloads").addEventListener("click", function () {
        showMobilePanel("downloads");
    });

      window.addEventListener("resize", function () {
        const nowIsMobileView = isMobileView();

        if (nowIsMobileView !== lastIsMobileView) {
            showMobilePanel(currentMobilePanel);
            lastIsMobileView = nowIsMobileView;
        }

        updateJlButton();
        updateMobilePanelsHeight();
    });

    document.getElementById("btnSearch").addEventListener("click", searchTorrents);
    document.getElementById("btnLastError").addEventListener("click", loadLastError);

//    document.getElementById("searchQuery").addEventListener("keydown", function (e) {
//        if (e.key === "Enter") {
//            searchTorrents();
//        }
//    });

    document.getElementById("dialogClose").addEventListener("click", function () {
        document.getElementById("infoDialog").close();
    });

    document.getElementById("errorClose").addEventListener("click", function () {
        document.getElementById("errorDialog").close();
    });

    document.getElementById("dialogDownload").addEventListener("click", async function () {
        if (currentInfoNum !== null) {
            await startDownload(currentInfoNum, false);
        }
    });

    document.getElementById("dialogDownloadJl").addEventListener("click", async function () {
        if (currentInfoNum !== null) {
            await startDownload(currentInfoNum, true);
        }
    });
    document.getElementById("deleteConfirm").addEventListener("click", deleteDownloadConfirmed);

    document.getElementById("deleteCancel").addEventListener("click", function () {
        document.getElementById("deleteDialog").close();
    });


    showMobilePanel("results")
    enableSwipeSwitch()
    updateMobilePanelsHeight();

    loadDownloads();
    loadLastSearchResults();
    setInterval(loadDownloads, 3000);
