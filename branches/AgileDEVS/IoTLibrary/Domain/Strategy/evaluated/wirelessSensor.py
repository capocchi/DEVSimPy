# -*- coding: utf-8 -*-

from Domain.Strategy.evaluated.abstractEvaluated import AbstractEvaluated

class WirelessSensor(AbstractEvaluated):

        def __init__(self, maxRange=600.0):
            AbstractEvaluated.__init__(self, maxRange)


	def __str__(self):
            return "WirelessSensor"