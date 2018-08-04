import os

t = open('comparison.txt','a')
s = open('detailed_data.txt','r')
i=1
for lines in s:
	t.write(lines)
	if(i%3==0):
		t.write('\n')
	i+=1

t.close()
s.close()
