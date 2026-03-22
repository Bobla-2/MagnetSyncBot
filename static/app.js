
    let currentInfoNum = null;
    let currentDefaultJlName = "";
    let deleteNum = null;
    let deleteName = "";
    let currentMobilePanel = "results";

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
            return;
        }

        root.innerHTML = items.map(item => `
            <div class="result-item">
                <div class="result-title">${escapeHtml(item.num)}) ${escapeHtml(item.name)}</div>
                <div class="result-meta">Размер: ${escapeHtml(item.size)}<br>Категория: ${escapeHtml(item.category)}</div>
                <div class="result-actions">
                    <button onclick="showInfo(${item.num})">Показать доп. инфу</button>
                    <button onclick="startDownload(${item.num}, false)">Скачать</button>
                    <button onclick="startDownload(${item.num}, true)">Скачать + symlink</button>
                </div>
            </div>
        `).join("");
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
}



    async function deleteDownload(num) {
    const ok = confirm(`Удалить закачку ${num}?`);
    if (!ok) {
        return;
    }

    setStatus("Удаление закачки...");

    try {
        await api("/api/download/delete", {
            method: "POST",
            body: JSON.stringify({
                num: num,
            }),
        });

        setStatus("Закачка удалена");
        await loadDownloads();
    } catch (e) {
        setStatus(e.message);
    }
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

    function showMobilePanel(name) {
        const panelResults = document.getElementById("panelResults");
        const panelDownloads = document.getElementById("panelDownloads");
        const tabResults = document.getElementById("tabResults");
        const tabDownloads = document.getElementById("tabDownloads");
        currentMobilePanel = name;

        if (!isMobileView()) {
            panelResults.classList.remove("hidden-mobile");
            panelDownloads.classList.remove("hidden-mobile");
            tabResults.classList.remove("active");
            tabDownloads.classList.remove("active");
            return;
        }


        if (name === "downloads") {
            panelResults.classList.add("hidden-mobile");
            panelDownloads.classList.remove("hidden-mobile");
            tabResults.classList.remove("active");
            tabDownloads.classList.add("active");
        } else {
            panelResults.classList.remove("hidden-mobile");
            panelDownloads.classList.add("hidden-mobile");
            tabResults.classList.add("active");
            tabDownloads.classList.remove("active");
        }
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
        showMobilePanel(currentMobilePanel);
    });

    document.getElementById("btnSearch").addEventListener("click", searchTorrents);
    document.getElementById("btnLastError").addEventListener("click", loadLastError);

    document.getElementById("searchQuery").addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            searchTorrents();
        }
    });

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



    showMobilePanel("results");

    loadDownloads();
    loadLastSearchResults();
    setInterval(loadDownloads, 3000);
