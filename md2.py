import sys
import itertools

BLOCK_SIZE = 16
S = [1, 3, 0, 2]

def strToIntList(str):
    tmp = str.split()
    lst = []
    for item in tmp:
        lst.append(int(item))
    return lst

def generateAllPossibleVariants(num):
    values = [0, 1, 2, 3]
    return list(itertools.product(values, repeat = num))
    
def pad(buf):
    padLength = BLOCK_SIZE - (len(buf) % BLOCK_SIZE)
    for i in range(padLength):
        buf.append(padLength % 4)

def appendChecksum(buf):
    C = [0] * BLOCK_SIZE
    L = 0 
    for i in range(len(buf) // BLOCK_SIZE):
        for j in range(BLOCK_SIZE):
            c = buf[i * BLOCK_SIZE + j]
            C[j] ^= S[c ^ L] 
            L = C[j]
    buf.extend(C)

def F(msgBlock, X):
    newX = X[:]
    for i in range(BLOCK_SIZE):
        b = msgBlock[i]
        newX[BLOCK_SIZE + i] = b
        newX[2 * BLOCK_SIZE + i] = b ^ newX[i]
    t = 0
    for i in range(18):
        for j in range(len(newX)):
            newX[j] = newX[j] ^ S[t] 
            t = newX[j]
        t = (t + i) % 4
    return newX

def md2(m):
    msg = m[:]
    pad(msg)
    appendChecksum(msg)
    X = [0] * 3 * BLOCK_SIZE
    for i in range(len(msg) // BLOCK_SIZE):
        block = msg[i * BLOCK_SIZE : (i + 1) * BLOCK_SIZE]
        X = F(block, X)
    return X[:16]

def compress(H, M):
    X = [0] * 3 * BLOCK_SIZE
    for i in range(16):
        X[i] = H[i]
    return F(M,X)[:16]

def preimage(H_cur, H_next):
    A = [[-1 for i in range(BLOCK_SIZE)] for j in range(19)]
    B = [[-1 for i in range(BLOCK_SIZE)] for j in range(5)]
    C = [[-1 for i in range(BLOCK_SIZE)] for j in range(5)]

    A[0] = H_cur[:]
    A[18] = H_next[:]

    # Computing first row of A
    t = 0
    for i in range(BLOCK_SIZE):
        A[1][i] = A[0][i] ^ S[t]
        t = A[1][i]

    # Computing lower right triangle of A
    k = 1
    for i in reversed(range(2,18)):
        for j in range(k, BLOCK_SIZE):
            A[i][j] = A[i+1][j] ^ S[A[i+1][j-1]]
        k = k + 1


    counter = 0

    # Fixing C[1][15] 
    for val in range(4):
        C[1][15] = val

        # Dealing with second row of A
        t = (C[1][15] + 1) % 4
        for i in range(BLOCK_SIZE):
            A[2][i] = A[1][i] ^ S[t]
            t = A[2][i]

        # The last part of A
        k = 16
        for i in range(3, 18):
            for j in reversed(range(k)):
               sboxValue= A[i][j] ^ A[i-1][j]
               A[i][j-1] = S.index(sboxValue)

        # Defining right column of C
        for i in range(2, 5):
            sboxValue = (A[i][0] ^ A[i+1][0])
            C[i][15] = (S.index(sboxValue) - i + 4 ) % 4

        # Fixing B[1][15] - B[4][15]
        B_values = generateAllPossibleVariants(4)
        for val in B_values:

            print("#############################################################################################################################")
            print(counter)
            counter = counter + 1

            for i in range(1, 5):
                B[i][15] = val[i - 1]

            T = {} # key: (B[1][7]-B[4][7], C[1][7]-C[4][7]), value: ["a"/"b"/"c", L/R half of message, ...] b - only Left parts result in key,
                   #                                                                                         c - only Right parts,
                   #                                                                                         a - left and right parts produce the key.

            B_0_values = generateAllPossibleVariants(8)

            for val_ in B_0_values:

                ########## Fixing B[0][0] - B[0][7] ##########
                for i in range(8):
                    B[0][i] = val_[i]
                
                # Defining C[0][1] - C[0][7]
                for i in range(8):
                    C[0][i] = B[0][i] ^ A[0][i]

                # Computing B[1][7] - B[4][7]
                for i in range(1, 5):
                    t = A[i][15]
                    for j in range(8):
                        B[i][j] = B[i - 1][j] ^ S[t]
                        t = B[i][j]

                # Computing C[1][7] - C[4][7]
                for i in range(1, 5):
                    t = B[i][15]
                    for j in range(8):
                        C[i][j] = C[i - 1][j] ^ S[t]
                        t = C[i][j]

                # Filling in T_1
                T_1_value = []
                for i in range(1,5):
                    T_1_value.append(B[i][7])
                for i in range(1,5):
                    T_1_value.append(C[i][7])

                key_1 = str(T_1_value)

                if( not(key_1 in T) ):
                    T[key_1] = ["b"]
                elif( T[key_1][0] == "c" ):
                    T[key_1][0] = "a"
                T[key_1].append("L" + str(val_))

                
                ########## Fixing B[0][8] - B[0][15] ##########
                for i in range(8, 16):
                    B[0][i] = val_[i - 8]

                # Defining C[0][8] - C[0][15]
                for i in range(8, 16):
                    C[0][i] = B[0][i] ^ A[0][i]

                # Computing B[1][7] - B[4][7]
                for i in range(1, 5):
                    for j in reversed(range(8, 16)):
                        sboxValue= B[i][j] ^ B[i-1][j]
                        B[i][j-1] = S.index(sboxValue)

                # Computing C[1][7] - C[4][7]
                for i in range(1, 5):
                    for j in reversed(range(8, 16)):
                        sboxValue= C[i][j] ^ C[i-1][j]
                        C[i][j-1] = S.index(sboxValue)

                # Filling in T_2
                T_2_value = []
                for i in range(1,5):
                    T_2_value.append(B[i][7])
                for i in range(1,5):
                    T_2_value.append(C[i][7])

                key_2 = str(T_2_value)

                if( not(key_2 in T) ):
                    T[key_2] = ["c"]
                elif (T[key_2][0] == "b"):
                    T[key_2][0] = "a"
                
                T[key_2].append("R" + str(val_))

                
            ########## Sorting the table alphabetically by value ##########
            for item in sorted(T.items(), key = lambda x: x[1][0], reverse = False):
                # print(item)
                # print(item[1][0])
                if (item[1][0] == "a"):
                    print(item)
                    return
                else: # запустить внешний цикл со следующим значением
                    break
                

if (__name__ == "__main__"):

    mode = sys.argv[1]

    if(mode == "md2"):
        msg = []
        for i in range(2, len(sys.argv)):
            tmp = strToIntList(sys.argv[i])
            msg.extend(tmp)
        print(' '.join(map(str, md2(msg))))
    
    if(mode == "compress"):
        H = strToIntList(sys.argv[2])
        M = strToIntList(sys.argv[3])
        print(' '.join(map(str, compress(H,M))))

    if(mode == "preimage"):
        H_cur = strToIntList(sys.argv[2])
        H_next = strToIntList(sys.argv[3])
       # print(' '.join(map(str, preimage(H_cur, H_next))))
        preimage(H_cur, H_next)
        
        
    
    





    

    
