import QtQuick
import qs.Commons

Text {
  property var bar

  textFormat: Text.PlainText
  color: Qt.darker(bar.foreground, 1.3)
  font.family: bar.fontFamily
  font.pixelSize: Style.font.caption
  font.capitalization: Font.AllUppercase
}
