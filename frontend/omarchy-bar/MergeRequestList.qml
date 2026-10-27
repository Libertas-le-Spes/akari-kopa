import QtQuick
import qs.Commons
import qs.Ui

KeyboardPanel {
  id: list

  property var board
  property var mergeRequests: []
  property int current: -1

  signal chosen(var mergeRequest)

  function step(by) {
    var count = mergeRequests.length
    if (count === 0 || by === 0) return
    if (current < 0) current = by > 0 ? 0 : count - 1
    else current = (current + by + count) % count
  }

  function chooseCurrent() {
    if (current >= 0 && current < mergeRequests.length) chosen(mergeRequests[current])
  }

  onOpenChanged: if (open) current = -1
  focusTarget: keys
  contentWidth: list.fittedContentWidth(Style.space(340))
  contentHeight: list.fittedContentHeight(sections.implicitHeight)

  PanelKeyCatcher {
    id: keys
    anchors.fill: parent
    onMoveRequested: function(across, down) { list.step(down) }
    onActivateRequested: list.chooseCurrent()
    onCloseRequested: list.close()

    Column {
      id: sections
      anchors.fill: parent
      spacing: Style.space(12)

      Repeater {
        model: list.board.groups

        Column {
          required property var modelData
          width: sections.width
          spacing: Style.space(4)

          Heading {
            bar: list.bar
            text: modelData.heading
          }

          Repeater {
            model: modelData.services

            Column {
              required property var modelData
              width: sections.width
              spacing: Style.space(2)

              ServiceHeading {
                bar: list.bar
                text: modelData.heading
              }

              Repeater {
                model: modelData.merge_requests

                MergeRequestLine {
                  required property var modelData
                  readonly property int position: list.mergeRequests.findIndex(function(other) { return other.key === modelData.key })
                  width: sections.width
                  bar: list.bar
                  mergeRequest: modelData
                  current: list.current === position
                  onPointedAt: list.current = position
                  onChosen: list.chosen(modelData)
                }
              }
            }
          }
        }
      }

      Column {
        width: sections.width
        spacing: Style.space(4)
        visible: list.board.not_updated.length > 0

        Heading {
          bar: list.bar
          text: "Not updated"
        }

        Repeater {
          model: list.board.not_updated

          Text {
            required property var modelData
            textFormat: Text.PlainText
            text: modelData
            color: Qt.darker(list.bar.foreground, 1.4)
            font.family: list.bar.fontFamily
            font.pixelSize: Style.font.caption
            wrapMode: Text.Wrap
            width: sections.width
          }
        }
      }
    }
  }
}
