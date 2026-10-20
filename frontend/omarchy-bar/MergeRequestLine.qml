import QtQuick
import qs.Commons
import qs.Ui

Item {
  id: line

  property var bar
  property var mergeRequest
  property bool current: false

  signal chosen()
  signal pointedAt()

  height: info.implicitHeight + Style.space(6)

  CursorSurface {
    anchors.fill: parent
    foreground: line.bar.foreground
    hasCursor: line.current
  }

  Row {
    anchors.verticalCenter: parent.verticalCenter
    x: Style.space(4)
    width: parent.width - Style.space(8)
    spacing: Style.space(8)

    Orb {
      anchors.verticalCenter: parent.verticalCenter
      look: line.mergeRequest.look
    }

    Column {
      id: info
      width: parent.width - Style.space(18)

      Text {
        textFormat: Text.PlainText
        text: line.mergeRequest.summary
        color: line.bar.foreground
        font.family: line.bar.fontFamily
        font.pixelSize: Style.font.body
        font.bold: true
        elide: Text.ElideRight
        width: parent.width
      }

      Text {
        textFormat: Text.PlainText
        text: line.mergeRequest.title + "  ·  " + line.mergeRequest.details
        color: Qt.darker(line.bar.foreground, 1.4)
        font.family: line.bar.fontFamily
        font.pixelSize: Style.font.caption
        elide: Text.ElideRight
        width: parent.width
      }
    }
  }

  MouseArea {
    id: hover
    anchors.fill: parent
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    onContainsMouseChanged: if (containsMouse) line.pointedAt()
    onClicked: line.chosen()
  }
}
