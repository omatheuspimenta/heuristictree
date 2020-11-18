import sys
import os
import fnmatch
from time import process_time
sys.setrecursionlimit(20000)

def tree(fin,fout):
    arq = open(fin,"r")
    out = open(fout,"a+")
    
    ## ORDENANDO POR ORDEM DECRESCENTE
    def partition(arr,seg,low,high): 
        i = ( low-1 )         # index of smaller element 
        pivot = arr[high]     # pivot 
      
        for j in range(low , high): 
            # If current element is smaller than or 
            # equal to pivot 
            if   arr[j] >= pivot: 
                # increment index of smaller element 
                i = i+1 
                arr[i],arr[j] = arr[j],arr[i] 
                seg[i],seg[j] = seg[j],seg[i]
      
        arr[i+1],arr[high] = arr[high],arr[i+1]
        seg[i+1],seg[high] = seg[high],seg[i+1]
        return ( i+1 ) 
    
    def quickSort(arr,seg,low,high): 
        if low < high: 
            # pi is partitioning index, arr[p] is now 
            # at right place 
            pi = partition(arr, seg,low,high) 
            
            # Separately sort elements before 
            # partition and after partition 
            quickSort(arr, seg, low, pi-1) 
            quickSort(arr, seg, pi+1, high) 
    
    ## CARREGANDO O ARQUIVO
    l = []
    d = []
    
    for line in arq:
        if(line[0] == "L" and line[1] == ":"):
            L = int(line[2:20])
        if(line[0] == "n" and line[1] == ":"):
            n = int(line[2:20])
        if(line[0] == "l" and line[1] == ":"):
            aux = line.split(" ")
            j = 1
            while(j < len(aux)):
                l.append(int(aux[j]))
                j += 1
        if(line[0] == "d" and line[1] == ":"):
            aux = line.split(" ")
            j = 1
            while(j < len(aux)):
                d.append(int(aux[j]))
                j += 1
    arq.close()
    ## FIM DO CARREGAMENTO DO ARQUIVO
    
    ## START TIME
    start_time = process_time()
    
    quickSort(l,d,0,n-1)
    
    ## UNINDO VALORES IGUAIS PARA DIMINUIR O TAMANHO DO VETOR
    ### MEXER
    i=0
    while i<(n-1):
        if l[i]==l[i+1]:
            d[i]=d[i]+d[i+1]
            l.pop(i+1)
            d.pop(i+1)
            n=n-1
        else:
            i=i+1
        if i==n:
            break
    n=len(d)
    
    ## START HEURISTIC
    soma = small = leftover = loss = 0
    L_hat = L
    bar = 0
    
    #SUM OF DEMAND ITEMS
    for i in range(n):
        soma = soma + d[i]
    
    ##DEFINI COMO VALOR DE PERDA OU SOBRA O MENOR ITEM
    small_ = l[n-1]
    
    ##INICIO DA HEURISTICA
    while (soma > 0 ):
        x_ini = [0]*n               # iniciando os vetores (talvez possa diminuir um vetor)
        x = [0]*n
        x_aux = [0]*n
        x_fix = [0]*n
        for i in range(n-1,-1,-1):  # definindo quem é o menor item ativo da barra
            if(l[i] != -1):
                small = l[i]
                break
        
        for i in range(n):          # primeiro ramo da arvore
            y = int(L_hat/l[i])
            if(y > d[i]):
                y = d[i]
            x_ini[i] = y
            L_hat = L_hat - (x_ini[i] * l[i])
            if((L_hat < small) or L_hat == 0):  
                break           # CONDIÇÃO DE PARADA DO PRIMEIRO RAMO
        cont = 1
        L_aux = L
        x_aux[0] = x_ini[0]         # PASSO SOMENTE O PRIMEIRO VALOR PARA O NOVO RAMO
        x = x_ini                   # guardo para o caso de ser a melhor solucao ate o momento
        while((L_aux != 0) and (cont != n )):   #condicoes de parada ou sobra nula ou final da arvore
            x_fix = [0]*n
            ra = -1                 # VALOR DO INDICE CASO OCORRA SOBRA == VALOR EXISTENTE
            if(x_aux[cont-1] != 0):
                x_fix[cont-1] = x_aux[cont-1] - 1   # REMOVENDO UMA UNIDADE DO MAIOR ITEM DO RAMO ANTERIOR
            else:
                x_fix[cont-1] = 0           # NÃO REMOVER CASO JA SEJA 0
            L_fix = L - (l[cont-1]*x_fix[cont-1]) # liberar espaço na mochila
            L_aux = L_fix
            x_aux = x_fix
            for j in range(cont,n):     # criacao dos outros ramos
                if(l[j] != -1):
                    y = int(L_aux/l[j])
                    if(y > d[j]):
                        y = d[j]
                    x_aux[j] = y
                    L_aux -= (x_aux[j] * l[j])
                    if(L_aux > l[cont]):
                        if(L_aux in l[0:cont]): # se a sobra for igual a algum item anterior colocar esse item
                            ra = l.index(L_aux)
                            x_aux[ra] = 1
                            L_aux = 0
                        else:
                            for ind in range(cont):
                                if( ((L_aux - l[ind]) >= 0) and ((L_aux - l[ind]) < L_hat)):
                                    L_aux = (L_aux - l[ind])
                                    x_aux[ind] = 1
                                    break                                
            if(L_aux < L_hat): # se a sobra é melhor que a menor sobra atual entao é a melhor solucao ate o momento
                L_hat = L_aux
                x = x_aux
            cont = cont + 1
                
        sum_x = 0    
    
        for i in range(n):
            sum_x = sum_x + x[i]
            d[i] = d[i] - x[i]
        i = 0
        while i <= (n-1):
            if(d[i] == 0):
                l.pop(i)
                d.pop(i)
                n = n-1
            else:
                i=i+1
            if i==n:
                break
        n = len(d) 
        
        if(L_hat < small_): # determinando se é sobra ou perda
            loss += L_hat
            L_hat = L
        else:
            leftover += L_hat
            L_hat = L
            
        soma = soma - sum_x
        bar += 1
    
    # END TIME
    end_time = process_time()
    ex_time = end_time - start_time
    
    ##WRITE IN FILE
    out.write(file)
    out.write("\n")
    out.write("leftover;")
    out.write(str(leftover))
    out.write("\n")
    out.write("loss;")
    out.write(str(loss))
    out.write("\n")
    out.write("bar;")
    out.write(str(bar))
    out.write("\n")
    out.write("time;")
    out.write(str(ex_time))
    out.write("\n")
    out.close()


for file in os.listdir('.'):
    if fnmatch.fnmatch(file, '*.dat'):
        print("Loading...",file)
        aux = 'PPL_tree.txt'
        tree(file,aux)    