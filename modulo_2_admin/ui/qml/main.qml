import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

/* ═══════════════════════════════════════════════════════════════
   ScrapperGenérico — Admin UI v2
   Diseñado para crear servicios genéricos de extracción
   con filtros configurables por dominio (autos, casas, etc.)
   ═══════════════════════════════════════════════════════════════ */

ApplicationWindow {
    id: window
    visible: true
    width: 1024
    height: 720
    minimumWidth: 780
    minimumHeight: 560
    title: "BuscadorGenérico — Creador de Servicios de Búsqueda"

    Material.theme: Material.Light
    Material.accent: Material.Blue

    // ─── Estado global ──────────────────────────────────────
    property string currentView: "dashboard"
    // sub-vistas: "list", "form" (para servicios), "detail" (para ejecución)
    property string servicesView: "list"
    property string editingServiceId: ""
    property string selectedServiceId: ""
    property string lastRunOpId: ""
    property bool loading: false

    // Colores
    readonly property color bgPrimary: "#ffffff"
    readonly property color bgSecondary: "#f8fafc"
    readonly property color bgCard: "#ffffff"
    readonly property color textPrimary: "#1a1a2e"
    readonly property color textSecondary: "#64748b"
    readonly property color accent: "#2563eb"
    readonly property color accentLight: "#dbeafe"
    readonly property color success: "#22c55e"
    readonly property color successLight: "#dcfce7"
    readonly property color warning: "#f59e0b"
    readonly property color error: "#ef4444"
    readonly property color errorLight: "#fee2e2"
    readonly property color border: "#e2e8f0"

    // Stored function references (set by pages during init)
    property var _refreshDashboard: null
    property var _refreshServicesList: null
    property var _refreshResults: null
    property var _refreshHistory: null

    // Parse JSON helper
    function parseJson(str) {
        try { return JSON.parse(str); }
        catch(e) { return null; }
    }

    // ─── HEADER ──────────────────────────────────────────────
    header: ToolBar {
        padding: 0
        background: Rectangle {
            color: "#1a1a2e"
        }

        ColumnLayout {
            spacing: 0
            anchors.fill: parent

            // Top bar with logo and nav
            Rectangle {
                Layout.fillWidth: true
                height: 48
                color: "#1a1a2e"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 8
                    spacing: 4

                    Label {
                        text: "🕸️ ScrapperGenérico"
                        color: "white"
                        font.pixelSize: 15
                        font.weight: Font.Bold
                        Layout.rightMargin: 16
                    }

                    // Nav buttons
                    Repeater {
                        model: [
                            {key: "dashboard", label: "Dashboard", icon: "🏠"},
                            {key: "services",  label: "Servicios", icon: "📦"},
                            {key: "run",       label: "Ejecutar",  icon: "▶"},
                            {key: "results",   label: "Resultados",icon: "📊"},
                            {key: "history",   label: "Historial", icon: "📋"},
                        ]
                        delegate: ToolButton {
                            text: modelData.icon + " " + modelData.label
                            highlighted: currentView === modelData.key
                            onClicked: {
                                currentView = modelData.key
                                if (modelData.key === "services") servicesView = "list"
                                if (modelData.key === "dashboard" && dashboardPage.refreshDashboard) dashboardPage.refreshDashboard()
                                if (modelData.key === "services" && servicesPage.refreshServicesList) servicesPage.refreshServicesList()
                                if (modelData.key === "results" && _refreshResults) _refreshResults()
                                if (modelData.key === "history" && _refreshHistory) _refreshHistory()
                            }
                            contentItem: Text {
                                text: parent.text
                                color: currentView === modelData.key ? "#93c5fd" : "white"
                                font.pixelSize: 12
                            }
                            background: Rectangle {
                                color: currentView === modelData.key ? "#ffffff20" : "transparent"
                                radius: 6
                            }
                        }
                    }

                    Item { Layout.fillWidth: true }

                    // Connection indicator
                    Rectangle {
                        width: 8; height: 8; radius: 4
                        color: python.connected ? success : error
                        Layout.alignment: Qt.AlignVCenter
                    }
                    Label {
                        text: python.connected ? "Conectado" : "Offline"
                        color: python.connected ? success : error
                        font.pixelSize: 11
                        Layout.rightMargin: 8
                    }
                }
            }
        }
    }

    // ─── FOOTER ──────────────────────────────────────────────
    footer: Pane {
        background: Rectangle { color: "#f1f5f9" }
        padding: 6

        RowLayout {
            anchors.fill: parent
            Label {
                text: "Creador de Servicios de Búsqueda Genéricos"
                font.pixelSize: 10
                color: "#94a3b8"
            }
            Item { Layout.fillWidth: true }
            Label {
                text: "v0.2.0"
                font.pixelSize: 10
                color: "#94a3b8"
            }
        }
    }

    // ════════════════════════════════════════════════════════
    // CONTENIDO PRINCIPAL
    // ════════════════════════════════════════════════════════
    StackLayout {
        anchors.fill: parent
        currentIndex: {
            if (currentView === "dashboard") return 0
            if (currentView === "services") return 1
            if (currentView === "run") return 2
            if (currentView === "results") return 3
            if (currentView === "history") return 4
            return 0
        }

        // ──── PÁGINA 0: DASHBOARD ───────────────────────────
        Page {
            id: dashboardPage
            background: Rectangle { color: bgSecondary }

            ScrollView {
                anchors.fill: parent
                anchors.margins: 24
                clip: true
                contentWidth: availableWidth

                ColumnLayout {
                    width: parent.width
                    spacing: 20

                    Label {
                        text: "Dashboard"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: textPrimary
                    }

                    // Stats row
                    RowLayout {
                        spacing: 16
                        Layout.fillWidth: true

                        Rectangle {
                            Layout.fillWidth: true
                            height: 80
                            radius: 12
                            color: bgCard
                            border.color: border

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 4
                                Label {
                                    id: statServices
                                    text: "0"
                                    font.pixelSize: 28
                                    font.weight: Font.Bold
                                    color: accent
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Label {
                                    text: "Servicios"
                                    font.pixelSize: 12
                                    color: textSecondary
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 80
                            radius: 12
                            color: bgCard
                            border.color: border

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 4
                                Label {
                                    id: statRuns
                                    text: "0"
                                    font.pixelSize: 28
                                    font.weight: Font.Bold
                                    color: success
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Label {
                                    text: "Ejecuciones"
                                    font.pixelSize: 12
                                    color: textSecondary
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 80
                            radius: 12
                            color: bgCard
                            border.color: border

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 4
                                Label {
                                    id: statOps
                                    text: "0"
                                    font.pixelSize: 28
                                    font.weight: Font.Bold
                                    color: warning
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
                    }

                    // Services grid
                    Label {
                        text: "Servicios Creados"
                        font.pixelSize: 16
                        font.weight: Font.Bold
                        color: textPrimary
                    }

                    // Grid of service cards
                    Flow {
                        id: dashboardFlow
                        Layout.fillWidth: true
                        spacing: 12

                        Repeater {
                            id: dashboardServicesRepeater
                            model: ListModel { id: dashboardServicesModel }

                            Rectangle {
                                width: Math.min(280, Math.max(200, dashboardFlow.width / 3 - 16))
                                height: 120
                                radius: 12
                                color: bgCard
                                border.color: border

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        selectedServiceId = model.service_id
                                        currentView = "run"
                                    }
                                }

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 4

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        Label {
                                            text: model.name
                                            font.weight: Font.Bold
                                            color: textPrimary
                                            font.pixelSize: 14
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                        Label {
                                            text: model.field_count + " cmp"
                                            font.pixelSize: 10
                                            color: textSecondary
                                        }
                                    }

                                    Label {
                                        text: model.sources_count > 0 ? model.sources_count + " fuente(s)" : ""
                                        color: textSecondary
                                        font.pixelSize: 11
                                        elide: Text.ElideMiddle
                                        Layout.fillWidth: true
                                    }

                                    Item { Layout.fillHeight: true }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        Label {
                                            text: model.filter_count > 0 ? model.filter_count + " filtros" : "Sin filtros"
                                            font.pixelSize: 10
                                            color: model.filter_count > 0 ? accent : textSecondary
                                        }
                                        Item { Layout.fillWidth: true }
                                        Label {
                                            text: "▶ Ejecutar"
                                            font.pixelSize: 11
                                            color: accent
                                            font.weight: Font.Bold
                                        }
                                    }
                                }
                            }
                        }

                        // Card: Create new service
                        Rectangle {
                            width: Math.min(280, Math.max(200, dashboardFlow.width / 3 - 16))
                            height: 120
                            radius: 12
                            color: bgCard
                            border.color: accent
                            border.width: 2

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    editingServiceId = ""
                                    servicesView = "form"
                                    currentView = "services"
                                }
                            }

                            ColumnLayout {
                                anchors.centerIn: parent
                                spacing: 8
                                Label {
                                    text: "+"
                                    font.pixelSize: 32
                                    color: accent
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                Label {
                                    text: "Nuevo Servicio"
                                    font.pixelSize: 13
                                    color: accent
                                    font.weight: Font.Bold
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }
                    }

                    // Recent activity
                    Label {
                        text: "Actividad Reciente"
                        font.pixelSize: 16
                        font.weight: Font.Bold
                        color: textPrimary
                    }

                    ListView {
                        Layout.fillWidth: true
                        height: 160
                        clip: true
                        model: ListModel { id: dashboardRecentModel }
                        delegate: Rectangle {
                            width: parent.width
                            height: 32
                            color: index % 2 === 0 ? bgSecondary : "transparent"
                            radius: 4
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 8
                                Label {
                                    text: model.operation_id
                                    font.weight: Font.Bold
                                    color: textPrimary
                                    font.pixelSize: 11
                                    Layout.preferredWidth: 80
                                }
                                Label {
                                    text: model.source
                                    color: textSecondary
                                    font.pixelSize: 11
                                    Layout.fillWidth: true
                                    elide: Text.ElideMiddle
                                }
                                Label {
                                    text: model.status === "completed" ? "✓" :
                                          model.status === "completed_with_errors" ? "⚠" : "●"
                                    color: model.status === "completed" ? success : error
                                }
                            }
                        }
                        Label {
                            anchors.centerIn: parent
                            text: "Sin actividad aún"
                            color: textSecondary
                            visible: dashboardRecentModel.count === 0
                            font.pixelSize: 13
                        }
                    }
                }
            }

            property var refreshDashboard: function() {
                var raw = python.get_dashboard_stats()
                var data = parseJson(raw)
                if (!data) return

                // Update stats
                statServices.text = String(data.total_services || 0)
                statRuns.text = String(data.total_runs || 0)
                statOps.text = String(data.total_operations || 0)

                dashboardServicesModel.clear()
                if (data.services) {
                    for (var i = 0; i < data.services.length; i++)
                        dashboardServicesModel.append(data.services[i])
                }

                dashboardRecentModel.clear()
                if (data.recent) {
                    for (var i = 0; i < data.recent.length; i++)
                        dashboardRecentModel.append(data.recent[i])
                }
            }

            Component.onCompleted: {
                window._refreshDashboard = refreshDashboard
                refreshDashboard()
            }
        }

        // ──── PÁGINA 1: SERVICIOS ────────────────────────────
        Page {
            id: servicesPage
            background: Rectangle { color: bgSecondary }

            // ─── Sub-vista: Lista de servicios ───
            ColumnLayout {
                id: servicesListView
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16
                visible: servicesView === "list"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Label {
                        text: "Mis Servicios de Búsqueda"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: textPrimary
                        Layout.fillWidth: true
                    }
                    Button {
                        text: "+ Nuevo Servicio"
                        onClicked: {
                            editingServiceId = ""
                            servicesView = "form"
                        }
                    }
                    Button {
                        text: "↻"
                        onClicked: refreshServicesList()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgCard
                    border.color: border
                    clip: true

                    ListView {
                        id: servicesList
                        anchors.fill: parent
                        anchors.margins: 8
                        model: ListModel { id: servicesListModel }
                        spacing: 4
                        clip: true

                        delegate: Rectangle {
                            width: parent.width
                            height: 64
                            radius: 8
                            color: bgSecondary
                            border.color: border

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12

                                ColumnLayout {
                                    spacing: 2
                                    Layout.fillWidth: true

                                    Label {
                                        text: model.name
                                        font.weight: Font.Bold
                                        color: textPrimary
                                        font.pixelSize: 14
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                    Label {
                                        text: model.sources_count + " fuente(s) · " + model.field_count + " campos · " + model.filter_count + " filtros"
                                        color: textSecondary
                                        font.pixelSize: 11
                                        elide: Text.ElideMiddle
                                        Layout.fillWidth: true
                                    }
                                }

                                RowLayout {
                                    spacing: 8
                                    Layout.alignment: Qt.AlignVCenter
                                    Button {
                                        text: "▶ Ejecutar"
                                        flat: true
                                        onClicked: {
                                            selectedServiceId = model.service_id
                                            currentView = "run"
                                        }
                                    }
                                    Button {
                                        text: "✎ Editar"
                                        flat: true
                                        onClicked: {
                                            editingServiceId = model.service_id
                                            loadServiceForm(model.service_id)
                                        }
                                    }
                                    Button {
                                        text: "✕"
                                        flat: true
                                        onClicked: {
                                            python.delete_service(model.service_id)
                                            refreshServicesList()
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Empty state (outside ListView for proper centering)
                    Label {
                        anchors.centerIn: parent
                        text: "No tienes servicios creados aún.\nCrea tu primer servicio de búsqueda."
                        color: textSecondary
                        font.pixelSize: 13
                        horizontalAlignment: Text.AlignHCenter
                        visible: servicesListModel.count === 0
                    }
                }
            }

            // ─── Sub-vista: Formulario de servicio ───
            ScrollView {
                id: serviceFormView
                anchors.fill: parent
                anchors.margins: 24
                clip: true
                contentWidth: availableWidth
                visible: servicesView === "form"

                ColumnLayout {
                    width: parent.width
                    spacing: 16

                    // Header
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: editingServiceId ? "Editar Servicio" : "Nuevo Servicio de Búsqueda"
                            font.pixelSize: 22
                            font.weight: Font.Bold
                            color: textPrimary
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "← Volver"
                            flat: true
                            onClicked: servicesView = "list"
                        }
                    }

                    // ─── Sección: Info General ───
                    Pane {
                        Layout.fillWidth: true
                        padding: 16
                        background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                        ColumnLayout {
                            spacing: 12
                            Label { text: "Información General"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 14 }

                            RowLayout { spacing: 12
                                ColumnLayout { spacing: 4; Layout.fillWidth: true
                                    Label { text: "Nombre del Servicio"; font.pixelSize: 11; color: textSecondary }
                                    TextField { id: formServiceName; placeholderText: "Ej: Autos Eléctricos en Cuba"; Layout.fillWidth: true }
                                }
                                ColumnLayout { spacing: 4; Layout.fillWidth: true
                                    Label { text: "Descripción"; font.pixelSize: 11; color: textSecondary }
                                    TextField { id: formDescription; placeholderText: "¿Para qué es este servicio?"; Layout.fillWidth: true }
                                }
                            }
                        }
                    }

                    // ─── Sección: Sitios Web a Buscar ───
                    Pane {
                        Layout.fillWidth: true
                        padding: 16
                        background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                        ColumnLayout {
                            spacing: 10
                            Label { text: "Sitios Web a Buscar"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 14 }
                            Label { text: "Agrega uno o más sitios. Cada fuente se buscará automáticamente."; font.pixelSize: 11; color: textSecondary; wrapMode: Text.WordWrap }

                            ListModel { id: formSourcesModel }

                            ListView {
                                id: formSourcesList
                                Layout.fillWidth: true
                                height: Math.min(160, formSourcesModel.count * 44 + 8)
                                model: formSourcesModel
                                clip: true
                                spacing: 4

                                delegate: Rectangle {
                                    width: parent.width
                                    height: 40
                                    radius: 6
                                    color: bgSecondary
                                    border.color: border

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 8
                                        Label { text: model.name; font.weight: Font.Bold; color: textPrimary; Layout.preferredWidth: 120; elide: Text.ElideRight }
                                        Label { text: model.url; color: textSecondary; Layout.fillWidth: true; elide: Text.ElideRight; font.pixelSize: 11 }
                                        Button { text: "✕"; flat: true; onClicked: formSourcesModel.remove(index) }
                                    }
                                }
                            }

                            RowLayout {
                                spacing: 8
                                TextField { id: formSourceName; placeholderText: "Nombre (ej: Revolico)"; Layout.preferredWidth: 140 }
                                TextField { id: formSourceUrl; placeholderText: "URL del sitio"; Layout.fillWidth: true }
                                Button {
                                    text: "+ Agregar"
                                    onClicked: {
                                        if (formSourceName.text && formSourceUrl.text) {
                                            formSourcesModel.append({
                                                name: formSourceName.text,
                                                url: formSourceUrl.text,
                                                source_type: "web_page"
                                            })
                                            formSourceName.text = ""
                                            formSourceUrl.text = ""
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // ─── Sección: Datos a Extraer ───
                    Pane {
                        Layout.fillWidth: true
                        padding: 16
                        background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                        ColumnLayout {
                            spacing: 10
                            Label { text: "¿Qué Información Quieres Recolectar?"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 14 }
                            Label { text: "Define los datos de cada anuncio: título, precio, ubicación, fotos, etc."; font.pixelSize: 11; color: textSecondary; wrapMode: Text.WordWrap }

                            ListModel { id: formFieldsModel }

                            ListView {
                                id: formFieldsList
                                Layout.fillWidth: true
                                height: Math.min(200, formFieldsModel.count * 44 + 8)
                                model: formFieldsModel
                                clip: true
                                spacing: 4

                                delegate: Rectangle {
                                    width: parent.width
                                    height: 40
                                    radius: 6
                                    color: bgSecondary
                                    border.color: border

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 8

                                        Label { text: model.name; font.weight: Font.Bold; color: textPrimary; Layout.preferredWidth: 100; elide: Text.ElideRight }
                                        Label { text: model.selector; color: textSecondary; Layout.preferredWidth: 140; elide: Text.ElideRight; font.pixelSize: 11 }
                                        Label { text: model.fieldType; color: textSecondary; Layout.preferredWidth: 60; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Button { text: "✕"; flat: true; onClicked: formFieldsModel.remove(index) }
                                    }
                                }
                            }

                            RowLayout {
                                spacing: 8
                                TextField { id: formFieldName; placeholderText: "Nombre del dato (ej: Título)"; Layout.preferredWidth: 120 }
                                TextField { id: formFieldSelector; placeholderText: "Selector CSS (ej: h2.titulo)"; Layout.fillWidth: true }
                                ComboBox { id: formFieldType; model: ["text", "price", "url", "number", "date", "image", "phone", "email"]; Layout.preferredWidth: 90 }
                                Button {
                                    text: "+ Agregar"
                                    onClicked: {
                                        if (formFieldName.text && formFieldSelector.text) {
                                            formFieldsModel.append({
                                                name: formFieldName.text,
                                                selector: formFieldSelector.text,
                                                fieldType: formFieldType.currentText,
                                                isFilter: false,
                                                filterType: "text",
                                                filterOptions: "",
                                                filterLabel: "",
                                            })
                                            formFieldName.text = ""
                                            formFieldSelector.text = ""
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // ─── Sección: Filtros de Usuario ───
                    Pane {
                        Layout.fillWidth: true
                        padding: 16
                        background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                        ColumnLayout {
                            spacing: 10
                            Label { text: "Filtros de Búsqueda (opcional)"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 14 }
                            Label { text: "Activa filtros para buscar por precio, ubicación, rango de fechas, etc."; font.pixelSize: 11; color: textSecondary; wrapMode: Text.WordWrap }

                            ListView {
                                id: filterConfigList
                                Layout.fillWidth: true
                                height: Math.min(200, formFieldsModel.count * 48 + 8)
                                model: formFieldsModel
                                clip: true
                                spacing: 4

                                delegate: Rectangle {
                                    width: parent.width
                                    height: 44
                                    radius: 6
                                    color: bgSecondary
                                    border.color: border

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 8

                                        CheckBox {
                                            id: filterCb
                                            checked: model.isFilter
                                            text: model.name
                                            font.weight: Font.Bold
                                            Layout.preferredWidth: 120
                                        }

                                        ComboBox {
                                            id: filterTypeCombo
                                            model: ["text", "range", "dropdown", "checkbox", "date_range"]
                                            currentIndex: {
                                                var types = ["text", "range", "dropdown", "checkbox", "date_range"]
                                                var idx = types.indexOf(model.filterType)
                                                return idx >= 0 ? idx : 0
                                            }
                                            enabled: filterCb.checked
                                            Layout.preferredWidth: 110
                                        }

                                        TextField {
                                            id: filterLabelField
                                            text: model.filterLabel
                                            placeholderText: "Label del filtro"
                                            enabled: filterCb.checked
                                            Layout.fillWidth: true
                                            font.pixelSize: 11
                                        }

                                        TextField {
                                            id: filterOptionsField
                                            text: model.filterOptions
                                            placeholderText: "Opciones (a,b,c)"
                                            enabled: filterCb.checked && filterTypeCombo.currentText === "dropdown"
                                            Layout.preferredWidth: 140
                                            font.pixelSize: 11
                                        }

                                        onVisibleChanged: syncFilter()
                                        Component.onCompleted: syncFilter()

                                        function syncFilter() {
                                            formFieldsModel.set(index, {
                                                name: model.name,
                                                selector: model.selector,
                                                fieldType: model.fieldType,
                                                isFilter: filterCb.checked,
                                                filterType: filterTypeCombo.currentText,
                                                filterOptions: filterOptionsField.text,
                                                filterLabel: filterLabelField.text,
                                            })
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // ─── Sección: Entrega ───
                    Pane {
                        Layout.fillWidth: true
                        padding: 16
                        background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                        ColumnLayout {
                            spacing: 10
                            Label { text: "Entrega de Resultados"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 14 }

                            RowLayout { spacing: 12
                                ColumnLayout { spacing: 4; Layout.fillWidth: true
                                    Label { text: "Emails (separados por coma)"; font.pixelSize: 11; color: textSecondary }
                                    TextField { id: formEmails; placeholderText: "user@ejemplo.com, otro@ejemplo.com"; Layout.fillWidth: true }
                                }
                            }
                            CheckBox { id: formGenerateWeb; text: "Generar página web de resultados"; checked: true }
                        }
                    }

                    // ─── Botón Guardar ───
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Item { Layout.fillWidth: true }

                        BusyIndicator {
                            id: saveSpinner
                            running: false
                            Layout.preferredWidth: 24; Layout.preferredHeight: 24
                        }
                        Label {
                            id: saveStatus
                            visible: false
                            font.pixelSize: 12
                        }
                        Button {
                            text: "💾 Guardar Servicio"
                            enabled: formServiceName.text && formSourcesModel.count > 0 && formFieldsModel.count > 0 && !saveSpinner.running
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
                                    saveSpinner.running = true
                                    saveStatus.visible = false

                                    // Build sources array
                                    var sources = []
                                    for (var si = 0; si < formSourcesModel.count; si++) {
                                        var src = formSourcesModel.get(si)
                                        sources.push({
                                            name: src.name,
                                            url: src.url,
                                            source_type: src.source_type || "web_page"
                                        })
                                    }

                                    var fields = []
                                    for (var i = 0; i < formFieldsModel.count; i++) {
                                        var f = formFieldsModel.get(i)
                                        fields.push({
                                            name: f.name,
                                            selector: f.selector,
                                            field_type: f.fieldType
                                        })
                                    }

                                    var fieldFilters = []
                                    for (var i = 0; i < formFieldsModel.count; i++) {
                                        var f = formFieldsModel.get(i)
                                        if (f.isFilter) {
                                            var opts = null
                                            if (f.filterOptions) {
                                                opts = f.filterOptions.split(",")
                                                var cleanOpts = []
                                                for (var oi = 0; oi < opts.length; oi++) {
                                                    var trimmed = opts[oi].trim()
                                                    if (trimmed) cleanOpts.push(trimmed)
                                                }
                                                opts = cleanOpts
                                            }
                                            fieldFilters.push({
                                                field_name: f.name,
                                                label: f.filterLabel || "Filtrar por " + f.name,
                                                filter_type: f.filterType || "text",
                                                options: opts,
                                                placeholder: "Ingresa " + f.name.toLowerCase(),
                                                required: false,
                                                order: fieldFilters.length
                                            })
                                        }
                                    }

                                    var config = {
                                        sources: sources,
                                        fields: fields,
                                        field_filters: fieldFilters,
                                        delivery: {
                                            emails: formEmails.text ? (function() {
                                            var parts = formEmails.text.split(",")
                                            var result = []
                                            for (var ei = 0; ei < parts.length; ei++) {
                                                var e = parts[ei].trim()
                                                if (e) result.push(e)
                                            }
                                            return result
                                        })() : [],
                                            whatsapp_numbers: [],
                                            generate_web: formGenerateWeb.checked
                                        },
                                        timeout: 30
                                    }

                                    var result = python.save_service(editingServiceId, formServiceName.text, JSON.stringify(config))
                                    var data = parseJson(result)
                                    if (data && data.service_id) {
                                        saveStatus.text = "✅ Servicio guardado: " + data.name
                                        saveStatus.color = success
                                        saveStatus.visible = true
                                        editingServiceId = data.service_id
                                    } else {
                                        saveStatus.text = "❌ Error: " + (data ? data.error : result)
                                        saveStatus.color = error
                                        saveStatus.visible = true
                                    }
                                    saveSpinner.running = false
                                }
                            }
                        }

                        Item { height: 20 }
                    }
                }

            property var refreshServicesList: function() {
                var raw = python.get_services()
                var data = parseJson(raw)
                if (!data) return
                servicesListModel.clear()
                for (var i = 0; i < data.length; i++)
                    servicesListModel.append(data[i])
            }

            function loadServiceForm(serviceId) {
                var raw = python.get_service_detail(serviceId)
                var data = parseJson(raw)
                if (!data || data.error) return

                formServiceName.text = data.name
                formDescription.text = data.description

                // Load multiple sources
                formSourcesModel.clear()
                if (data.sources) {
                    for (var si = 0; si < data.sources.length; si++) {
                        formSourcesModel.append({
                            name: data.sources[si].name,
                            url: data.sources[si].url,
                            source_type: data.sources[si].source_type || "web_page"
                        })
                    }
                }
                formEmails.text = data.delivery ? (data.delivery.emails || []).join(", ") : ""
                formGenerateWeb.checked = data.delivery ? data.delivery.generate_web !== false : true

                formFieldsModel.clear()
                if (data.fields) {
                    for (var i = 0; i < data.fields.length; i++) {
                        var f = data.fields[i]
                        // Find matching filter if any
                        var matchingFilter = null
                        if (data.field_filters) {
                            for (var j = 0; j < data.field_filters.length; j++) {
                                if (data.field_filters[j].field_name === f.name) {
                                    matchingFilter = data.field_filters[j]
                                    break
                                }
                            }
                        }
                        formFieldsModel.append({
                            name: f.name,
                            selector: f.selector,
                            fieldType: f.field_type || f.fieldType,
                            isFilter: matchingFilter !== null,
                            filterType: matchingFilter ? matchingFilter.filter_type : "text",
                            filterOptions: matchingFilter && matchingFilter.options ? matchingFilter.options.join(", ") : "",
                            filterLabel: matchingFilter ? matchingFilter.label : "",
                        })
                    }
                }
            }

            Component.onCompleted: refreshServicesList()
        }

        // ──── PÁGINA 2: EJECUTAR SERVICIO ────────────────────
        Page {
            id: runPage
            background: Rectangle { color: bgSecondary }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Ejecutar Servicio"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: textPrimary
                        Layout.fillWidth: true
                    }
                    Button {
                        text: "↻"
                        onClicked: loadRunServices()
                    }
                }

                // Select service
                Pane {
                    Layout.fillWidth: true
                    padding: 12
                    background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                    RowLayout {
                        anchors.fill: parent
                        spacing: 12

                        Label { text: "Servicio:"; font.weight: Font.Bold; color: textPrimary }

                        ComboBox {
                            id: runServiceCombo
                            model: ListModel { id: runServicesModel }
                            textRole: "display"
                            Layout.fillWidth: true
                            onCurrentIndexChanged: {
                                if (currentIndex >= 0 && runServicesModel.count > 0) {
                                    var svc = runServicesModel.get(currentIndex)
                                    selectedServiceId = svc.service_id
                                    runPage.loadRunFilters(svc.service_id)
                                    runPage.loadRunSources(svc.service_id)
                                }
                            }
                        }
                    }
                }

                // Sources info
                Pane {
                    Layout.fillWidth: true
                    padding: 12
                    visible: selectedServiceId
                    background: Rectangle { color: accentLight; border.color: accent; radius: 12 }

                    ColumnLayout {
                        spacing: 6

                        Label {
                            text: "Sitios que se buscarán"
                            font.weight: Font.Bold
                            color: accent
                            font.pixelSize: 13
                        }

                        ListView {
                            id: runSourcesList
                            Layout.fillWidth: true
                            height: Math.min(80, runSourcesModel.count * 24 + 4)
                            model: ListModel { id: runSourcesModel }
                            clip: true
                            spacing: 2

                            delegate: Label {
                                text: "• " + model.name + " (" + model.url + ")"
                                color: textPrimary
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }
                        }
                    }
                }

                // Filters area
                Pane {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    padding: 16
                    visible: selectedServiceId
                    background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 12

                        Label {
                            text: "Filtros de Búsqueda"
                            font.weight: Font.Bold
                            color: textPrimary
                            font.pixelSize: 14
                        }

                        Label {
                            id: noFiltersLabel
                            text: "Este servicio no tiene filtros configurados. Se ejecutará sin filtros."
                            color: textSecondary
                            font.pixelSize: 12
                            visible: false
                        }

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            contentWidth: availableWidth

                            ColumnLayout {
                                id: filtersContainer
                                width: parent.width
                                spacing: 10

                                // Filters are dynamically added here
                            }
                        }
                    }
                }

                // Execute button
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    BusyIndicator {
                        id: runSpinner
                        running: false
                        Layout.preferredWidth: 24; Layout.preferredHeight: 24
                    }

                    Label {
                        id: runStatus
                        visible: false
                        font.pixelSize: 12
                        Layout.fillWidth: true
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        id: runBtn
                        text: "▶ Ejecutar Búsqueda"
                        enabled: selectedServiceId && !runSpinner.running
                        background: Rectangle {
                            radius: 8
                            color: parent.enabled ? (selectedServiceId ? accent : "#94a3b8") : "#94a3b8"
                        }
                        contentItem: Text {
                            text: parent.text
                            color: "white"
                            font.pixelSize: 14
                        }
                        onClicked: {
                            runSpinner.running = true
                            runStatus.visible = false

                            // Collect filter values
                            var filterValues = {}
                            for (var i = 0; i < filtersContainer.children.length; i++) {
                                var child = filtersContainer.children[i]
                                if (child.filterFieldName) {
                                    if (child.filterType === "range") {
                                        var minField = child.children[1].children[0] // min input
                                        var maxField = child.children[1].children[1] // max input
                                        if (minField.text) filterValues[child.filterFieldName + "_min"] = minField.text
                                        if (maxField.text) filterValues[child.filterFieldName + "_max"] = maxField.text
                                    } else if (child.filterType === "dropdown") {
                                        var combo = child.children[1]
                                        if (combo.currentText && combo.currentText !== "Todos") {
                                            filterValues[child.filterFieldName] = combo.currentText
                                        }
                                    } else if (child.filterType === "checkbox") {
                                        var cb = child.children[1]
                                        filterValues[child.filterFieldName] = cb.checked ? "true" : "false"
                                    } else {
                                        // text / date_range
                                        var input = child.children[1]
                                        if (input.text) filterValues[child.filterFieldName] = input.text
                                    }
                                }
                            }

                            var result = python.run_service(selectedServiceId, JSON.stringify(filterValues))
                            var data = parseJson(result)
                            if (data && data.operation_id) {
                                var srcList = data.sources ? data.sources.join(", ") : ""
                                runStatus.text = "✅ Completado — " + data.total_found + " items (" + srcList + ")"
                                runStatus.color = success
                                runStatus.visible = true
                                lastRunOpId = data.operation_id
                            } else {
                                runStatus.text = "❌ " + (data ? data.error : result)
                                runStatus.color = error
                                runStatus.visible = true
                            }
                            runSpinner.running = false
                        }
                    }
                }
            }

            property var loadRunServices: function() {
                var raw = python.get_services()
                var data = parseJson(raw)
                if (!data) return
                runServicesModel.clear()
                for (var i = 0; i < data.length; i++) {
                    runServicesModel.append({
                    display: data[i].name + " (" + data[i].sources_count + " fuentes)",
                    service_id: data[i].service_id
                    })
                }
                if (runServicesModel.count > 0) {
                    // Select matching or first
                    if (selectedServiceId) {
                        for (var i = 0; i < runServicesModel.count; i++) {
                            if (runServicesModel.get(i).service_id === selectedServiceId) {
                                runServiceCombo.currentIndex = i
                                return
                            }
                        }
                    }
                    runServiceCombo.currentIndex = 0
                }
            }

            property var loadRunSources: function(serviceId) {
                runSourcesModel.clear()
                var raw = python.get_service_detail(serviceId)
                var data = parseJson(raw)
                if (!data || data.error) return
                if (data.sources) {
                    for (var si = 0; si < data.sources.length; si++) {
                        runSourcesModel.append({
                            name: data.sources[si].name,
                            url: data.sources[si].url
                        })
                    }
                }
            }

            property var loadRunFilters: function(serviceId) {
                // Clear existing filters
                while (filtersContainer.children.length > 0) {
                    var child = filtersContainer.children[filtersContainer.children.length - 1]
                    child.destroy()
                }

                var raw = python.get_service_detail(serviceId)
                var data = parseJson(raw)
                if (!data || data.error) return

                var filters = data.field_filters || []
                if (filters.length === 0) {
                    noFiltersLabel.visible = true
                    return
                }
                noFiltersLabel.visible = false

                for (var i = 0; i < filters.length; i++) {
                    var ff = filters[i]
                    var comp

                    if (ff.filter_type === "range") {
                        // Range filter: min / max inputs
                        comp = Qt.createQmlObject('
                            import QtQuick 2.15; import QtQuick.Controls 2.15; import QtQuick.Layouts 1.15
                            ColumnLayout {
                                property string filterFieldName: "' + ff.field_name + '"
                                property string filterType: "range"
                                spacing: 4
                                Label { text: "' + ff.label.replace(/'/g, "\\'") + '"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 12 }
                                RowLayout { spacing: 8
                                    TextField { placeholderText: "Mínimo"; Layout.fillWidth: true }
                                    Label { text: "—"; color: textSecondary }
                                    TextField { placeholderText: "Máximo"; Layout.fillWidth: true }
                                }
                            }
                        ', filtersContainer)
                    } else if (ff.filter_type === "dropdown") {
                        var opts = ff.options || []
                        var allOpts = ["Todos"].concat(opts)
                        var optsStr = JSON.stringify(allOpts)
                        comp = Qt.createQmlObject('
                            import QtQuick 2.15; import QtQuick.Controls 2.15; import QtQuick.Layouts 1.15
                            ColumnLayout {
                                property string filterFieldName: "' + ff.field_name + '"
                                property string filterType: "dropdown"
                                spacing: 4
                                Label { text: "' + ff.label.replace(/'/g, "\\'") + '"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 12 }
                                ComboBox {
                                    model: ' + optsStr + '
                                    Layout.fillWidth: true
                                }
                            }
                        ', filtersContainer)
                    } else if (ff.filter_type === "checkbox") {
                        comp = Qt.createQmlObject('
                            import QtQuick 2.15; import QtQuick.Controls 2.15; import QtQuick.Layouts 1.15
                            ColumnLayout {
                                property string filterFieldName: "' + ff.field_name + '"
                                property string filterType: "checkbox"
                                spacing: 4
                                CheckBox {
                                    text: "' + ff.label.replace(/'/g, "\\'") + '"
                                    font.weight: Font.Bold; font.pixelSize: 12
                                }
                            }
                        ', filtersContainer)
                    } else {
                        // text or date_range
                        var ph = ff.placeholder || "Ingresa " + ff.field_name
                        comp = Qt.createQmlObject('
                            import QtQuick 2.15; import QtQuick.Controls 2.15; import QtQuick.Layouts 1.15
                            ColumnLayout {
                                property string filterFieldName: "' + ff.field_name + '"
                                property string filterType: "' + ff.filter_type + '"
                                spacing: 4
                                Label { text: "' + ff.label.replace(/'/g, "\\'") + '"; font.weight: Font.Bold; color: textPrimary; font.pixelSize: 12 }
                                TextField { placeholderText: "' + ph.replace(/'/g, "\\'") + '"; Layout.fillWidth: true }
                            }
                        ', filtersContainer)
                    }
                }
            }

            Component.onCompleted: loadRunServices()
        }

        // ──── PÁGINA 3: RESULTADOS ───────────────────────────
        Page {
            id: resultsPage
            background: Rectangle { color: bgSecondary }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Resultados"
                        font.pixelSize: 22
                        font.weight: Font.Bold
                        color: textPrimary
                        Layout.fillWidth: true
                    }
                    Button { text: "↻"; onClicked: refreshResults() }
                }

                // Op selector
                Pane {
                    Layout.fillWidth: true
                    padding: 12
                    background: Rectangle { color: bgCard; border.color: border; radius: 12 }

                    RowLayout {
                        anchors.fill: parent
                        spacing: 12
                        Label { text: "Operación:"; font.weight: Font.Bold; color: textPrimary }

                        ComboBox {
                            id: resultsOpCombo
                            model: ListModel { id: resultsOpsModel }
                            textRole: "display"
                            Layout.fillWidth: true
                            onCurrentIndexChanged: {
                                if (currentIndex >= 0 && resultsOpsModel.count > 0)
                                    loadOpResults(resultsOpsModel.get(currentIndex).op_id)
                            }
                        }
                    }
                }

                // Results display
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgCard
                    border.color: border
                    clip: true

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        Label {
                            id: resultsSummary
                            text: "Selecciona una operación para ver resultados."
                            color: textSecondary
                            font.pixelSize: 13
                            visible: resultsItemsModel.count === 0
                        }

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            contentWidth: availableWidth

                            ListView {
                                id: resultsListView
                                anchors.fill: parent
                                model: ListModel { id: resultsItemsModel }
                                spacing: 6
                                clip: true

                                delegate: Rectangle {
                                    width: parent.width
                                    height: resultsItemContent.height + 24
                                    radius: 8
                                    color: bgSecondary
                                    border.color: border

                                    ColumnLayout {
                                        id: resultsItemContent
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 4

                                        Repeater {
                                            model: {
                                                var keys = Object.keys(model.data)
                                                return keys.map(function(k) {
                                                    return {key: k, value: typeof model.data[k] === "string" ? model.data[k] : JSON.stringify(model.data[k])}
                                                })
                                            }
                                            delegate: Label {
                                                text: "<b>" + model.key + ":</b> " + model.value
                                                font.pixelSize: 12
                                                color: textPrimary
                                                wrapMode: Text.WordWrap
                                                maximumLineCount: 3
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        // Item count
                        Label {
                            id: resultsCount
                            font.pixelSize: 11
                            color: textSecondary
                            visible: resultsItemsModel.count > 0
                        }
                    }
                }
            }

            function refreshResults() {
                var raw = python.get_history()
                var data = parseJson(raw)
                if (!data) return
                resultsOpsModel.clear()
                for (var i = 0; i < data.length; i++) {
                    resultsOpsModel.append({
                        display: data[i].operation_id + " — " + data[i].source,
                        op_id: data[i].operation_id
                    })
                }
                if (resultsOpsModel.count > 0) {
                    // Auto-select last run
                    if (lastRunOpId) {
                        for (var i = 0; i < resultsOpsModel.count; i++) {
                            if (resultsOpsModel.get(i).op_id === lastRunOpId) {
                                resultsOpCombo.currentIndex = i
                                return
                            }
                        }
                    }
                    resultsOpCombo.currentIndex = 0
                }
            }

            Component.onCompleted: {
                window._refreshResults = refreshResults
            }

            function loadOpResults(opId) {
                var raw = python.get_results(opId)
                var data = parseJson(raw)
                if (!data || data.error) {
                    resultsSummary.text = data ? data.error : "Error al cargar"
                    resultsSummary.visible = true
                    return
                }
                resultsSummary.visible = false
                resultsItemsModel.clear()
                if (data.items) {
                    for (var i = 0; i < data.items.length; i++)
                        resultsItemsModel.append(data.items[i])
                }
                resultsCount.text = resultsItemsModel.count + " resultados · " + (data.elapsed_seconds || "?") + "s"
            }
        }

        // ──── PÁGINA 4: HISTORIAL ────────────────────────────
        Page {
            id: historyPage
            background: Rectangle { color: bgSecondary }

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
                    Button { text: "↻"; onClicked: refreshHistory() }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgCard
                    border.color: border
                    clip: true

                    ListView {
                        id: historyList
                        anchors.fill: parent
                        anchors.margins: 8
                        model: ListModel { id: historyModel }
                        spacing: 4
                        clip: true

                        delegate: Rectangle {
                            width: parent.width
                            height: 52
                            radius: 8
                            color: bgSecondary
                            border.color: border

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
                                    width: 8; height: 8; radius: 4
                                    color: model.status === "completed" ? success :
                                          model.status === "completed_with_errors" ? warning : error
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    var raw = python.get_operation_detail(model.operation_id)
                                    var data = parseJson(raw)
                                    if (data && !data.error) {
                                        historyDetail.text = JSON.stringify(data, null, 2)
                                        detailDrawer.open()
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

            // Detail drawer
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

            function refreshHistory() {
                var raw = python.get_history()
                var data = parseJson(raw)
                if (!data) return
                historyModel.clear()
                for (var i = 0; i < data.length; i++)
                    historyModel.append(data[i])
            }

            Component.onCompleted: {
                refreshHistory()
                window._refreshHistory = refreshHistory
            }
        }
    }
}
