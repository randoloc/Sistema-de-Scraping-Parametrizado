import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    id: window
    visible: true
    width: 960
    height: 680
    minimumWidth: 720
    minimumHeight: 520
    title: "ScrapperGenérico — Admin"

    Material.theme: Material.Light
    Material.accent: Material.Blue

    property string currentView: "dashboard"
    property bool loading: false

    // Colores
    readonly property color bgPrimary: "#ffffff"
    readonly property color bgSecondary: "#f8fafc"
    readonly property color textPrimary: "#1a1a2e"
    readonly property color textSecondary: "#64748b"
    readonly property color accent: "#2563eb"
    readonly property color success: "#22c55e"
    readonly property color error: "#ef4444"

    // Función helper para parsear JSON
    function parseJson(str) {
        try { return JSON.parse(str); }
        catch(e) { return null; }
    }

    header: ToolBar {
        padding: 8
        background: Rectangle {
            color: "#1a1a2e"
        }
        RowLayout {
            anchors.fill: parent
            spacing: 8

            Label {
                text: "ScrapperGenérico"
                color: "white"
                font.pixelSize: 16
                font.weight: Font.Bold
                Layout.leftMargin: 8
            }

            Item { Layout.fillWidth: true }

            ToolButton {
                text: "Dashboard"
                highlighted: currentView === "dashboard"
                onClicked: currentView = "dashboard"
                contentItem: Text {
                    text: parent.text
                    color: currentView === "dashboard" ? accent : "white"
                    font.pixelSize: 13
                }
            }
            ToolButton {
                text: "Búsqueda"
                highlighted: currentView === "search"
                onClicked: { currentView = "search"; loadSearchVerticales(); }
                contentItem: Text {
                    text: parent.text
                    color: currentView === "search" ? accent : "white"
                    font.pixelSize: 13
                }
            }
            ToolButton {
                text: "Nuevo Scraper"
                highlighted: currentView === "scrape"
                onClicked: currentView = "scrape"
                contentItem: Text {
                    text: parent.text
                    color: currentView === "scrape" ? accent : "white"
                    font.pixelSize: 13
                }
            }
            ToolButton {
                text: "Resultados"
                highlighted: currentView === "results"
                onClicked: { currentView = "results"; loadResults(); }
                contentItem: Text {
                    text: parent.text
                    color: currentView === "results" ? accent : "white"
                    font.pixelSize: 13
                }
            }
            ToolButton {
                text: "Entregas"
                highlighted: currentView === "delivery"
                onClicked: { currentView = "delivery"; loadDeliveryOps(); }
                contentItem: Text {
                    text: parent.text
                    color: currentView === "delivery" ? accent : "white"
                    font.pixelSize: 13
                }
            }
            ToolButton {
                text: "Historial"
                highlighted: currentView === "history"
                onClicked: { currentView = "history"; loadHistory(); }
                contentItem: Text {
                    text: parent.text
                    color: currentView === "history" ? accent : "white"
                    font.pixelSize: 13
                }
            }
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: {
            if (currentView === "dashboard") return 0;
            if (currentView === "search") return 1;
            if (currentView === "scrape") return 2;
            if (currentView === "results") return 3;
            if (currentView === "delivery") return 4;
            if (currentView === "history") return 5;
            return 0;
        }

        // ======== Página 0: Dashboard ========
        Rectangle {
            color: bgSecondary
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Label {
                    text: "Dashboard"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: textPrimary
                }

                // Stats
                RowLayout {
                    spacing: 16
                    Layout.fillWidth: true

                    Rectangle {
                        Layout.fillWidth: true
                        height: 100
                        radius: 12
                        color: bgPrimary
                        border.color: "#e2e8f0"

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4
                            Label {
                                id: totalOpsLabel
                                text: "..."
                                font.pixelSize: 28
                                font.weight: Font.Bold
                                color: accent
                                Layout.alignment: Qt.AlignHCenter
                            }
                            Label {
                                text: "Operaciones"
                                font.pixelSize: 12
                                color: textSecondary
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 100
                        radius: 12
                        color: bgPrimary
                        border.color: "#e2e8f0"

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4
                            Label {
                                id: serviceLabel
                                text: "..."
                                font.pixelSize: 28
                                font.weight: Font.Bold
                                color: success
                                Layout.alignment: Qt.AlignHCenter
                            }
                            Label {
                                text: "Servicio"
                                font.pixelSize: 12
                                color: textSecondary
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }
                }

                Pane {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    padding: 16
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12

                        Label {
                            text: "Operaciones Recientes"
                            font.pixelSize: 14
                            font.weight: Font.Bold
                            color: textPrimary
                        }

                        ListView {
                            id: recentList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: ListModel { id: recentModel }
                            delegate: Rectangle {
                                width: parent.width
                                height: 36
                                color: index % 2 === 0 ? bgSecondary : bgPrimary
                                radius: 4
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 8
                                    Label { text: model.operation_id; font.weight: Font.Bold; color: textPrimary; Layout.preferredWidth: 80 }
                                    Label { text: model.source; color: textSecondary; Layout.fillWidth: true; elide: Text.ElideMiddle }
                                    Label {
                                        text: model.status === "completed" ? "OK" : model.status === "completed_with_errors" ? "⚠" : "●"
                                        color: model.status === "completed" ? success : error
                                    }
                                }
                            }
                            Label {
                                anchors.centerIn: parent
                                text: "Sin operaciones aún"
                                color: textSecondary
                                visible: recentModel.count === 0
                                font.pixelSize: 13
                            }
                        }
                    }
                }
            }

            Component.onCompleted: refreshDashboard()
            function refreshDashboard() {
                var raw = python.get_dashboard_stats();
                var data = parseJson(raw);
                if (!data) return;
                totalOpsLabel.text = String(data.total_operations || 0);
                serviceLabel.text = data.connected ? "Activo" : "Inactivo";
                serviceLabel.color = data.connected ? success : error;
                recentModel.clear();
                if (data.recent) {
                    for (var i = 0; i < data.recent.length; i++) {
                        recentModel.append(data.recent[i]);
                    }
                }
            }
        }

        // ======== Página 1: Búsqueda por Vertical ========
        Rectangle {
            color: bgSecondary
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Label {
                    text: "Búsqueda por Vertical"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: textPrimary
                }

                // Feedback
                Rectangle {
                    id: searchBanner
                    Layout.fillWidth: true
                    radius: 8
                    visible: false
                    height: 40
                    Label {
                        id: searchBannerText
                        anchors.centerIn: parent
                        color: "white"
                        font.pixelSize: 13
                    }
                }

                // Configuración de búsqueda
                Pane {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12

                        Label { text: "Parámetros de Búsqueda"; font.weight: Font.Bold; color: textPrimary }

                        RowLayout {
                            spacing: 12
                            Layout.fillWidth: true

                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true
                                Label { text: "Vertical"; font.pixelSize: 11; color: textSecondary }
                                ComboBox {
                                    id: verticalCombo
                                    model: ListModel { id: verticalsModel }
                                    textRole: "display"
                                    Layout.fillWidth: true
                                    onCurrentIndexChanged: {
                                        if (currentIndex >= 0 && verticalsModel.count > 0) {
                                            updateSitesForVertical();
                                        }
                                    }
                                }
                            }

                            ColumnLayout {
                                spacing: 4
                                Layout.fillWidth: true
                                Label { text: "Sitio (opcional)"; font.pixelSize: 11; color: textSecondary }
                                ComboBox {
                                    id: siteCombo
                                    model: ListModel { id: sitesModel }
                                    textRole: "display"
                                    Layout.fillWidth: true
                                }
                            }
                        }

                        RowLayout {
                            spacing: 12
                            Layout.fillWidth: true

                            TextField {
                                id: searchQueryInput
                                placeholderText: "Ej: autos usados, iPhone 15, departamento en renta..."
                                Layout.fillWidth: true
                                onAccepted: runSearch()
                            }

                            Button {
                                id: searchBtn
                                text: "🔍 Buscar"
                                enabled: searchQueryInput.text.length > 0 && verticalCombo.currentIndex >= 0 && !searchSpinner.running
                                background: Rectangle {
                                    radius: 8
                                    color: parent.enabled ? accent : "#94a3b8"
                                }
                                contentItem: Text {
                                    text: parent.text
                                    color: "white"
                                    font.pixelSize: 14
                                }
                                onClicked: runSearch()
                            }
                        }

                        RowLayout {
                            spacing: 8
                            BusyIndicator {
                                id: searchSpinner
                                running: false
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                            }
                            Label {
                                id: searchStatusLabel
                                color: textSecondary
                                font.pixelSize: 12
                                visible: false
                            }
                            Item { Layout.fillWidth: true }
                            Button {
                                text: "↻ Recargar Verticales"
                                flat: true
                                onClicked: loadSearchVerticales()
                            }
                        }
                    }
                }

                // Resultados
                Pane {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    padding: 16
                    visible: searchResultsModel.count > 0
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12

                        // Summary
                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                id: searchSummaryLabel
                                text: "0 resultados"
                                font.pixelSize: 14
                                font.weight: Font.Bold
                                color: textPrimary
                            }
                            Item { Layout.fillWidth: true }
                            Label {
                                id: searchAdaptersLabel
                                text: ""
                                font.pixelSize: 12
                                color: textSecondary
                            }
                        }

                        // Results list
                        ListView {
                            id: searchResultsList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: ListModel { id: searchResultsModel }
                            clip: true
                            spacing: 8

                            delegate: Rectangle {
                                width: parent.width
                                height: {
                                    // Auto height based on content
                                    var base = 80;
                                    if (model.description) base += 20;
                                    return base;
                                }
                                radius: 8
                                color: bgSecondary
                                border.color: "#e2e8f0"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 4

                                    // Title + Source badge
                                    RowLayout {
                                        spacing: 8
                                        Layout.fillWidth: true

                                        Label {
                                            text: model.title || "(Sin título)"
                                            font.weight: Font.Bold
                                            font.pixelSize: 14
                                            color: textPrimary
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }

                                        Rectangle {
                                            color: "#dbeafe"
                                            radius: 4
                                            height: 20
                                            implicitWidth: siteLabel.implicitWidth + 8
                                            Label {
                                                id: siteLabel
                                                text: model.source_site || "?"
                                                font.pixelSize: 10
                                                color: "#1e40af"
                                                anchors.centerIn: parent
                                            }
                                        }
                                    }

                                    // Description (if available)
                                    Label {
                                        text: model.description || ""
                                        font.pixelSize: 12
                                        color: textSecondary
                                        elide: Text.ElideRight
                                        maximumLineCount: 2
                                        visible: text.length > 0
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                        Layout.maximumHeight: 36
                                    }

                                    // Price + Rank row
                                    RowLayout {
                                        spacing: 12
                                        Layout.fillWidth: true

                                        Label {
                                            text: model.price ? "$" + Number(model.price).toLocaleString(Qt.locale(), "f", 2) : ""
                                            font.pixelSize: 16
                                            font.weight: Font.Bold
                                            color: "#059669"
                                            visible: model.price
                                        }

                                        Label {
                                            text: model.currency || ""
                                            font.pixelSize: 11
                                            color: textSecondary
                                            visible: model.currency
                                        }

                                        Item { Layout.fillWidth: true }

                                        Label {
                                            text: "#" + (model.rank + 1)
                                            font.pixelSize: 11
                                            color: textSecondary
                                        }

                                        Button {
                                            text: "Abrir"
                                            flat: true
                                            enabled: model.url && model.url.length > 0
                                            onClicked: {
                                                if (model.url) {
                                                    Qt.openUrlExternally(model.url);
                                                }
                                            }
                                            contentItem: Text {
                                                text: parent.text
                                                color: parent.enabled ? accent : textSecondary
                                                font.pixelSize: 12
                                            }
                                        }
                                    }
                                }
                            }

                            // Empty state
                            Label {
                                anchors.centerIn: parent
                                text: "Realiza una búsqueda para ver resultados."
                                color: textSecondary
                                visible: searchResultsModel.count === 0
                                font.pixelSize: 14
                            }
                        }
                    }
                }
            }

            // --- Funciones de la página de búsqueda ---

            function loadSearchVerticales() {
                var raw = python.get_verticals();
                var data = parseJson(raw);
                if (!data || data.error) return;
                verticalsModel.clear();
                for (var i = 0; i < data.length; i++) {
                    verticalsModel.append({ display: data[i], value: data[i] });
                }
                if (verticalsModel.count > 0) {
                    verticalCombo.currentIndex = 0;
                }
            }

            function updateSitesForVertical() {
                var vertical = verticalsModel.get(verticalCombo.currentIndex).value;
                var raw = python.adapters;
                var adapters = parseJson(raw);
                if (!adapters) return;
                sitesModel.clear();
                sitesModel.append({ display: "Todos los sitios", value: "all" });
                for (var i = 0; i < adapters.length; i++) {
                    if (adapters[i].vertical === vertical) {
                        sitesModel.append({
                            display: adapters[i].name,
                            value: adapters[i].name
                        });
                    }
                }
                siteCombo.currentIndex = 0;
            }

            function runSearch() {
                if (!searchQueryInput.text || verticalCombo.currentIndex < 0) return;

                searchSpinner.running = true;
                searchStatusLabel.text = "Buscando...";
                searchStatusLabel.visible = true;

                var vertical = verticalsModel.get(verticalCombo.currentIndex).value;
                var site = siteCombo.currentIndex >= 0 ? sitesModel.get(siteCombo.currentIndex).value : "all";

                var raw = python.search_adapters(searchQueryInput.text, vertical, site);
                var data = parseJson(raw);

                searchSpinner.running = false;

                if (!data || data.error) {
                    searchBanner.color = error;
                    searchBannerText.text = data ? data.error : "Error en búsqueda";
                    searchBanner.visible = true;
                    searchStatusLabel.text = "Error";
                    searchStatusLabel.color = error;
                    return;
                }

                // Mostrar resultados
                searchResultsModel.clear();
                searchSummaryLabel.text = data.total_found + " resultados";
                searchAdaptersLabel.text = "en " + data.adapters_used + " adaptador(es)";

                if (data.items) {
                    for (var i = 0; i < data.items.length; i++) {
                        searchResultsModel.append(data.items[i]);
                    }
                }

                searchBanner.color = success;
                searchBannerText.text = "Búsqueda completada: " + data.total_found + " resultados";
                searchBanner.visible = true;
                searchStatusLabel.text = "OK";
                searchStatusLabel.color = success;

                // Auto-ocultar banner
                searchHideTimer.start();
            }

            Timer {
                id: searchHideTimer
                interval: 4000
                onTriggered: searchBanner.visible = false
            }
        }

        // ======== Página 2: Nuevo Scraper ========
        Rectangle {
            color: bgSecondary
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Label {
                    text: "Nueva Configuración de Scraping"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: textPrimary
                }

                // Feedback de último resultado
                Rectangle {
                    id: resultBanner
                    Layout.fillWidth: true
                    radius: 8
                    visible: false
                    height: 40
                    color: success
                    Label {
                        id: resultBannerText
                        anchors.centerIn: parent
                        color: "white"
                        font.pixelSize: 13
                    }
                }

                // Conexión
                Pane {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12

                        Label { text: "Fuente"; font.weight: Font.Bold; color: textPrimary }

                        RowLayout {
                            spacing: 12
                            ComboBox {
                                id: sourceTypeCombo
                                model: ["web_page", "api", "html_file", "sitemap"]
                                Layout.preferredWidth: 140
                            }
                            TextField {
                                id: sourceField
                                placeholderText: "https://ejemplo.com/productos"
                                Layout.fillWidth: true
                            }
                        }
                    }
                }

                // Campos
                Pane {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    padding: 16
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8

                        Label { text: "Campos a Extraer"; font.weight: Font.Bold; color: textPrimary }

                        ListModel { id: fieldsModel }

                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: fieldsModel
                            clip: true
                            delegate: Rectangle {
                                width: parent.width
                                height: 40
                                color: index % 2 === 0 ? bgSecondary : bgPrimary
                                radius: 4
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 8
                                    Label { text: model.name; Layout.preferredWidth: 120; font.weight: Font.Bold; color: textPrimary }
                                    Label { text: model.selector; Layout.preferredWidth: 180; color: textSecondary }
                                    Label { text: model.fieldType; color: textSecondary }
                                    Item { Layout.fillWidth: true }
                                    Button {
                                        text: "×"
                                        flat: true
                                        onClicked: fieldsModel.remove(index)
                                    }
                                }
                            }
                        }

                        RowLayout {
                            spacing: 8
                            TextField {
                                id: fieldNameInput
                                placeholderText: "Nombre"
                                Layout.preferredWidth: 120
                            }
                            TextField {
                                id: fieldSelectorInput
                                placeholderText: "Selector CSS"
                                Layout.preferredWidth: 200
                            }
                            ComboBox {
                                id: fieldTypeCombo
                                model: ["text", "price", "url", "number", "date", "image"]
                                Layout.preferredWidth: 100
                            }
                            Button {
                                text: "+ Agregar"
                                onClicked: {
                                    if (fieldNameInput.text && fieldSelectorInput.text) {
                                        fieldsModel.append({
                                            name: fieldNameInput.text,
                                            selector: fieldSelectorInput.text,
                                            fieldType: fieldTypeCombo.currentText
                                        })
                                        fieldNameInput.text = ""
                                        fieldSelectorInput.text = ""
                                    }
                                }
                            }
                        }
                    }
                }

                // Botones de acción
                RowLayout {
                    spacing: 12
                    Layout.fillWidth: true

                    BusyIndicator {
                        id: scrapeSpinner
                        running: false
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 24
                    }

                    Label {
                        id: scrapeStatusLabel
                        color: textSecondary
                        font.pixelSize: 12
                        visible: false
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "Probar Conexión"
                        flat: true
                        onClicked: {
                            python.check_connection();
                            scrapeStatusLabel.text = python.connected ? "Conectado" : "Desconectado";
                            scrapeStatusLabel.color = python.connected ? success : error;
                            scrapeStatusLabel.visible = true;
                        }
                    }
                    Button {
                        text: "▶ Ejecutar Scraping"
                        enabled: sourceField.text.length > 0 && fieldsModel.count > 0 && !scrapeSpinner.running
                        background: Rectangle {
                            radius: 8
                            color: parent.enabled ? accent : "#94a3b8"
                        }
                        contentItem: Text {
                            text: parent.text
                            color: "white"
                            font.pixelSize: 14
                        }
                        onClicked: {
                            loading = true;
                            scrapeSpinner.running = true;
                            scrapeStatusLabel.text = "Ejecutando...";
                            scrapeStatusLabel.visible = true;

                            var fields = [];
                            for (var i = 0; i < fieldsModel.count; i++) {
                                fields.push(fieldsModel.get(i));
                            }

                            var result = python.run_scrape(
                                sourceField.text,
                                sourceTypeCombo.currentText,
                                JSON.stringify(fields)
                            );

                            scrapeSpinner.running = false;
                            loading = false;

                            if (result.startsWith("Error:")) {
                                resultBanner.color = error;
                                resultBannerText.text = result;
                                scrapeStatusLabel.text = "Error";
                                scrapeStatusLabel.color = error;
                            } else {
                                resultBanner.color = success;
                                resultBannerText.text = "Operación " + result + " completada";
                                scrapeStatusLabel.text = "OK — ID: " + result;
                                scrapeStatusLabel.color = success;
                            }
                            resultBanner.visible = true;
                            scrapeStatusLabel.visible = true;

                            // Auto-ocultar banner
                            hideTimer.start();
                        }
                    }
                }
            }

            Timer {
                id: hideTimer
                interval: 5000
                onTriggered: resultBanner.visible = false
            }
        }

        // ======== Página 2: Resultados ========
        Rectangle {
            color: bgSecondary
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Label {
                    text: "Resultados de Operación"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: textPrimary
                }

                RowLayout {
                    spacing: 8
                    Layout.fillWidth: true

                    ComboBox {
                        id: resultsOpCombo
                        model: ListModel { id: resultsOpsModel }
                        textRole: "display"
                        Layout.fillWidth: true
                        onCurrentIndexChanged: {
                            if (currentIndex >= 0 && resultsOpsModel.count > 0) {
                                var op = resultsOpsModel.get(currentIndex);
                                loadOperationResults(op.op_id);
                            }
                        }
                    }
                    Button {
                        text: "↻"
                        onClicked: loadResults()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"
                    clip: true

                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 16

                        ColumnLayout {
                            width: parent.width
                            spacing: 8

                            Label {
                                id: resultsSummary
                                text: "Selecciona una operación para ver resultados."
                                color: textSecondary
                                font.pixelSize: 13
                                visible: resultsItemsModel.count === 0
                            }

                            ListView {
                                id: resultsListView
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                model: ListModel { id: resultsItemsModel }
                                clip: true
                                spacing: 4
                                delegate: Rectangle {
                                    width: parent.width
                                    height: 80
                                    radius: 8
                                    color: bgSecondary
                                    border.color: "#e2e8f0"

                                    ColumnLayout {
                                        spacing: 4
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        Repeater {
                                            model: {
                                                var keys = Object.keys(model.data);
                                                return keys.map(function(k) { return {key: k, value: JSON.stringify(model.data[k])}; });
                                            }
                                            Label {
                                                text: model.key + ": " + model.value
                                                font.pixelSize: 12
                                                color: textPrimary
                                                elide: Text.ElideRight
                                                maximumLineCount: 1
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            function loadResults() {
                var raw = python.get_history();
                var data = parseJson(raw);
                if (!data) return;
                resultsOpsModel.clear();
                for (var i = 0; i < data.length; i++) {
                    resultsOpsModel.append({
                        display: data[i].operation_id + " — " + data[i].source,
                        op_id: data[i].operation_id
                    });
                }
                if (resultsOpsModel.count > 0) {
                    resultsOpCombo.currentIndex = 0;
                }
            }

            function loadOperationResults(opId) {
                var raw = python.get_results(opId);
                var data = parseJson(raw);
                if (!data || data.error) {
                    resultsSummary.text = data ? data.error : "Error al cargar resultados";
                    resultsSummary.visible = true;
                    return;
                }
                resultsSummary.visible = false;
                resultsSummary.text = data.total_found + " resultados encontrados";
                resultsItemsModel.clear();
                if (data.items) {
                    for (var i = 0; i < data.items.length; i++) {
                        resultsItemsModel.append(data.items[i]);
                    }
                }
            }
        }

        // ======== Página 3: Entregas ========
        Rectangle {
            color: bgSecondary
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Label {
                    text: "Configuración de Entregas"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: textPrimary
                }

                // Seleccionar operación
                Pane {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        Label { text: "Operación a entregar"; font.weight: Font.Bold; color: textPrimary }
                        ComboBox {
                            id: deliveryOpCombo
                            model: ListModel { id: deliveryOpsModel }
                            textRole: "display"
                            Layout.fillWidth: true
                        }
                    }
                }

                // Email
                Pane {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        Label { text: "Correo Electrónico"; font.weight: Font.Bold; color: textPrimary }
                        RowLayout {
                            spacing: 8
                            TextField {
                                id: emailInput
                                placeholderText: "email@ejemplo.com"
                                Layout.fillWidth: true
                            }
                            Button {
                                text: "+ Agregar"
                                onClicked: {
                                    if (emailInput.text) {
                                        emailsModel.append({email: emailInput.text});
                                        emailInput.text = "";
                                    }
                                }
                            }
                        }
                        ListModel { id: emailsModel }
                        ListView {
                            Layout.fillWidth: true
                            height: Math.min(60, emailsModel.count * 30)
                            model: emailsModel
                            visible: emailsModel.count > 0
                            delegate: Rectangle {
                                width: parent.width
                                height: 28
                                color: bgSecondary
                                radius: 4
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    Label { text: model.email; color: textPrimary }
                                    Item { Layout.fillWidth: true }
                                    Button { text: "×"; flat: true; onClicked: emailsModel.remove(index) }
                                }
                            }
                        }
                        Label {
                            text: emailsModel.count === 0 ? "Sin destinatarios configurados." : ""
                            color: textSecondary; font.pixelSize: 12
                        }
                    }
                }

                // WhatsApp
                Pane {
                    Layout.fillWidth: true
                    padding: 16
                    background: Rectangle {
                        color: bgPrimary
                        border.color: "#e2e8f0"
                        radius: 12
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        Label { text: "WhatsApp"; font.weight: Font.Bold; color: textPrimary }
                        RowLayout {
                            spacing: 8
                            TextField {
                                id: whatsappInput
                                placeholderText: "521234567890"
                                Layout.fillWidth: true
                            }
                            Button {
                                text: "+ Agregar"
                                onClicked: {
                                    if (whatsappInput.text) {
                                        whatsappModel.append({number: whatsappInput.text});
                                        whatsappInput.text = "";
                                    }
                                }
                            }
                        }
                        ListModel { id: whatsappModel }
                        ListView {
                            Layout.fillWidth: true
                            height: Math.min(60, whatsappModel.count * 30)
                            model: whatsappModel
                            visible: whatsappModel.count > 0
                            delegate: Rectangle {
                                width: parent.width
                                height: 28
                                color: bgSecondary
                                radius: 4
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    Label { text: model.number; color: textPrimary }
                                    Item { Layout.fillWidth: true }
                                    Button { text: "×"; flat: true; onClicked: whatsappModel.remove(index) }
                                }
                            }
                        }
                        Label {
                            text: whatsappModel.count === 0 ? "Sin números configurados." : ""
                            color: textSecondary; font.pixelSize: 12
                        }
                        Button {
                            text: "Enviar Activación"
                            flat: true
                            enabled: false
                        }
                    }
                }

                // Botón enviar
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "Entregar Resultados"
                        enabled: deliveryOpCombo.currentIndex >= 0 && deliveryOpsModel.count > 0
                        background: Rectangle {
                            radius: 8
                            color: parent.enabled ? accent : "#94a3b8"
                        }
                        contentItem: Text {
                            text: parent.text
                            color: "white"
                            font.pixelSize: 14
                        }
                        onClicked: {
                            var emails = [];
                            for (var i = 0; i < emailsModel.count; i++)
                                emails.push(emailsModel.get(i).email);
                            var whatsapp = [];
                            for (var i = 0; i < whatsappModel.count; i++)
                                whatsapp.push(whatsappModel.get(i).number);

                            var opId = deliveryOpsModel.get(deliveryOpCombo.currentIndex).op_id;
                            var result = python.deliver_results(opId, JSON.stringify(emails), JSON.stringify(whatsapp));
                            var data = parseJson(result);
                            deliveryStatus.text = data && !data.error ? "Entrega solicitada exitosamente" : "Error: " + (data ? data.error : result);
                            deliveryStatus.visible = true;
                        }
                    }
                }

                Label {
                    id: deliveryStatus
                    visible: false
                    color: success
                    font.pixelSize: 12
                }
            }

            function loadDeliveryOps() {
                var raw = python.get_history();
                var data = parseJson(raw);
                if (!data) return;
                deliveryOpsModel.clear();
                for (var i = 0; i < data.length; i++) {
                    deliveryOpsModel.append({
                        display: data[i].operation_id + " — " + data[i].source,
                        op_id: data[i].operation_id
                    });
                }
            }
        }

        // ======== Página 4: Historial ========
        Rectangle {
            color: bgSecondary
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Historial de Operaciones"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: textPrimary
                        Layout.fillWidth: true
                    }
                    Button {
                        text: "↻"
                        onClicked: loadHistory()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"
                    clip: true

                    ListView {
                        id: historyList
                        anchors.fill: parent
                        anchors.margins: 8
                        model: ListModel { id: historyModel }
                        clip: true
                        spacing: 4

                        delegate: Rectangle {
                            width: parent.width
                            height: 48
                            radius: 8
                            color: bgSecondary
                            border.color: "#e2e8f0"

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                ColumnLayout {
                                    spacing: 2
                                    Layout.fillWidth: true
                                    Label {
                                        text: model.source
                                        font.weight: Font.Bold
                                        color: textPrimary
                                        font.pixelSize: 13
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        text: model.operation_id + " · " + (model.created_at || "")
                                        color: textSecondary
                                        font.pixelSize: 11
                                    }
                                }

                                Label {
                                    text: model.total_found + " items"
                                    color: textSecondary
                                    font.pixelSize: 12
                                    Layout.preferredWidth: 70
                                }

                                Rectangle {
                                    width: 8
                                    height: 8
                                    radius: 4
                                    color: model.status === "completed" ? success :
                                           model.status === "completed_with_errors" ? "#f59e0b" : error
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    var raw = python.get_operation_detail(model.operation_id);
                                    var data = parseJson(raw);
                                    if (data && !data.error) {
                                        historyDetail.text = JSON.stringify(data, null, 2);
                                        detailDrawer.open();
                                    }
                                }
                            }
                        }

                        Label {
                            anchors.centerIn: parent
                            text: "Sin operaciones registradas"
                            color: textSecondary
                            visible: historyModel.count === 0
                            font.pixelSize: 14
                        }
                    }
                }
            }

            // Drawer de detalle
            Drawer {
                id: detailDrawer
                width: Math.min(window.width * 0.6, 500)
                height: window.height
                edge: Qt.RightEdge

                Rectangle {
                    anchors.fill: parent
                    color: bgPrimary

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 12

                        RowLayout {
                            Label { text: "Detalle"; font.pixelSize: 18; font.weight: Font.Bold; color: textPrimary }
                            Item { Layout.fillWidth: true }
                            Button { text: "✕"; flat: true; onClicked: detailDrawer.close() }
                        }

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            TextArea {
                                id: historyDetail
                                readOnly: true
                                font.family: "Courier New"
                                font.pixelSize: 11
                                color: textPrimary
                                wrapMode: TextEdit.WordWrap
                            }
                        }
                    }
                }
            }

            function loadHistory() {
                var raw = python.get_history();
                var data = parseJson(raw);
                if (!data) return;
                historyModel.clear();
                for (var i = 0; i < data.length; i++) {
                    historyModel.append(data[i]);
                }
            }
        }
    }

    footer: Pane {
        background: Rectangle { color: "#f1f5f9" }
        padding: 8

        RowLayout {
            anchors.fill: parent
            Label {
                text: "Servicio: " + (python.connected ? "Conectado" : "Desconectado")
                font.pixelSize: 11
                color: python.connected ? "#22c55e" : "#ef4444"
            }
            Item { Layout.fillWidth: true }
            Label {
                text: "v0.1.0"
                font.pixelSize: 11
                color: "#94a3b8"
            }
        }
    }
}
