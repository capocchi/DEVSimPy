# -*- coding: utf-8 -*-

from scipy.constants import codata
import math

nameC = ""
def compute(name, data, dt):
	global nameC
	nameC = name
	G = codata.value('Newtonian constant of gravitation')
	at = [[], []]

	current_mass_objet = data[name]
	for mass_object in data.keys():
		
		if name != mass_object:
			M = data[mass_object]["M"]
			x = data[mass_object]["x"]
			y = data[mass_object]["y"]
			a = gravitational_field(M, (current_mass_objet["x"], current_mass_objet["y"]), (x, y))
			ax, ay = vector_decomp((current_mass_objet["x"], current_mass_objet["y"]), (x, y), a)

			at[0].append(ax)
			at[1].append(ay)
	ax, ay = speed_sum(at)
	vx, vy = from_a_to_v((ax, ay), (current_mass_objet["vx"], current_mass_objet["vy"]), dt)
	x, y = position_computing((current_mass_objet["x"], current_mass_objet["y"]), (vx, vy), dt)
	current_mass_objet["x"] = x
	current_mass_objet["y"] = y
	current_mass_objet["vx"] = vx
	current_mass_objet["vy"] = vy
	current_mass_objet["ax"] = ax
	current_mass_objet["ay"] = ay
	return current_mass_objet

def gravitational_field(M, current, planet):
	G = codata.value('Newtonian constant of gravitation')
	r = get_distance(current, planet)
	return G*M/math.pow(r, 2)

def get_distance(current, planet):
	x1, y1 = current
	x2, y2 = planet

	r = math.sqrt(math.pow(x1 - x2, 2)) + math.sqrt(math.pow(y1 - y2, 2))
	# r = r * math.pow(10, 3)
	return r

def position_computing(coord, v, dt):
	x, y = coord
	vx, vy = v

	x += vx * dt
	y += vy * dt
	return x, y

def vector_decomp(current, planet, a):
	global nameC

	x1, y1 = current
	x2, y2 = planet
	x = x1 - x2
	y = y1 - y2

	op = None
	adj = None
	hyp = None

	### Hypotenus par Pythagore
	hyp = math.sqrt(math.pow(x, 2) + math.pow(y, 2))

	### Partie gauche du cercle
	if x1 < x2:
		adj = abs(x)
		op = abs(y)
	else:
		adj = abs(y)
		op = abs(x)

	### Angle du vecteur de gravitation
	teta = math.acos(adj/hyp)

	ax = abs(a * math.cos(teta))
	ay = math.sqrt(math.pow(a, 2) - math.pow(ax, 2))
	# if nameC == "MassObject_0":
	# 	print current, planet
	# 	print x1 > x2
	# 	print y1 > y2
	if x1 > x2:
		ax = -ax
	if y1 > y2:
		ay = -ay

	return ax, ay

def from_a_to_v(a, Vinit, dt):
	ax, ay = a
	vx, vy = Vinit

	vx += ax * dt
	vy += ay * dt

	return vx, vy

def speed_sum(a):
	ax = 0
	ay = 0

	for axt in a[0]:
		ax += axt
	for ayt in a[1]:
		ay += ayt
	return ax, ay
