import math, random, sys

# These are the other AnonPay algorithms (ROD, NUN, SPA).
# They must be invoked manually from within your app.
# The remainder of this directory is the oTree equivalent of CPY+TDY.

def count(l, x):
	return sum([1 for el in l if el == x])

def p_print2(paym):
	for pi in paym:
		print(pi, end = ", ")
	
	print()

def hadUniqPaym(paym):
	return any([count(paym, pi) == 1 for pi in paym])

def P(paym, attr, q):
	a = sum([1 for (i, el) in enumerate(paym) if el == q and attr[i] == 1])/count(attr, 1)
	b = sum([1 for (i, el) in enumerate(paym) if el == q and attr[i] == 0])/count(attr, 0)
	c = count(attr, 1)/len(paym)
	
	return (a * c)/(a * c + b * (1 - c))

def infoBayes(paym, attr):
	return {pi: P(paym, attr, pi) for pi in [_pi for (_pi, _x) in zip(paym, attr) if _x == 1]}

def ROD(paym, chi):
	for (i, pi) in enumerate(paym):
		paym[i] = math.ceil(pi/chi)*chi
	
	return paym

def NUN(paym):
	if len(paym) > 3:
		s = 1

		while True:
			if s == 1:
				rank = [sum([1 for pi2 in paym if pi2 >= pi]) for pi in paym]

			if count(rank, s) > 0:
				q = [paym[i] for (i, r) in enumerate(rank) if r == s][0]
				
				if count(paym, q) == 1:
					who1 = max([pi for pi in paym if pi < q], default = -math.inf)
					who2 = min([pi for pi in paym if pi > q], default = +math.inf)
					
					if count(paym, who1) > 0 and count(paym, who1)*(q-who1) <= who2-q:
						for (i, pi) in enumerate(paym):
							if pi == who1:
								paym[i] = q
								
								s = 0
								break
					else:
						for (i, pi) in enumerate(paym):
							if pi == q:
								paym[i] = who2


			s = s + 1
			
			if s > len(paym):
				break
		
		return paym
	else:
		print("ok - few subjects, payments all equalized", file = sys.stderr)
		
		paym = [max(paym) for _ in paym]

		return paym

def SPA(paym, attr, eta):
	if eta > 0 and eta < 1 and len(paym) > 3 and count(attr, 1) > 0 and count(attr, 0) > 0:
		s = 1
		hadUniq = hadUniqPaym(paym)

		while True:
			if s == 1:
				rank = [sum([1 for pi2 in paym if pi2 >= pi]) for pi in paym]

			if count(rank, s) > 0:
				q = [paym[i] for (i, r) in enumerate(rank) if r == s][0]

				if count(attr, 1)/len(paym) > eta:
					print("ERROR: too many attribute bearers, infeasible", file = sys.stderr)
					
					break
				else:
					while P(paym, attr, q) > eta:
						if any([pi < q for (i, pi) in enumerate(paym) if attr[i] == 0]) or any([pi > q for (i, pi) in enumerate(paym) if attr[i] == 0]):
							who1 = max([pi for (i, pi) in enumerate(paym) if pi < q and attr[i] == 0], default = -math.inf)
							who2 = min([pi for (i, pi) in enumerate(paym) if pi > q and attr[i] == 0], default = +math.inf)
							
							c = sum([1 for (i, pi) in enumerate(paym) if pi == who1 and attr[i] == 0])
							
							if c > 0 and c*(q-who1) <= count(paym, q)*(who2-q):
								for (i, pi) in enumerate(paym):
									if pi == who1 and attr[i] == 0:
										paym[i] = q
										break
									
								s = 0
								break
							else:
								for (i, pi) in enumerate(paym):
									if pi == q:
										paym[i] = who2
								
								s = 0
								break
						else:
							print(f"ERROR: no valid candidates", file = sys.stderr) # should be impossible
							break
					
					if s == len(paym) and not hadUniq:
						if any([count(paym, pi) == 1 for pi in paym]):
							paym = NUN(paym)
							s = 0

			s = s + 1
			
			if s > len(paym):
				break
		
		return paym
	elif eta <= 0 or eta >= 1:
		print("(disabled)", file = sys.stderr)

		return paym
	elif len(paym) <= 3:
		paym = [max(paym) for _ in paym]
		
		print("err - few subjects, payments all equalized", file = sys.stderr)
		
		return paym
	else:
		print("ok - inactive", file = sys.stderr)

		return paym
