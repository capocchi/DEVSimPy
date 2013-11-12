## In order to produce .so file (python-pyrex and cython must be installed)
## 1/ cython func.pyx
## 2/ gcc -c -fPIC -I/usr/include/python2.6/ func.c
## 3/ gcc -shared func.o -o func.so

pidiv3 = 1.047197551

cdef extern from "math.h":
	double acos(double a)
	double cos(double a)
	double sqrt(double a)
	double fabs(double a)
	double abs(double a)
	double pow(double a, double b)

def calc1(double x, double u, double q, double dQ, double INFINITY):
	
	cdef double sigma = (q-dQ-x)/u
	
	if(u == 0):
		sigma=INFINITY
	elif(u > 0):
		sigma=(q+dQ-x)/u
		
	return sigma

def calc2(double x, double elapsed, double u, double q, double dQ, double mu, double mq, double INFINITY):
	cdef double a = mu/2
	cdef double b = u-mq
	cdef double c = x-q+dQ
	cdef double s = 0.0
	cdef double sigma =INFINITY

	if(a==0):
		if(b!=0):
			s=-c/b
			if(s>0):
				# changement d'etat
				sigma=s
			c=x-q-dQ
			s=-c/b
			if ((s>0) and (s<sigma)):
				# changement d'etat
				sigma=s
	else:
		if (b*b-4*a*c) > 0:
			s=(-b+sqrt(b*b-4*a*c))/2/a
			if (s>0):
				# changement d'etat
				sigma=s
			s=(-b-sqrt(b*b-4*a*c))/2/a
			if ((s>0) and (s<sigma)):
				# changement d'etat
				sigma=s
		
		c=x-q-dQ
		if (b*b-4*a*c) > 0:	
			s=(-b+sqrt(b*b-4*a*c))/2/a
			if ((s>0) and (s<sigma)):
				# changement d'etat
				sigma=s
			s=(-b-sqrt(b*b-4*a*c))/2/a
			if ((s>0) and (s<sigma)):
				# changement d'etat
				sigma=s
	
	if abs(x-q)>dQ:
		
		# changement d'etat
		sigma=0
			
	return sigma
	
