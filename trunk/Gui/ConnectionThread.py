# -*- coding: utf-8 -*-

import os
import sys
import time

from threading import Thread
from Container import Diagram

class LoadFileThread(Thread):
	""" Worker thread class to attempt loading diagram from filename."""

	def __init__(self, diagram, filename):
		"""
		Initialize the worker thread.

		
		**Parameters:**

		* diagram:
		* filename:

		"""
		
		Thread.__init__(self)

		self._fn = filename
		self._d = diagram

		# final value
		self.value = True

		self.setDaemon(True)
		self.start()

	def run(self):
		""" Run worker thread. 
		"""
		
		self.value = Diagram.LoadFile(self._d, self._fn)
		
		return

	def finish(self):
		""" Return final value.
		"""
		return self.value # return value