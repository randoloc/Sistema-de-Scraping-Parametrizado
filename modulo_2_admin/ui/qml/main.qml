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

    // Colores
    readonly property color bgPrimary: "#ffffff"
    readonly property color bgSecondary: "#f8fafc"
    readonly property color textPrimary: "#1a1a2e"
    readonly property color textSecondary: "#64748b"
    readonly property color accent: "#2563eb"
    readonly property color success: "#22c55e"
    readonly property color error: "#ef4444"

    header: ToolBar {
        background: Rectangle {
            color: "#1a1a2e"
        }
        RowLayout {
            anchors.fill: parent
            spacing: 8
            padding: 8

            Label {
                text: "🕸️ ScrapperGenérico"
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
                text: "Entregas"
                highlighted: currentView === "delivery"
                onClicked: currentView = "delivery"
                contentItem: Text {
                    text: parent.text
                    color: currentView === "delivery" ? accent : "white"
                    font.pixelSize: 13
                }
            }
            ToolButton {
                text: "Historial"
                highlighted: currentView === "history"
                onClicked: currentView = "history"
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
            if (currentView === "scrape") return 1;
            if (currentView === "delivery") return 2;
            if (currentView === "history") return 3;
            return 0;
        }

        // Página 0: Dashboard
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
                                text: "0"
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
                                text: "—"
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

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 12
                        Label {
                            text: "🤖"
                            font.pixelSize: 40
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Bienvenido a ScrapperGenérico"
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            color: textPrimary
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Configura tu primer scraper o revisa los resultados recientes."
                            font.pixelSize: 13
                            color: textSecondary
                            Layout.alignment: Qt.AlignHCenter
                            wrapMode: Text.WordWrap
                        }
                        Button {
                            text: "Nuevo Scraper"
                            Layout.alignment: Qt.AlignHCenter
                            onClicked: currentView = "scrape"
                            background: Rectangle {
                                radius: 8
                                color: accent
                            }
                            contentItem: Text {
                                text: parent.text
                                color: "white"
                                font.pixelSize: 14
                            }
                        }
                    }
                }
            }
        }

        // Página 1: Nuevo Scraper
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

                // Conexión
                Rectangle {
                    Layout.fillWidth: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"
                    padding: 16

                    ColumnLayout {
                        spacing: 12
                        width: parent.width

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
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"
                    padding: 16

                    ColumnLayout {
                        spacing: 8
                        width: parent.width

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
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 8
                                    Label { text: model.name; Layout.preferredWidth: 120 }
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
                                text: "+"
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

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "Probar Conexión"
                        flat: true
                    }
                    Button {
                        text: "▶ Ejecutar Scraping"
                        background: Rectangle {
                            radius: 8
                            color: accent
                        }
                        contentItem: Text {
                            text: parent.text
                            color: "white"
                            font.pixelSize: 14
                        }
                    }
                }
            }
        }

        // Página 2: Entregas
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

                // Email
                Rectangle {
                    Layout.fillWidth: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"
                    padding: 16

                    ColumnLayout {
                        spacing: 8
                        width: parent.width
                        Label { text: "📧 Correo Electrónico"; font.weight: Font.Bold; color: textPrimary }
                        RowLayout {
                            spacing: 8
                            TextField {
                                placeholderText: "email@ejemplo.com"
                                Layout.fillWidth: true
                            }
                            Button { text: "+ Agregar" }
                        }
                        Label { text: "Sin destinatarios configurados."; color: textSecondary; font.pixelSize: 12 }
                    }
                }

                // WhatsApp
                Rectangle {
                    Layout.fillWidth: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"
                    padding: 16

                    ColumnLayout {
                        spacing: 8
                        width: parent.width
                        Label { text: "💬 WhatsApp"; font.weight: Font.Bold; color: textPrimary }
                        RowLayout {
                            spacing: 8
                            TextField {
                                placeholderText: "521234567890"
                                Layout.fillWidth: true
                            }
                            Button { text: "+ Agregar" }
                            Button {
                                text: "Enviar Activación"
                                flat: true
                                enabled: false
                            }
                        }
                        Label {
                            text: "Los números deben activarse vía email (link wa.me) para recibir resultados gratis."
                            color: textSecondary; font.pixelSize: 11; wrapMode: Text.WordWrap
                        }
                    }
                }

                // Web
                Rectangle {
                    Layout.fillWidth: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"
                    padding: 16

                    RowLayout {
                        spacing: 12
                        width: parent.width
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: "🌐 Página Web"; font.weight: Font.Bold; color: textPrimary }
                            Label {
                                text: "Se genera automáticamente una página con los resultados."
                                color: textSecondary; font.pixelSize: 12; wrapMode: Text.WordWrap
                            }
                        }
                        Switch {
                            checked: true
                        }
                    }
                }
            }
        }

        // Página 3: Historial
        Rectangle {
            color: bgSecondary
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Label {
                    text: "Historial de Operaciones"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: textPrimary
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 12
                    color: bgPrimary
                    border.color: "#e2e8f0"

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 8
                        Label { text: "📋"; font.pixelSize: 36; Layout.alignment: Qt.AlignHCenter }
                        Label {
                            text: "Sin operaciones aún"
                            color: textSecondary
                            font.pixelSize: 14
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Las operaciones completadas aparecerán aquí."
                            color: textSecondary
                            font.pixelSize: 12
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
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
                text: "Servicio: " + (python.connected ? "🟢 Conectado" : "🔴 Desconectado")
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