def calc3(double x, double elapsed, double u, double q, double dQ, double mu, double mq, double pq, double pu, double INFINITY):
	
	cdef double a = mu/2-pq
	cdef double b = u-mq
	cdef double c = x-q-dQ
	cdef double v = 0.0
	cdef double w = 0.0
	cdef double A = 0.0
	cdef double B = 0.0
	cdef double i1 = 0.0
	cdef double i2 = 0.0
	cdef double s = 0.0
	cdef double sigma = 0.0

	if(pu!=0):
		
		a=3*a/pu
		b=3*b/pu
		c=3*c/pu
		v=b-(a*a/3)
		w=c-(b*a/3)+(2*a*a*a/27)
		i1=-w/2
		i2=(i1*i1)+(v*v*v/27)
		
		if(i2>0):
			i2=sqrt(i2)
			A=i1+i2
			B=i1-i2
			if(A>0):
				A=pow(A,1.0/3)
			else:
				A=-pow(fabs(A),1.0/3)
			if(B>0):
				B=pow(B,1.0/3)
			else:
				B=-pow(fabs(B),1.0/3)	
				
			s=A+B-(a/3)
			if(s<0): s=INFINITY
			
		elif(i2==0):
			A=i1
			if(A>0):
				A=pow(A,1.0/3)
			else:
				A=-pow(fabs(A),1.0/3)
			x1=2*A-(a/3)
			x2=-(A+(a/3))
			if(x1<0):
				if(x2<0):
					s=INFINITY
				else:
					s=x2
			elif(x2<0) or (x1<x2):
				s=x1
			else:
				s=x2
		else:
			arg=(w*sqrt(27/-v))/(2*v)
			arg=acos(arg)/3.0

			y1=2*sqrt(-v/3)
			y2=-y1*cos(pidiv3-arg)-(a/3)
			y3=-y1*cos(pidiv3+arg)-(a/3)
			y1=y1*cos(arg)-(a/3)
			if(y1<0):
				s=INFINITY
			elif(y3<0):
				s=y1
			elif(y2<0):
				s=y3
			else:
				s=y2
				
		c+=(6*dQ)/pu
		w=c-(b*a/3)+(2*a*a*a/27)
		i1=-w/2
		i2=(i1*i1)+(v*v*v/27)
		
		if(i2>0):
			i2=sqrt(i2)
			A=i1+i2
			B=i1-i2
			if(A>0):
				A=pow(A,1.0/3)
			else:
				A=-pow(fabs(A),1.0/3)
			if(B>0):
				A=pow(B,1.0/3)
			else:
				B=-pow(fabs(B),1.0/3)
			
			sigma=A+B-(a/3)
			
			if (s<sigma) or (sigma<0):
				sigma=s
				
		elif(i2==0):
			A=i1
			if(A>0):
				A=pow(A,1.0/3)
			else:
				A=-pow(fabs(A),1.0/3)
			x1=(2*A)-(a/3)
			x2=-(A+(a/3))
			if(x1<0):
				if(x2<0):
					sigma=INFINITY
				else:
					sigma=x2
			
			elif(x2<0) or (x1<x2):
					sigma=x1
			else:
					sigma=x2
					
			if (s<sigma):
				sigma = s
	
		else:
			arg=(w*sqrt(27/-v))/(2*v)
			arg=acos(arg)/3.0

			y1=2*sqrt(-v/3)
			y2=-y1*cos(pidiv3-arg)-(a/3)
			y3=-y1*cos(pidiv3+arg)-(a/3)
			y1=y1*cos(arg)-(a/3)
			if(y1<0):
				s=INFINITY
			elif(y3<0):
				s=y1
			elif(y2<0):
				s=y3
			else:
				s=y2			
			if (s<sigma):
				sigma = s
	else:
		if(a!=0):
			x1=(b*b)-(4*a*c)
			if(x1<0):
				s=INFINITY
			else:
				x1=sqrt(x1)
				x2=(-b-x1)/(2*a)
				x1=(-b+x1)/(2*a)
				
				if(x1<0):
					if(x2<0):
						s=INFINITY
					else:
						s=x2
				elif(x2<0) or (x1<x2):
					s=x1
				else:
					s=x2
						
			c+=2*dQ
			x1=(b*b)-(4*a*c)
			if(x1<0):
				sigma=INFINITY
			else:
				x1=sqrt(x1)
				x2=(-b-x1)/(2*a)
				x1=(-b+x1)/(2*a)
				if(x1<0):
					if(x2<0):
						sigma=INFINITY
					else:
						sigma=x2
				elif(x2<0) or (x1<x2):
					sigma=x1
				else:
					sigma=x2
					
			if (s<sigma):	sigma=s
			
		elif(b!=0):
			x1=-c/b
			x2=x1-2*(dQ/b)
			if(x1<0):
				x1=INFINITY
			if (x2<0):
				x2=INFINITY
			if(x1<x2):
				sigma=x1
			else:
				sigma=x2
				
	if fabs(x-q)>dQ: 
		sigma=0
	 
	return sigma
	
def calc4(double q, double dQ, double u):
	return [q+dQ*u/fabs(u),0.0,0.0]
	
def calc5(double x, double u, double sigma, double mu):
	return [x+u*sigma+mu*sigma*sigma/2, u+mu*sigma, 0.0]
	
def calc6(double x, double u, double sigma, double mu, double pu):
	return [x+u*sigma+(mu*pow(sigma,2))/2.0 + (pu*pow(sigma,3))/3.0, u+mu*sigma+pu*pow(sigma,2), mu/2.0 + pu*sigma]