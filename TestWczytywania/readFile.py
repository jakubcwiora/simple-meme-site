from sympy.parsing.latex import parse_latex
import sympy as sp

with open("input.md", 'r') as file:
  line = file.readline()
  line = line.strip().replace('$', '')
  PhysQuantity = line[0]
  eq = line[line.find('=')]
  equation = parse_latex(eq)

# print(equation)
x = sp.symbols('x')
y = x ** 2 - 5 * x + 6
print(sp.latex(eq))