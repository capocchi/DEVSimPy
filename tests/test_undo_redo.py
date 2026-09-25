"""Test script for the undo/redo functionality of DEVSimPy.

The test exercises the ShapeCanvas history engine (baseline recording, undo,
redo, redo invalidation) without relying on the main window notification chain.

Usage:
    python test_undo_redo.py --autoclose
    python test_undo_redo.py --autoclose 10  # Auto-close after 10s delay
"""

from ApplicationController import TestApp

# import after ApplicationController that inits sys.path to avoid this import
import Container
from DetachedFrame import DetachedFrame


class UndoRedoTester:
	"""Small harness that exercises the ShapeCanvas undo/redo engine.
	"""

	def __init__(self, canvas):
		self.canvas = canvas
		self.results = []

	def check(self, name, ok, extra=None):
		self.results.append((name, bool(ok), extra))
		return bool(ok)

	def run(self):
		canvas = self.canvas

		### a fresh diagram is the baseline of the history: one snapshot, nothing to undo
		self.check('baseline snapshot recorded', len(canvas.stockUndo) == 1, len(canvas.stockUndo))
		self.check('redo stack empty at start', len(canvas.stockRedo) == 0, len(canvas.stockRedo))
		self.check('undo on baseline does nothing', canvas.ApplyUndo() is False)
		self.check('redo on empty stack does nothing', canvas.ApplyRedo() is False)

		### simulate a first edit and record it
		diagram = canvas.GetDiagram()
		diagram.modify = True
		diagram.constants_dico['k'] = 1
		self.check('edit recorded', canvas.PushUndoState() is True, len(canvas.stockUndo))
		self.check('two snapshots after one edit', len(canvas.stockUndo) == 2, len(canvas.stockUndo))

		### pushing an unchanged state must be ignored
		self.check('unchanged state not recorded', canvas.PushUndoState() is False, len(canvas.stockUndo))

		### undo restores the baseline and fills the redo stack
		self.check('undo returns True', canvas.ApplyUndo() is True)
		self.check('baseline restored', canvas.GetDiagram().constants_dico.get('k') is None,
					canvas.GetDiagram().constants_dico)
		self.check('redo now available', len(canvas.stockRedo) == 1, len(canvas.stockRedo))

		### redo re-applies the edit
		self.check('redo returns True', canvas.ApplyRedo() is True)
		self.check('edit re-applied', canvas.GetDiagram().constants_dico.get('k') == 1,
					canvas.GetDiagram().constants_dico)

		### a new edit after an undo must invalidate the redo history
		canvas.ApplyUndo()
		diagram = canvas.GetDiagram()
		diagram.modify = True
		diagram.constants_dico['other'] = 2
		canvas.PushUndoState()
		self.check('new edit clears redo', len(canvas.stockRedo) == 0, len(canvas.stockRedo))

		return self.results


def main():
	results = UndoRedoTester(frame.canvas).run()

	print('\n=== UNDO/REDO TEST RESULTS ===')
	for name, ok, extra in results:
		print('[%s] %s (%s)' % ('PASS' if ok else 'FAIL', name, extra))
	all_ok = len(results) > 0 and all(ok for _, ok, _ in results)
	print('ALL PASS:', all_ok)
	print('==============================\n')

	app.RunTest(frame)


# Run the test
app = TestApp(0)

diagram = Container.Diagram()
frame = DetachedFrame(None, -1, "Test", diagram)

main()
