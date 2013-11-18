import numpy as np

from scipy.interpolate import interp1d

#######################################################
###                 <base> 
###		 ---------- max
###	       -      |     -
###  <zero_l> -     center     - <zero_r>
###  -------- <slop_l>  <slop-r> --------
###
###
#######################################################

def trapeze(c=1, b = 10, s_l = 10, s_r = 10, m = 500000, w=53):
  """	c = center of trapeze (1 to weeks possibility)
	b = must be pair (top of the trapeze)
	s_l = base of left slop_l
	s_r = base of left slop_r
	m = max level in m3
	w = numnber of weeks
  """
  center = c 
  base = b 
  slop_l = s_l
  slop_r = s_r
  max = m
  weeks = w

  ### test if center is good for left part
  a = center-slop_l-base/2

  if a < 0:
    zero_l = 0
    if slop_l+a < 0:
      a += slop_l
      slop_l = 0
    else:
      slop_l+=a
      
    if slop_l == 0 and a < 0:
      if base+a>0:
	base+=a
  else:
    zero_l = a 

  ###################################################

  b = weeks - (zero_l+slop_l+base+slop_r)
  zero_r = b if b >=0 else 0

  interval = (zero_l, slop_l, base, slop_r, zero_r )

  ### test if center is good for right part
  if sum(interval)!=weeks and zero_r==0:
    d = sum(interval) - weeks
    slop_r -= d
    if slop_r < 0:
      slop_r = 0
  
  interval = (zero_l, slop_l, base, slop_r, zero_r )

  if sum(interval)!=weeks and slop_r==0:
    d = sum(interval) - weeks
    base -= d
    if slop_r < 0:
      base = 0

  interval = (zero_l, slop_l, base, slop_r, zero_r )

  #########################################################
  ### lets go to build x and y array and plot it

  assert(sum(interval)==weeks)

  a = np.zeros(interval[0])
  b = np.linspace(0,max,interval[1])
  c = np.ones(interval[2])*max
  d = np.linspace(max,0,interval[3])
  e = np.zeros(interval[-1])

  x = np.arange(weeks)
  y = np.concatenate((a, b, c, d, e))

  return (x,y)
  
x,y = trapeze(24)

weeks = 53

### interpolate
f = interp1d(x, y)
f2 = interp1d(x, y, kind='cubic')
xnew = np.linspace(0, weeks-1, weeks)

### plot
import matplotlib.pyplot as plt
#plt.plot(x,y, 'o',xnew,f(xnew),'-', xnew, f2(xnew),'--')
#plt.plot(xnew, f2(xnew))
#plt.legend(['data', 'linear', 'cubic'], loc='best')
#plt.grid(True)
#plt.show()