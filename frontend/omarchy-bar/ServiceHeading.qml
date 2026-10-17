import QtQuick
import qs.Commons

Text {
  property var bar

  textFormat: Text.PlainText
  color: bar.foreground
  font.family: bar.fontFamily
  font.pixelSize: Style.font.caption
  font.bold: true
  topPadding: Style.space(2)
}
