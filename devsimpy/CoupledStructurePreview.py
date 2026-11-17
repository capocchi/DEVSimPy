# -*- coding: utf-8 -*-  # noqa: UP009

"""Graphical preview of a coupled model structure.

The AI coupled-model assistant displays the JSON structure proposed by the
model.  This module turns that structure into a simple diagram (submodel
boxes, ports and couplings) so the user can check it before validating it.

The layout computation (:func:`compute_preview_layout`) is pure Python and
can be tested without a graphical display; :class:`StructurePreviewPanel`
only draws the computed layout.
"""

import gettext
import math

import wx

from CoupledStructure import (
	DEFAULT_COLUMNS,
	DEFAULT_COLUMN_WIDTH,
	DEFAULT_ROW_HEIGHT,
	DEFAULT_X,
	DEFAULT_Y,
	INPUT_REFERENCES,
	OUTPUT_REFERENCES,
)

_ = gettext.gettext

### Drawing constants
BOX_WIDTH = 140
BOX_HEIGHT = 60
MARGIN = 40
LEGEND_HEIGHT = 26
EXTERNAL_PORT_OFFSET = 70
PORT_RADIUS = 4
ARROW_SIZE = 8

### Fill and border colours of the submodel boxes, by generate mode
BOX_COLOURS = {
	"existing": ((232, 241, 251), (47, 109, 181)),
	"behavior": ((230, 246, 233), (46, 125, 50)),
	"stub": ((240, 240, 240), (110, 110, 110)),
}

### Badge shown in the top-right corner of each box
BOX_BADGES = {
	"existing": "LIB",
	"behavior": "AI",
	"stub": "EMPTY",
}


def _as_float(value):
	"""Return ``value`` as a float, or None when it is not numeric."""
	try:
		return float(value)
	except (TypeError, ValueError):
		return None


def _as_count(value):
	"""Return ``value`` as a non-negative int."""
	try:
		count = int(value)
	except (TypeError, ValueError):
		return 0
	return max(count, 0)


