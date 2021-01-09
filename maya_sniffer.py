import os
import time
import argparse
import functools

from PySide2 import QtCore, QtGui, QtWidgets
import shiboken2

maya_window = None
dpi = None

color_template = """\
Square[nodeType=%(nodeType)s] { background: %(color)s; }
Square[nodeType=%(nodeType)s]:hover { background: %(hover)s; }
Square[nodeType=%(nodeType)s]:focus { background: %(focus)s; }
"""

colors = {
    "transform": "#75BCE1",
    "nurbsCurve": "#EDD377",
    "mesh": "#C0935E",
    "joint": "#91DC73",
    "camera": "#DD6A6A",
    "skinCluster": "#E17839",
    "dagPose": "#E14530",

    "animCurve": "#D474EC",
    "animCurveTA": "#D474EC",
    "animCurveTL": "#D474EC",
    "animCurveTT": "#D474EC",
    "animCurveTU": "#D474EC",
    "animCurveUA": "#D474EC",
    "animCurveUL": "#D474EC",
    "animCurveUT": "#D474EC",
    "animCurveUU": "#D474EC",
}

colors = "\n".join(
    color_template % {
        "nodeType": node_type,
        "color": color,
        "hover": QtGui.QColor(color).lighter(110).name(),
        "focus": QtGui.QColor(color).lighter(150).name(),
    }
    for node_type, color in colors.items()
)

stylesheet = """
QSpinBox {
    min-width: 50px;
}

Square {
    color: #111;
}

Square {
    background: #999;
    border: 1px solid #333;
    margin: 2px;
}
Square:hover { background: #aaa; }

""" + colors


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        start = time.time()

        try:
            return func(*args, **kwargs)

        finally:
            end = time.time()
            duration = end - start

            if duration > 0.1:
                print("%s took %.2f seconds" % (name, duration))

    return wrapper


def scale_stylesheet(style):
    """Replace any mention of <num>px with scaled version

    This way, you can still use px without worrying about what
    it will look like at HDPI resolution.

    """

    output = []
    for line in style.splitlines():
        line = line.rstrip()
        if line.endswith("px;"):
            key, value = line.rsplit(" ", 1)
            value = px(int(value[:-3]))
            line = "%s %dpx;" % (key, value)
        output += [line]
    return "\n".join(output)


def px(value):
    """Return a scaled value, for HDPI resolutions"""

    global dpi

    if not dpi:
        # We can get system DPI from a window handle,
        # but I haven't figured out how to get a window handle
        # without first making a widget. So here we make one
        # as invisibly as we can, as an invisible tooltip.
        # This doesn't create a taskbar icon nor changes focus
        # and in fact *should* happen without any noticeable effect
        # to the user. Welcome to provide a less naughty alternative
        any_widget = QtWidgets.QWidget()
        any_widget.setWindowFlags(QtCore.Qt.ToolTip)
        any_widget.show()
        window = any_widget.windowHandle()

        # E.g. 1.5 or 2.0
        scale = window.screen().logicalDotsPerInch() / 96.0

        # Store for later
        dpi = scale

    return value * dpi


def MayaWindow():
    """Fetch Maya window"""
    global maya_window

    # This will never change during the lifetime of this Python session
    if not maya_window:
        from maya.OpenMayaUI import MQtUtil
        ptr = MQtUtil.mainWindow()

        try:
            # Backwards compatibility with Python 2.x
            long
        except NameError:
            long = int

        if ptr is not None:
            maya_window = shiboken2.wrapInstance(
                long(ptr), QtWidgets.QMainWindow
            )

        else:
            # Running standalone
            return None

    return maya_window


class Parser(object):
    def __init__(self):
        self._current_node = None
        self._current_node_type = None

        self.result = {}

    def on_create(self, line):
        comp = line.split()
        index = comp.index("-n")
        node_type = comp[1]
        name = comp[index + 1]
        name = name.replace('"', "")

        self._current_node = name
        self._current_node_type = node_type

    def on_setattr(self, line):
        nodes = self.result["nodes"]

        if self._current_node not in nodes:
            nodes[self._current_node] = {
                "nodeType": self._current_node_type,
                "lines": 0,
                "characters": 0,
            }

        nodes[self._current_node]["lines"] += 1
        nodes[self._current_node]["characters"] += len(line)

    @timer
    def read(self, fname):
        with open(fname) as f:
            return f.readlines()

    @timer
    def parse(self, fname):
        lines = self.read(fname)

        self.result = {
            "fname": fname,
            "filesize": os.path.getsize(fname),
            "lineCount": len(lines),
            "totalCharacterCount": sum([len(line) for line in lines]),
            "nodes": {},
        }

        for line in lines:
            # Once node creation completes, Maya
            # selects and modifies the time1 node
            if line.startswith("select"):
                break

            # In case it doesn't, then connections are next
            if line.startswith("connectAttr"):
                break

            # Remove padding and newline
            line = line.strip().rstrip(" ;\n")

            if line.startswith("createNode"):
                self.on_create(line)

            elif line.startswith("setAttr"):
                self.on_setattr(line)

            elif self._current_node is not None:
                self.on_setattr(line)


