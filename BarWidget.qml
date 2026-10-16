import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "kayu.merge-requests"

  readonly property var orbColors: ({
    mine: { passing: "#3fb950", idle: "#3fb950", pending: "#3fb950", failing: "#f85149", comments: "#a371f7" },
    review: { passing: "#4c8dff", idle: "#4c8dff", pending: "#4c8dff", failing: "#e3b341", comments: "#4c8dff" }
  })

  readonly property var orbWords: ({
    passing: "passing", idle: "no pipeline", pending: "running", failing: "failing", comments: "comments to answer"
  })

  property var mergeRequests: []
  property var failures: []
  readonly property bool stale: failures.length > 0
  property bool popupOpen: false

  readonly property var mine: mergeRequests.filter(function(mr) { return mr.role === "mine" })
  readonly property var reviewing: mergeRequests.filter(function(mr) { return mr.role === "review" })

  function orbColor(mr) {
    return orbColors[mr.role][mr.orb]
  }

  function orbWord(mr) {
    return orbWords[mr.orb]
  }

  function summary(mr) {
    return mr.reference + " · " + mr.author
  }

  function apply(listing) {
    var failed = listing.failed.map(function(failure) { return failure.provider })
    var kept = mergeRequests.filter(function(mr) { return failed.indexOf(mr.provider) !== -1 })
    mergeRequests = listing.mergeRequests.concat(kept)
    failures = listing.failed
  }

  function failureSummary() {
    return "Not updated: " + failures.map(function(failure) { return failure.provider }).join(", ")
  }

  function refresh() {
    if (!fetch.running) fetch.running = true
  }

  function close() { popupOpen = false }

  function toggleOnFocusedScreen() {
    var screen = root.QsWindow.window ? root.QsWindow.window.screen : null
    var focused = Hyprland.focusedMonitor
    if (screen && focused && screen.name === focused.name) popupOpen = !popupOpen
  }

  function openInBrowser(mr) {
    popupOpen = false
    Qt.openUrlExternally(mr.url)
  }

  visible: mergeRequests.length > 0 || failures.length > 0
  implicitWidth: vertical ? barSize : orbs.implicitWidth + Style.space(8)
  implicitHeight: vertical ? orbs.implicitHeight + Style.space(8) : barSize

  IpcHandler {
    target: "kayu.merge-requests"

    function refresh(): void { root.refresh() }
    function toggle(): void { root.broadcast("toggleOnFocusedScreen") }
  }

  Process {
    id: fetch
    command: [decodeURIComponent(Qt.resolvedUrl("merge-requests").toString().replace(/^file:\/\//, ""))]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          root.apply(JSON.parse(text))
        } catch (error) {
          root.failures = [{ provider: "merge-requests", reason: String(error) }]
        }
      }
    }
  }

  Timer {
    interval: Math.max(15, Number(root.setting("intervalSeconds", 60))) * 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  Grid {
    id: orbs
    anchors.centerIn: parent
    columns: root.vertical ? 1 : root.mergeRequests.length
    spacing: Style.space(2)

    WidgetButton {
      visible: root.mergeRequests.length === 0 && root.stale
      bar: root.bar
      hasVisualContent: true
      dimmed: true
      fixedWidth: root.vertical ? root.barSize : Style.space(16)
      fixedHeight: root.vertical ? Style.space(16) : root.barSize
      tooltipText: root.failureSummary()
      onPressed: function(button) {
        if (button === Qt.LeftButton) root.popupOpen = !root.popupOpen
        else if (button === Qt.MiddleButton) root.refresh()
      }

      Rectangle {
        anchors.centerIn: parent
        width: Style.space(10)
        height: width
        radius: width / 2
        color: "transparent"
        border.width: Math.max(1, Style.space(2))
        border.color: root.bar ? root.bar.foreground : "white"
      }
    }

    Repeater {
      model: root.mergeRequests

      WidgetButton {
        required property var modelData
        bar: root.bar
        hasVisualContent: true
        dimmed: root.stale
        fixedWidth: root.vertical ? root.barSize : Style.space(16)
        fixedHeight: root.vertical ? Style.space(16) : root.barSize
        tooltipText: root.summary(modelData)
        onPressed: function(button) {
          if (button === Qt.LeftButton) root.popupOpen = !root.popupOpen
          else if (button === Qt.MiddleButton) root.refresh()
        }

        Rectangle {
          anchors.centerIn: parent
          width: Style.space(10)
          height: width
          radius: width / 2
          color: modelData.orb === "pending" ? "transparent" : root.orbColor(modelData)
          border.width: Math.max(1, Style.space(2))
          border.color: root.orbColor(modelData)
        }
      }
    }
  }

  PopupCard {
    id: popup
    anchorItem: root
    bar: root.bar
    owner: root
    open: root.popupOpen
    contentWidth: popup.fittedContentWidth(Style.space(340))
    contentHeight: popup.fittedContentHeight(sections.implicitHeight)

    Column {
      id: sections
      anchors.fill: parent
      spacing: Style.space(12)

      Repeater {
        model: [
          { heading: "My merge requests", items: root.mine },
          { heading: "Reviewing", items: root.reviewing }
        ]

        Column {
          required property var modelData
          width: sections.width
          spacing: Style.space(4)
          visible: modelData.items.length > 0

          Text {
            textFormat: Text.PlainText
            text: modelData.heading
            color: Qt.darker(root.bar.foreground, 1.3)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            font.capitalization: Font.AllUppercase
          }

          Repeater {
            model: modelData.items

            Item {
              id: line
              required property var modelData
              width: sections.width
              height: info.implicitHeight + Style.space(6)

              Rectangle {
                anchors.fill: parent
                radius: Style.space(4)
                color: lineHover.containsMouse ? Style.hoverFill : "transparent"
              }

              Row {
                anchors.verticalCenter: parent.verticalCenter
                x: Style.space(4)
                width: parent.width - Style.space(8)
                spacing: Style.space(8)

                Rectangle {
                  anchors.verticalCenter: parent.verticalCenter
                  width: Style.space(10)
                  height: width
                  radius: width / 2
                  color: line.modelData.orb === "pending" ? "transparent" : root.orbColor(line.modelData)
                  border.width: Math.max(1, Style.space(2))
                  border.color: root.orbColor(line.modelData)
                }

                Column {
                  id: info
                  width: parent.width - Style.space(18)

                  Text {
                    textFormat: Text.PlainText
                    text: root.summary(line.modelData)
                    color: root.bar.foreground
                    font.family: root.bar.fontFamily
                    font.pixelSize: Style.font.body
                    font.bold: true
                    elide: Text.ElideRight
                    width: parent.width
                  }

                  Text {
                    textFormat: Text.PlainText
                    text: line.modelData.title + "  ·  " + line.modelData.project + "  ·  " + root.orbWord(line.modelData)
                    color: Qt.darker(root.bar.foreground, 1.4)
                    font.family: root.bar.fontFamily
                    font.pixelSize: Style.font.caption
                    elide: Text.ElideRight
                    width: parent.width
                  }
                }
              }

              MouseArea {
                id: lineHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.openInBrowser(line.modelData)
              }
            }
          }
        }
      }

      Column {
        width: sections.width
        spacing: Style.space(4)
        visible: root.stale

        Text {
          textFormat: Text.PlainText
          text: "Not updated"
          color: Qt.darker(root.bar.foreground, 1.3)
          font.family: root.bar.fontFamily
          font.pixelSize: Style.font.caption
          font.capitalization: Font.AllUppercase
        }

        Repeater {
          model: root.failures

          Text {
            required property var modelData
            textFormat: Text.PlainText
            text: modelData.provider + ": " + modelData.reason
            color: Qt.darker(root.bar.foreground, 1.4)
            font.family: root.bar.fontFamily
            font.pixelSize: Style.font.caption
            wrapMode: Text.Wrap
            width: sections.width
          }
        }
      }
    }
  }
}
