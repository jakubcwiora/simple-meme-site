lines = []
i = 0
with open("input1.md", 'r') as input:
  for line in input:
    i += 1
    line = line.strip()
    lines.append(f"{i}. Line: " + line)

i = 0

with open("output.md", 'w') as output:
  for line in lines:
    output.write(line + '\n')