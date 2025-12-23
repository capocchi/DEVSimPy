import builtins
import importlib
import os
import re

from Utilities import getOutDir
from Patterns.Strategy import SimStrategy

def terminate_never(model, clock):
	return False

class ClassicPyPDEVSSimStrategy(SimStrategy):
	""" classic strategy for PyPDEVS simulation
		setClassicDEVS is True and confTransition in disabled
	"""

	def __init__(self, simulator = None):
		super().__init__(simulator)

	def simulate(self, T = 1e8):
		"""Simulate the model (Root-Coordinator).
		"""
		
		if self._simulator is None:
			raise ValueError("Simulator instance must be provided to ClassicPyPDEVSSimStrategy.")
		
		# Import the correct simulator module dynamically
		path = getattr(builtins, 'DEVS_DIR_PATH_DICT').get('PyPDEVS', None)
		if not path:
			raise ValueError("PyPDEVS path not found in DEVS_DIR_PATH_DICT")

		d = re.split("DEVSKernel", path)[-1].replace(os.sep, '.')
		simulator_module = importlib.import_module(f"DEVSKernel{d}.simulator")

		print("\nAvailable classes and methods:")
		for item in dir(simulator_module.Simulator):
			if not item.startswith('_'):
				print(f"- {item}")

		# Create simulator instance with the model
		sim = simulator_module.Simulator(self._simulator.model)

		# Configure simulation parameters
		if hasattr(sim, 'setVerbose'):
			if self._simulator.verbose:
				sim.setVerbose(None)
			else:
				out_dir = os.path.join(getOutDir())
				if not os.path.exists(out_dir):
					os.makedirs(out_dir)
				verbose_file = os.path.join(out_dir, 'verbose.txt')
				sim.setVerbose(verbose_file)

		# Set termination condition
		if hasattr(sim, 'setTerminationTime'):
			if self._simulator.ntl:
				sim.setTerminationCondition(terminate_never)
			else:
				sim.setTerminationTime(T)

		# Run simulation using available method
		if hasattr(sim, 'simulate'):
			sim.simulate()
		elif hasattr(sim, 'run'):
			sim.run()
		else:
			raise AttributeError("Simulator has no 'simulate' or 'run' method")

		self._simulator.terminate()

	def SetClassicDEVSOption(self):
		return True

class ParallelPyPDEVSSimStrategy(ClassicPyPDEVSSimStrategy):
	""" Parallel strategy for PyPDEVS simulation
		setClassicDEVS is False and confTransition in enabled
	"""

	def __init__(self, simulator = None):
		""" Constructor.
		"""
		super(). __init__(simulator)

	def SetClassicDEVSOption(self):
		return False