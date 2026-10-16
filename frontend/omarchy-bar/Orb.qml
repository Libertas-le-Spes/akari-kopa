import QtQuick
import qs.Commons

Rectangle {
  property var look

  width: Style.space(10)
  height: width
  radius: width / 2
  opacity: look && look.faded ? 0.45 : 1
  color: !look || look.ring ? "transparent" : look.colour
  border.width: Math.max(1, Style.space(2))
  border.color: look ? look.colour : "transparent"
}