class Square(QtWidgets.QLabel):
    pass


class Widget(QtWidgets.QDialog):
    clicked = QtCore.Signal(str)  # node path

    def __init__(self, data, opts=None, title=None, parent=None):
        super(Widget, self).__init__(parent=parent)
        self.setWindowTitle(title or data["fname"])
        self.setMinimumHeight(px(100))

        panels = {
            "header": QtWidgets.QWidget(self),
            "body": QtWidgets.QWidget(self),
        }

        widgets = {
            "filename": QtWidgets.QPushButton(),
            "filesize": QtWidgets.QLabel(),
            "characterCount": QtWidgets.QLabel(),
            "nodeCount": QtWidgets.QLabel(),
            "maxCount": QtWidgets.QSpinBox(),
            "reload": QtWidgets.QPushButton("Reload"),
        }

        layout = QtWidgets.QHBoxLayout(panels["header"])
        layout.addWidget(widgets["filesize"])
        layout.addWidget(QtWidgets.QWidget())
        layout.addWidget(widgets["nodeCount"])
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(QtWidgets.QLabel("Maximum Count"))
        layout.addWidget(widgets["maxCount"])
        layout.addWidget(QtWidgets.QWidget())
        layout.setContentsMargins(px(5), px(2), px(5), px(2))
        layout.setSpacing(px(3))

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(panels["header"])
        layout.addWidget(panels["body"], 1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        widgets["filesize"].setText(
            "%.2f mb" % (data["filesize"] / 1000.0 / 1000.0)
        )
        widgets["nodeCount"].setText(
            "%d nodes" % len(data["nodes"])
        )
        widgets["characterCount"].setText(
            "%d characters" % data["totalCharacterCount"]
        )

        widgets["maxCount"].setMinimum(1)
        widgets["maxCount"].setMaximum(10000)
        widgets["maxCount"].setSingleStep(5)
        widgets["maxCount"].setValue(opts.maxcount if opts else 100)

        # Try not to hog the CPU during window resize
        self._timer = QtCore.QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(5)
        self._timer.timeout.connect(self.layout)

        widgets["maxCount"].valueChanged.connect(self._timer.start)

        self._panels = panels
        self._widgets = widgets

        self._data = {
            "parsed": data,
            "items": sorted(
                data["nodes"].items(),
                reverse=True,
                key=lambda i: i[1]["characters"]
            )
        }

        self.setStyleSheet(scale_stylesheet(stylesheet))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            button = self.childAt(event.pos())

            if button and isinstance(button, QtWidgets.QLabel):
                name = button.objectName()

                clipboard = QtWidgets.qApp.clipboard()
                clipboard.setText(name)

                self.clicked.emit(name)

                print("Copied '%s' to clipboard" % name)

        return super(Widget, self).mousePressEvent(event)

    def clear(self):
        for child in self._panels["body"].children():
            child.deleteLater()

    def showEvent(self, event):
        self._timer.start()

    def resizeEvent(self, event):
        self._timer.start()

    @timer
    def layout(self):
        self.clear()

        body = self._panels["body"]
        size = body.size()
        items = self._data["items"]
        parsed = self._data["parsed"]

        x = 0.0
        y = 0.0
        width = size.width()
        height = size.height()

        maxcount = self._widgets["maxCount"].value()
        peak = max([1, min(maxcount, len(items))])

        keys = list(
            i[0] for i in items[:peak]
        )

        character_counts = list(
            i[1]["characters"] for i in items[:peak]
        )

        sizes = normalize_sizes(character_counts, width, height)
        padded_rects = squarify(sizes, x, y, width, height)

        for index, rect in enumerate(padded_rects):
            name = keys[index]
            characters = character_counts[index]
            characters = float(characters)  # Support division
            typ = parsed["nodes"][name]["nodeType"]

            # Give names to the first n-number of items
            if rect["dx"] > px(80):
                percentage = (characters / parsed["totalCharacterCount"]) * 100
                label = "%s\n%.1f%% (%d)" % (name, percentage, characters)
            else:
                label = "%d" % characters

            button = Square(label, parent=body)
            button.setObjectName(name)
            button.setAlignment(QtCore.Qt.AlignCenter)
            button.setProperty("node", True)
            button.setProperty("nodeType", typ)
            button.setToolTip("%s (%d)\n%s" % (name, characters, typ))
            button.move(rect["x"], rect["y"])
            button.setFixedSize(rect["dx"], rect["dy"])
            button.show()


def parse(fname=None):
    """Parse current of specified filename from within Maya"""

    from maya import cmds
    import tempfile

    tempdir = tempfile.gettempdir()
    title = None

    if not fname:
        location = cmds.file(location=True, query=True)
        modified = cmds.file(modified=True, query=True)
        fformat = cmds.file(type=True, query=True)

        if location and fformat == "mayaAscii" and not modified:
            print("Reading current saved file..")
            fname = cmds.file(sceneName=True, query=True)
        else:
            print("Saving to a temporary directory..")
            fname = os.path.join(tempdir, "temp.ma")
            cmds.file(fname, exportAll=True, force=True, type="mayaAscii")

        title = "Current Scene"

    parser = Parser()
    parser.parse(fname)

    parent = MayaWindow()
    width = px(600)

    # Fit within the Maya window
    height = min([px(1000), parent.size().height() - 200])

    # But lookout for getting a 0 or negative size
    height = max([height, 300])

    def on_clicked(path):
        cmds.select(path)

    win = Widget(parser.result, title=title, parent=parent)
    win.clicked.connect(on_clicked)
    win.resize(width, height)
    win.show()

    return win


def show():
    return parse()


# Embedded version of https://github.com/laserson/squarify
# Copyright 2013 Uri Laserson
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
def pad_rectangle(rect):
    if rect["dx"] > 2:
        rect["x"] += 1
        rect["dx"] -= 2
    if rect["dy"] > 2:
        rect["y"] += 1
        rect["dy"] -= 2


def layoutrow(sizes, x, y, dx, dy):
    covered_area = sum(sizes)
    width = covered_area / dy
    rects = []
    for size in sizes:
        rects.append({"x": x, "y": y, "dx": width, "dy": size / width})
        y += size / width
    return rects


def layoutcol(sizes, x, y, dx, dy):
    covered_area = sum(sizes)
    height = covered_area / dx
    rects = []
    for size in sizes:
        rects.append({"x": x, "y": y, "dx": size / height, "dy": height})
        x += size / height
    return rects


def layout(sizes, x, y, dx, dy):
    return (
        layoutrow(sizes, x, y, dx, dy)
        if dx >= dy
        else layoutcol(sizes, x, y, dx, dy)
    )


def leftoverrow(sizes, x, y, dx, dy):
    covered_area = sum(sizes)
    width = covered_area / dy
    leftover_x = x + width
    leftover_y = y
    leftover_dx = dx - width
    leftover_dy = dy
    return (leftover_x, leftover_y, leftover_dx, leftover_dy)


def leftovercol(sizes, x, y, dx, dy):
    covered_area = sum(sizes)
    height = covered_area / dx
    leftover_x = x
    leftover_y = y + height
    leftover_dx = dx
    leftover_dy = dy - height
    return (leftover_x, leftover_y, leftover_dx, leftover_dy)


def leftover(sizes, x, y, dx, dy):
    return (
        leftoverrow(sizes, x, y, dx, dy)
        if dx >= dy
        else leftovercol(sizes, x, y, dx, dy)
    )


def worst_ratio(sizes, x, y, dx, dy):
    return max(
        [
            max(rect["dx"] / rect["dy"], rect["dy"] / rect["dx"])
            for rect in layout(sizes, x, y, dx, dy)
        ]
    )


def squarify(sizes, x, y, dx, dy):
    sizes = list(map(float, sizes))

    if len(sizes) == 0:
        return []

    if len(sizes) == 1:
        return layout(sizes, x, y, dx, dy)

    # figure out where 'split' should be
    i = 1
    while (i < len(sizes) and
           worst_ratio(sizes[:i], x, y, dx, dy) >=
           worst_ratio(sizes[: (i + 1)], x, y, dx, dy)):
        i += 1

    current = sizes[:i]
    remaining = sizes[i:]

    leftover_x, leftover_y, leftover_dx, leftover_dy = leftover(
        current, x, y, dx, dy)

    return layout(current, x, y, dx, dy) + squarify(
        remaining, leftover_x, leftover_y, leftover_dx, leftover_dy
    )


def padded_squarify(sizes, x, y, dx, dy):
    rects = squarify(sizes, x, y, dx, dy)
    for rect in rects:
        pad_rectangle(rect)
    return rects


def normalize_sizes(sizes, dx, dy, minimum_size=0.01):
    """Give each size a value between 0-1

    Arguments:
        minimum_size (float, optional): Minimum size ratio, to keep
            dominant values from completely obstructing the
            view of smaller sizes

    """

    minsize = max(sizes) * minimum_size

    for index, size in enumerate(sizes):
        sizes[index] = max([size, minsize])

    total_size = sum(sizes)
    total_area = dx * dy
    sizes = map(float, sizes)
    sizes = map(lambda size: size * total_area / total_size, sizes)

    return list(sizes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--maxcount", default=100, type=int)

    opts = parser.parse_args()

    parser = Parser()
    parser.parse(opts.file)

    app = QtWidgets.QApplication()

    win = Widget(parser.result, opts)
    win.resize(px(600), px(1000))
    win.show()
    app.exec_()
