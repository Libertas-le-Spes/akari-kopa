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

  readonly property var mergeRequests: board.groups.reduce(function(all, group) { return group.services.reduce(function(found, service) { return found.concat(service.merge_requests) }, all) }, [])
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

  MergeRequestList {
    anchorItem: root
    owner: root
    bar: root.bar
    open: root.popupOpen
    board: root.board
    mergeRequests: root.mergeRequests
    onChosen: function(mergeRequest) { root.openInBrowser(mergeRequest) }
  }
}
