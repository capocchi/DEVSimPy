# -*- coding: utf-8 -*- # noqa: UP009

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
# test_aifilecontext.py --- Tests for AI file attachments.
#                     --------------------------------
#                            Copyright (c) 2026
#                    L. CAPOCCHI (capocchi@univ-corse.fr)
#                SPE Lab - SISU Group - University of Corsica
#                     --------------------------------
# Version 1.0                                      last modified:  15/11/26
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

"""Pure (non-GUI) tests for ``devsimpy/AIFileContext.py``.

Run with:
    python tests/test_aifilecontext.py
"""

import os
import sys
import tempfile

### Paths ---------------------------------------------------------------
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(os.path.dirname(TESTS_DIR), "devsimpy")

if PACKAGE_DIR not in sys.path:
	sys.path.append(PACKAGE_DIR)

import AIFileContext as afc


### Helpers -------------------------------------------------------------
def write_text(directory, name, text, encoding="utf-8"):
	path = os.path.join(directory, name)
	with open(path, "w", encoding=encoding, newline="") as file:
		file.write(text)
	return path


def write_pdf(directory, name, text=None):
	"""Create a small PDF with reportlab; return None when unavailable."""
	try:
		from reportlab.pdfgen import canvas
	except ImportError:
		return None

	path = os.path.join(directory, name)
	document = canvas.Canvas(path)
	document.setFont("Helvetica", 12)

	if text:
		document.drawString(72, 720, text)

	document.showPage()
	document.save()
	return path


### Tests ---------------------------------------------------------------
def test_supported_extensions():
	assert afc.is_supported_file("spec.txt")
	assert afc.is_supported_file("spec.TXT")
	assert afc.is_supported_file("spec.pdf")
	assert afc.is_supported_file("spec.md")
	assert not afc.is_supported_file("spec.docx")
	print("OK test_supported_extensions")


def test_load_text_file():
	with tempfile.TemporaryDirectory() as directory:
		path = write_text(directory, "spec.txt", "Line 1\r\nLine 2\r\n")
		attachment = afc.load_attachment(path)

		assert attachment.name == "spec.txt"
		assert attachment.text == "Line 1\nLine 2"
		assert attachment.chars == len("Line 1\nLine 2")
		assert not attachment.truncated
	print("OK test_load_text_file")


def test_load_text_file_with_cp1252():
	with tempfile.TemporaryDirectory() as directory:
		path = write_text(
			directory,
			"latin.txt",
			"Caf\u00e9 et mod\u00e8le",
			encoding="cp1252",
		)
		attachment = afc.load_attachment(path)
		assert "Caf\u00e9" in attachment.text
	print("OK test_load_text_file_with_cp1252")


def test_load_pdf_file():
	with tempfile.TemporaryDirectory() as directory:
		path = write_pdf(directory, "spec.pdf", "Hello PDF attachment")

		if path is None:
			print("SKIP test_load_pdf_file (reportlab not installed)")
			return

		attachment = afc.load_attachment(path)
		assert "Hello PDF attachment" in attachment.text
	print("OK test_load_pdf_file")


def test_empty_pdf_is_rejected():
	with tempfile.TemporaryDirectory() as directory:
		path = write_pdf(directory, "empty.pdf")

		if path is None:
			print("SKIP test_empty_pdf_is_rejected (reportlab not installed)")
			return

		try:
			afc.load_attachment(path)
		except afc.AIFileError as error:
			assert "No extractable text" in str(error), error
		else:
			raise AssertionError("AIFileError was not raised for an empty PDF")
	print("OK test_empty_pdf_is_rejected")


def test_unsupported_file_is_rejected():
	with tempfile.TemporaryDirectory() as directory:
		path = write_text(directory, "data.docx", "not supported")

		try:
			afc.load_attachment(path)
		except afc.AIFileError as error:
			assert "Unsupported file type" in str(error), error
		else:
			raise AssertionError("AIFileError was not raised")
	print("OK test_unsupported_file_is_rejected")


def test_single_file_is_truncated():
	with tempfile.TemporaryDirectory() as directory:
		path = write_text(directory, "long.txt", "x" * 100)
		attachment = afc.load_attachment(path, max_chars=10)

		assert attachment.truncated
		assert attachment.text.startswith("x" * 10)
		assert "[truncated]" in attachment.text
	print("OK test_single_file_is_truncated")


def test_total_budget_is_enforced():
	attachments = [
		afc.AIFileAttachment("a.txt", "a" * 30),
		afc.AIFileAttachment("b.txt", "b" * 30),
	]

	block = afc.format_attachments(attachments, max_total_chars=25)

	assert "Begin attached file: a.txt" in block
	assert "a" * 25 in block
	assert "[truncated]" in block
	assert "omitted (context budget reached): b.txt" in block
	print("OK test_total_budget_is_enforced")


def test_compose_prompt():
	attachments = [afc.AIFileAttachment("spec.txt", "model specification")]

	assert afc.compose_prompt("build a model", []) == "build a model"

	composed = afc.compose_prompt("build a model", attachments)
	assert composed.startswith("build a model")
	assert afc.ATTACHMENT_HEADER in composed
	assert "--- Begin attached file: spec.txt ---" in composed
	assert "model specification" in composed
	assert "--- End attached file: spec.txt ---" in composed
	print("OK test_compose_prompt")


def test_summarize_attachments():
	assert afc.summarize_attachments([]) == "No file attached."

	attachments = [
		afc.AIFileAttachment("a.txt", "a" * 10),
		afc.AIFileAttachment("b.txt", "b" * 5),
	]

	summary = afc.summarize_attachments(attachments)
	assert "2 file(s)" in summary
	assert "15" in summary
	print("OK test_summarize_attachments")


### Main ----------------------------------------------------------------
if __name__ == "__main__":
	test_supported_extensions()
	test_load_text_file()
	test_load_text_file_with_cp1252()
	test_load_pdf_file()
	test_empty_pdf_is_rejected()
	test_unsupported_file_is_rejected()
	test_single_file_is_truncated()
	test_total_budget_is_enforced()
	test_compose_prompt()
	test_summarize_attachments()

	print("\nAll tests passed!")
