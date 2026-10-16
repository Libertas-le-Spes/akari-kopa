import QtQuick
import qs.Commons
import qs.Ui

WidgetButton {
  id: button

  property var look
  property bool vertical: false
  property int barSize: 0

  signal toggled()
  signal refreshed()

  hasVisualContent: true
  fixedWidth: vertical ? barSize : Style.space(16)
  fixedHeight: vertical ? Style.space(16) : barSize
  onPressed: function(pressed) {
    if (pressed === Qt.LeftButton) button.toggled()
    else if (pressed === Qt.MiddleButton) button.refreshed()
  }

  Orb {
    anchors.centerIn: parent
    look: button.look
  }
}
