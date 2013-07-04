
cdef extern from "math.h":
	float sin(float a)
	float cos(float a)
	float pow(float a, int b)

def calc1(float a, float phi, float w, float tn):
	return a*sin(w*tn+phi)
def calc2(float a, float phi, float w, float tn):
	return a*w*cos(w*tn+phi)
def calc3(float a, float phi, float w, float tn):
	return a*pow(w,2)*sin(w*tn+phi)/2
