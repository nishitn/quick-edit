import os

t = open('comparison.txt','a')
t2 = open('comparison.html','a')
s = open('detailed_data.txt','r')
i=1
for lines in s:
	t.write(lines)
	t2.write(lines)
	t2.write('<br>')
	if(i%3==0):
		t.write('\n')
		t2.write('<br>')
	i+=1

t.close()
t2.close()
s.close()