def _submodel_position(submodel, index):
	"""Return the diagram position of ``submodel`` (grid default)."""
	x = _as_float(submodel.get("x"))
	y = _as_float(submodel.get("y"))

	if x is None:
		x = DEFAULT_X + (index % DEFAULT_COLUMNS) * DEFAULT_COLUMN_WIDTH

	if y is None:
		y = DEFAULT_Y + (index // DEFAULT_COLUMNS) * DEFAULT_ROW_HEIGHT

	return x, y


def _side_ports(x, top, height, count):
	"""Return ``count`` port positions spread along a vertical side."""
	ports = []

	for index in range(count):
		y = top + height * (index + 1) / (count + 1)
		ports.append({"index": index, "x": x, "y": y})

	return ports


def _port_at(ports, index):
	"""Return the port of ``index``, or None when it does not exist."""
	if ports is None or index is None or index < 0 or index >= len(ports):
		return None
	return ports[index]


def compute_preview_layout(
	structure,
	box_width=BOX_WIDTH,
	box_height=BOX_HEIGHT,
):
	"""Compute the drawing layout of a normalized coupled structure.

	Args:
		structure (dict): Structure returned by
			:func:`CoupledStructure.normalize_coupled_structure`.
		box_width (int): Width of a submodel box.
		box_height (int): Height of a submodel box.

	Returns:
		dict: ``width``/``height`` of the canvas, the ``boxes`` (with their
		port positions), the external ``inputs``/``outputs`` and the
		``connections`` (source/target points).
	"""
	submodels = structure.get("submodels") or []

	positions = [
		(submodel, *_submodel_position(submodel, index)) for index, submodel in enumerate(submodels)
	]

	if positions:
		left = min(x for _, x, _ in positions)
		top = min(y for _, _, y in positions)
		right = max(x + box_width for _, x, _ in positions)
		bottom = max(y + box_height for _, _, y in positions)
	else:
		left = top = 0.0
		right = box_width
		bottom = box_height

	### leave room for the legend above and the external ports on the sides
	offset_x = MARGIN + EXTERNAL_PORT_OFFSET - left
	offset_y = MARGIN + LEGEND_HEIGHT - top

	width = int(right + offset_x + EXTERNAL_PORT_OFFSET + MARGIN)
	height = int(bottom + offset_y + MARGIN)

	span_top = top + offset_y
	span_bottom = bottom + offset_y
	span = max(span_bottom - span_top, 1.0)

	def external_ports(count, x):
		ports = []

		for index in range(count):
			y = span_top + span * (index + 1) / (count + 1)
			ports.append({"index": index, "x": x, "y": y})

		return ports

	inputs = external_ports(_as_count(structure.get("inputs")), MARGIN)
	outputs = external_ports(_as_count(structure.get("outputs")), width - MARGIN)

	boxes = []
	by_label = {}

	for submodel, x, y in positions:
		box_x = x + offset_x
		box_y = y + offset_y
		label = str(submodel.get("label") or "")

		box = {
			"label": label,
			"model": str(submodel.get("model") or ""),
			"generate": str(submodel.get("generate") or "existing"),
			"x": box_x,
			"y": box_y,
			"width": box_width,
			"height": box_height,
			"inputs": _side_ports(
				box_x,
				box_y,
				box_height,
				_as_count(submodel.get("inputs")),
			),
			"outputs": _side_ports(
				box_x + box_width,
				box_y,
				box_height,
				_as_count(submodel.get("outputs")),
			),
		}

		boxes.append(box)
		by_label[label.strip().lower()] = box

	connections = []

	for connection in structure.get("connections") or []:
		source_reference = str(connection.get("source", "")).strip()
		target_reference = str(connection.get("target", "")).strip()

		source_index = _as_count(connection.get("source_port"))
		target_index = _as_count(connection.get("target_port"))

		if source_reference.lower() in INPUT_REFERENCES:
			source = _port_at(inputs, source_index)
		else:
			source_box = by_label.get(source_reference.lower())
			source = _port_at(source_box["outputs"], source_index) if source_box else None

		if target_reference.lower() in OUTPUT_REFERENCES:
			target = _port_at(outputs, target_index)
		else:
			target_box = by_label.get(target_reference.lower())
			target = _port_at(target_box["inputs"], target_index) if target_box else None

		### the preview is lenient: unresolved couplings are simply skipped
		if source is None or target is None:
			continue

		connections.append(
			{
				"source": source_reference,
				"target": target_reference,
				"x1": source["x"],
				"y1": source["y"],
				"x2": target["x"],
				"y2": target["y"],
			}
		)

	return {
		"width": width,
		"height": height,
		"boxes": boxes,
		"inputs": inputs,
		"outputs": outputs,
		"connections": connections,
	}


def _fit_text(dc, text, max_width):
	"""Return ``text`` truncated with an ellipsis to fit ``max_width``."""
	if dc.GetTextExtent(text)[0] <= max_width:
		return text

	ellipsis = "..."
	trimmed = text

	while trimmed and dc.GetTextExtent(trimmed + ellipsis)[0] > max_width:
		trimmed = trimmed[:-1]

	return trimmed + ellipsis if trimmed else ellipsis


class StructurePreviewPanel(wx.ScrolledWindow):
	"""Draw a coupled model structure as a diagram."""

	def __init__(self, parent):
		super().__init__(parent, style=wx.HSCROLL | wx.VSCROLL)
		self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
		self.SetBackgroundColour(wx.WHITE)
		self.SetScrollRate(10, 10)
		self._layout = None
		self._message = _("No structure to display yet.")
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_SIZE, self.OnSize)

	def SetStructure(self, structure):
		"""Display ``structure`` (see :func:`compute_preview_layout`)."""
		self._layout = compute_preview_layout(structure)
		self._message = ""
		self.SetVirtualSize((self._layout["width"], self._layout["height"]))
		self.Refresh()

	def SetMessage(self, message):
		"""Display a message instead of a diagram (empty or invalid JSON)."""
		self._layout = None
		self._message = message or ""
		self.SetVirtualSize((0, 0))
		self.Refresh()

	def GetLayout(self):
		"""Return the current layout (None when a message is displayed)."""
		return self._layout

	def GetMessage(self):
		"""Return the current message (empty when a diagram is displayed)."""
		return self._message

	def OnSize(self, event):
		if event is not None:
			event.Skip()
		self.Refresh()

	def OnPaint(self, event):
		dc = wx.AutoBufferedPaintDC(self)
		self.PrepareDC(dc)
		dc.SetBackground(wx.Brush(wx.WHITE))
		dc.Clear()

		if self._layout is None:
			self._draw_message(dc)
			return

		self._draw_layout(dc)

	### ------------------------------------------------------------------
	### Drawing helpers
	### ------------------------------------------------------------------
	def _draw_message(self, dc):
		width, height = self.GetClientSize()

		if not self._message:
			return

		dc.SetTextForeground(wx.Colour(110, 110, 110))

		lines = self._message.splitlines() or [self._message]
		line_height = dc.GetTextExtent("Ay")[1] + 4
		y = max(10, (height - line_height * len(lines)) // 2)

		for line in lines:
			line_width, _ = dc.GetTextExtent(line)
			dc.DrawText(line, max(10, (width - line_width) // 2), y)
			y += line_height

	def _draw_layout(self, dc):
		layout = self._layout

		dc.SetPen(wx.Pen(wx.Colour(110, 110, 110), 1))

		for connection in layout["connections"]:
			self._draw_connection(dc, connection)

		for box in layout["boxes"]:
			self._draw_box(dc, box)

		self._draw_external_ports(dc, layout["inputs"], _("in"), align_left=False)
		self._draw_external_ports(dc, layout["outputs"], _("out"), align_left=True)
		self._draw_legend(dc, layout)

	def _draw_connection(self, dc, connection):
		x1, y1 = connection["x1"], connection["y1"]
		x2, y2 = connection["x2"], connection["y2"]

		dc.DrawLine(int(x1), int(y1), int(x2), int(y2))

		angle = math.atan2(y2 - y1, x2 - x1)

		for spread in (math.pi / 6, -math.pi / 6):
			dc.DrawLine(
				int(x2),
				int(y2),
				int(x2 - ARROW_SIZE * math.cos(angle + spread)),
				int(y2 - ARROW_SIZE * math.sin(angle + spread)),
			)

	def _draw_box(self, dc, box):
		fill, border = BOX_COLOURS.get(box["generate"], BOX_COLOURS["existing"])

		dc.SetPen(wx.Pen(wx.Colour(*border), 2))
		dc.SetBrush(wx.Brush(wx.Colour(*fill)))
		dc.DrawRoundedRectangle(
			int(box["x"]),
			int(box["y"]),
			int(box["width"]),
			int(box["height"]),
			8,
		)

		inner_width = box["width"] - 16
		center_x = box["x"] + box["width"] / 2

		### submodel label (the name of the code block)
		dc.SetTextForeground(wx.Colour(30, 30, 30))
		dc.SetFont(
			wx.Font(
				9,
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_BOLD,
			)
		)
		label = _fit_text(dc, box["label"], inner_width)
		label_width, label_height = dc.GetTextExtent(label)
		dc.DrawText(label, int(center_x - label_width / 2), int(box["y"] + 8))

		### model/class bound to the submodel
		dc.SetTextForeground(wx.Colour(90, 90, 90))
		dc.SetFont(
			wx.Font(
				7,
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)
		model = _fit_text(dc, box["model"], inner_width)
		model_width, _ = dc.GetTextExtent(model)
		dc.DrawText(
			model,
			int(center_x - model_width / 2),
			int(box["y"] + 8 + label_height + 4),
		)

		### badge telling how the submodel is obtained
		badge = BOX_BADGES.get(box["generate"], "")
		if badge:
			dc.SetTextForeground(wx.Colour(*border))
			badge_width, _ = dc.GetTextExtent(badge)
			dc.DrawText(
				badge,
				int(box["x"] + box["width"] - badge_width - 6),
				int(box["y"] + box["height"] - 16),
			)

		self._draw_ports(dc, box["inputs"], align_left=False, colour=border)
		self._draw_ports(dc, box["outputs"], align_left=True, colour=border)

	def _draw_ports(self, dc, ports, align_left, colour):
		dc.SetPen(wx.Pen(wx.Colour(*colour), 1))
		dc.SetBrush(wx.Brush(wx.Colour(*colour)))
		dc.SetTextForeground(wx.Colour(80, 80, 80))
		dc.SetFont(
			wx.Font(
				6,
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)

		for port in ports:
			dc.DrawCircle(int(port["x"]), int(port["y"]), PORT_RADIUS)

			text = str(port["index"])
			text_width, text_height = dc.GetTextExtent(text)
			text_x = (
				port["x"] - PORT_RADIUS - text_width - 2
				if align_left
				else port["x"] + PORT_RADIUS + 2
			)
			dc.DrawText(text, int(text_x), int(port["y"] - text_height / 2))

	def _draw_external_ports(self, dc, ports, prefix, align_left):
		dc.SetPen(wx.Pen(wx.Colour(70, 70, 70), 1))
		dc.SetBrush(wx.Brush(wx.Colour(70, 70, 70)))
		dc.SetTextForeground(wx.Colour(70, 70, 70))
		dc.SetFont(
			wx.Font(
				7,
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)

		for port in ports:
			dc.DrawCircle(int(port["x"]), int(port["y"]), PORT_RADIUS + 1)

			text = f"{prefix} {port['index']}"
			text_width, text_height = dc.GetTextExtent(text)
			text_x = (
				port["x"] - PORT_RADIUS - text_width - 4
				if align_left
				else port["x"] + PORT_RADIUS + 4
			)
			dc.DrawText(text, int(text_x), int(port["y"] - text_height / 2))

	def _draw_legend(self, dc, layout):
		dc.SetFont(
			wx.Font(
				7,
				wx.FONTFAMILY_DEFAULT,
				wx.FONTSTYLE_NORMAL,
				wx.FONTWEIGHT_NORMAL,
			)
		)
		dc.SetTextForeground(wx.Colour(80, 80, 80))

		x = 10
		y = 8

		for mode, text in (
			("existing", _("library")),
			("behavior", _("AI-generated")),
			("stub", _("empty")),
		):
			fill, border = BOX_COLOURS[mode]
			dc.SetPen(wx.Pen(wx.Colour(*border), 1))
			dc.SetBrush(wx.Brush(wx.Colour(*fill)))
			dc.DrawRectangle(x, y, 10, 10)

			dc.SetTextForeground(wx.Colour(80, 80, 80))
			dc.DrawText(text, x + 14, y - 2)

			x += 14 + dc.GetTextExtent(text)[0] + 14

		### summary on the right, or below the legend when there is no room
		summary = _("{submodels} submodel(s), {connections} connection(s)").format(
			submodels=len(layout["boxes"]),
			connections=len(layout["connections"]),
		)
		summary_width = dc.GetTextExtent(summary)[0]
		summary_x = layout["width"] - summary_width - 10

		if summary_x > x + 10:
			dc.DrawText(summary, summary_x, y - 2)
		else:
			dc.DrawText(summary, 10, y + 14)
