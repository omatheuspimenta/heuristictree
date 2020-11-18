import quick_tree as qt

def tree(L,n,l,d,smallitem = 0):
    #Initial Parameters
    n = len(d)
    soma = small = leftover = loss = 0
    L_hat = L
    bar = 0
    x_ret = []
    smallitem = smallitem
    
    #Sorting
    qt.quickSort(l,d,0,n-1)
    
    #Put together items of the same size
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
    
    #Sum of Demand Items
    for i in range(n):
        soma = soma + d[i]
    
    #small item
    if smallitem == 0:
        small_ = l[n-1]
    else:
        small_ = smallitem
    
    print("small_",small_)
    #Begin
    while (soma > 0 ):
        x_ini = [0]*n
        x = [0]*n
        x_aux = [0]*n
        x_fix = [0]*n
        small = l[n-1]
        #First branch
        for i in range(n):
            y = int(L_hat/l[i])
            if(y > d[i]):
                y = d[i]
            x_ini[i] = y
            L_hat = L_hat - (x_ini[i] * l[i])
            if((L_hat < small) or L_hat == 0):  
                break
        cont = 1
        L_aux = L
        x_aux[0] = x_ini[0]
        x = x_ini
        while((L_aux != 0) and (cont != n )):
            x_fix = [0]*n
            ra = -1                 
            if(x_aux[cont-1] != 0):
                x_fix[cont-1] = x_aux[cont-1] - 1   
            else:
                x_fix[cont-1] = 0           
            L_fix = L - (l[cont-1]*x_fix[cont-1]) 
            L_aux = L_fix
            x_aux = x_fix
            for j in range(cont,n):
                if(l[j] != -1):
                    y = int(L_aux/l[j])
                    if(y > d[j]):
                        y = d[j]
                    x_aux[j] = y
                    L_aux -= (x_aux[j] * l[j])
                    if(L_aux > l[cont]):
                        if(L_aux in l[0:cont]):
                            ra = l.index(L_aux)
                            x_aux[ra] = 1
                            L_aux = 0
                        else:
                            for ind in range(cont):
                                if( ((L_aux - l[ind]) >= 0) and ((L_aux - l[ind]) < L_hat)):
                                    L_aux = (L_aux - l[ind])
                                    x_aux[ind] = 1
                                    break                                
            if(L_aux < L_hat):
                L_hat = L_aux
                x = x_aux
            cont = cont + 1
        x_ret.append(x)
        
        sum_x = 0    
        for i in range(n):
            sum_x = sum_x + x[i]
            d[i] = d[i] - x[i]
        
        #Remove null demands
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
        
        #Add Loss, Leftover and Bar
        if(L_hat < small_): 
            loss += L_hat
            L_hat = L
        else:
            leftover += L_hat
            L_hat = L
            
        soma = soma - sum_x
        bar += 1
    return(leftover, loss, bar-1, x_ret)