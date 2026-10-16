import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "kayu.akari-kopa"

  property var board: ({ groups: [], not_updated: [], not_updated_summary: "", not_updated_look: null })
  property bool popupOpen: false

  readonly property var mergeRequests: board.groups.reduce(function(all, group) { return all.concat(group.merge_requests) }, [])
  readonly property bool stale: board.not_updated.length > 0

  function couldNotRun(reason) {
    board = Object.assign({}, board, {
      not_updated: ["akari-kopa: " + reason],
      not_updated_summary: "Not updated: akari-kopa"
    })
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

  function openInBrowser(mergeRequest) {
    popupOpen = false
    Qt.openUrlExternally(mergeRequest.url)
  }

  visible: mergeRequests.length > 0 || stale
  implicitWidth: vertical ? barSize : orbs.implicitWidth + Style.space(8)
  implicitHeight: vertical ? orbs.implicitHeight + Style.space(8) : barSize

  IpcHandler {
    target: "kayu.akari-kopa"

    function refresh(): void { root.refresh() }
    function toggle(): void { root.broadcast("toggleOnFocusedScreen") }
  }

  Process {
    id: fetch
    command: [decodeURIComponent(Qt.resolvedUrl("../../backend/bin/akari-kopa").toString().replace(/^file:\/\//, ""))]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          root.board = JSON.parse(text)
        } catch (error) {
          root.couldNotRun(String(error))
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
    columns: root.vertical ? 1 : Math.max(1, root.mergeRequests.length)
    spacing: Style.space(2)

    OrbButton {
      visible: root.mergeRequests.length === 0 && root.stale
      bar: root.bar
      vertical: root.vertical
      barSize: root.barSize
      look: root.board.not_updated_look
      tooltipText: root.board.not_updated_summary
      onToggled: root.popupOpen = !root.popupOpen
      onRefreshed: root.refresh()
    }

    Repeater {
      model: root.mergeRequests

      OrbButton {
        required property var modelData
        bar: root.bar
        vertical: root.vertical
        barSize: root.barSize
        look: modelData.look
        tooltipText: modelData.summary
        onToggled: root.popupOpen = !root.popupOpen
        onRefreshed: root.refresh()
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
        model: root.board.groups

        Column {
          required property var modelData
          width: sections.width
          spacing: Style.space(4)

          Heading {
            bar: root.bar
            text: modelData.heading
          }

          Repeater {
            model: modelData.merge_requests

            MergeRequestLine {
              required property var modelData
              width: sections.width
              bar: root.bar
              mergeRequest: modelData
              onChosen: root.openInBrowser(modelData)
            }
          }
        }
      }

      Column {
        width: sections.width
        spacing: Style.space(4)
        visible: root.stale

        Heading {
          bar: root.bar
          text: "Not updated"
        }

        Repeater {
          model: root.board.not_updated

          Text {
            required property var modelData
            textFormat: Text.PlainText
            text: modelData
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
