import os
CESTA_K_MINISAT = "minisat"

class NQueens():
    def solve(self, n):
        if n == 0:
            return []
        if n == 1:
            return [(1,1)]
        try:
            with open("vstup.txt", "w") as o:
                zapis_problem(o, n)
        except IOError as e:
            print("Chyba pri vytvarani vstupneho suboru ({0}): {1}".format(
                    e.errno, e.strerror))
            return 1
        
        os.system("{} vstup.txt vystup.txt".format(CESTA_K_MINISAT));
        riesenie=[]
        try:
            with open("vystup.txt", "r") as i:
                sat = i.readline()
                if sat == "SAT\n":
                    ries = i.readline()
                    riesenie = formatuj(ries.split(), n)
                else:
                    print("Ziadne riesenie")
        except IOError as e:
            print("Chyba pri nacitavani vystupneho suboru ({0}): {1}".format(
                    e.errno, e.strerror))
            return 1
        return riesenie
    
def decode(qn,n):
    x= (int(n)-1)%qn
    y= int((int(n)-1) / qn) 
    return (x,y)
    
def formatuj(arr,qn):
    res=[]
    print(arr)
    for a in arr:
        if not ("-") in a:
            if a!='0':
                res.append(decode(qn,a))
    return res
    
def impl(subor, a, b):
    subor.write( "{0:d} {1:d} 0\n".format(-a, b) )

def zapis_riadok(subor, qn, n):
    for i in range(qn*(n-1)+1,qn*(n-1)+qn+1):
        subor.write( "{0:d} ".format(i) )   
    subor.write("0\n")
    for i in range(qn*(n-1)+1,qn*n+1):
        for j in range(i+1,qn*n+1):
            impl(subor, i, -j)

def zapis_stlpec(subor, qn, n): 
    for i in range(1,qn+1):
        for j in range(i,qn-1):
           #print(str(i) + " "+ str(j))
            impl(subor, (i-1)*(qn-1)+n, -((j)*(qn-1)+n))

def zapis_uhlopriecky(subor, qn):
    #\\
    for i in range(1,qn+1):
        for j in range(i,):
            impl(subor, (i-1)*(qn-1)+n, -(i+1))
    return
  
def zapis_problem(subor, qn):
    for riadok in range(1, qn+1):
        zapis_riadok(subor, qn, riadok)
    for stlpec in range(1, qn+1):
        zapis_stlpec(subor, qn+1, stlpec)
    #zapis_uhlopriecky(subor, qn)  

##q=NQueens()
##print(q.solve(4))
