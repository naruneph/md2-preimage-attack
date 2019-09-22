import sys
import itertools
from multiprocessing import Pool
import time

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
    return itertools.product(values, repeat = num)
    
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
    X = [0] * (3 * BLOCK_SIZE)
    for i in range(16):
        X[i] = H[i]
    return F(M,X)[:16]

def check(Halves, H_cur, H_next):    
    for left in Halves[0]:
        for right in Halves[1]:
            msg = left + right
            if(H_next == compress(H_cur, msg)):
                return msg
    return None

def checkThisTable(T,H_cur,H_next):
    for item in T:
        if (len(item[0]) > 0) and (len(item[1]) > 0):
            preimage = check(item, H_cur, H_next)
            if(preimage):
                return preimage
        
def compute_A(A, H_cur, H_next, C_1_15):
    A[0] = H_cur[:]
    A[18] = H_next[:]

    # Computing first row of A
    t = 0
    for i in range(BLOCK_SIZE):
        A[1][i] = A[0][i] ^ S[t]
        t = A[1][i]

    # Computing lower right triangle of A
    k = 1
    for i in reversed(range(3,18)):
        for j in range(k, BLOCK_SIZE):
            A[i][j] = A[i+1][j] ^ S[A[i+1][j-1]]
        k += 1

    # Dealing with second row of A
    t = C_1_15
    for i in range(BLOCK_SIZE):
        A[2][i] = A[1][i] ^ S[t]
        t = A[2][i]

    # The last part of A
    k = 16
    for i in range(3, 18):
        for j in reversed(range(1, k)):
            sboxValue= A[i][j] ^ A[i-1][j]
            A[i][j-1] = S.index(sboxValue)
        k -= 1    

def defineRightCol_C(C, A):
    # Defining right column of C
    for i in range(2, 5):
        sboxValue = (A[i][0] ^ A[i+1][0])
        C[i][15] = (S.index(sboxValue) - (i - 1) + 4 ) % 4
    
def leftPart(val, A, B, C, T):
    # Fixing B[0][0] - B[0][7] 
    for i in range(8):
        B[0][i] = val[i]

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
    if( not (key_1 in T) ):
        T[key_1] = ([val],[])
    else:
        T[key_1][0].append(val)

def rightPart(val, A, B, C, T):
    # Fixing B[0][8] - B[0][15] 
    for i in range(8, 16):
        B[0][i] = val[i - 8]

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
    if( not (key_2 in T) ):
        T[key_2] = ([],[val])
    else:
        T[key_2][1].append(val)

def test(tryingToGuess, A, B, C, H_cur, H_next):
    for value in tryingToGuess:
        print(value)
        C[1][15] = value[0]
        for i in range(1, 5):
                B[i][15] = value[5 - i]

        compute_A(A, H_cur, H_next, C[1][15])
        defineRightCol_C(C, A)

        T = {}

        B_0_val = generateAllPossibleVariants(8)
        for val in B_0_val:
            leftPart(val, A, B, C, T)
            rightPart(val, A, B, C, T)

        result = checkThisTable(T.values(),H_cur,H_next)
        if result:
            return checkThisTable(T.values(),H_cur,H_next)

def preimage(H_cur, H_next):
    A = [[-1 for i in range(BLOCK_SIZE)] for j in range(19)]
    B = [[-1 for i in range(BLOCK_SIZE)] for j in range(5)]
    C = [[-1 for i in range(BLOCK_SIZE)] for j in range(5)]

    print("Checking (C[1][15], B[4][15], B[3][15], B[2][15], B[1][15])")

    tryingToGuess = list(generateAllPossibleVariants(5))

    pool = Pool(processes=3)
    vals = tryingToGuess
    parts = [[],[],[]]

    for i in range(len(vals)):
        if i % 3 == 0:
            parts[0].append(vals[i])
        elif i % 3 == 1:
            parts[1].append(vals[i])
        else: 
            parts[2].append(vals[i])

    hnds = []
    for part in parts:
        hnds.append(pool.starmap_async(test, [(part, A, B, C, H_cur, H_next)]))

    whenToStop = [0] * len(hnds)
    while True:
        for hnd in hnds:
            if hnd.ready():
                whenToStop[hnds.index(hnd)] = 1
                res = hnd.get() 
                if res[0] != None: 
                    pool.terminate()
                    pool.join()
                    return res[0]
        if 0 not in whenToStop:
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
        start_time = time.time()
        H_cur = strToIntList(sys.argv[2])
        H_next = strToIntList(sys.argv[3])
        print(' '.join(map(str, preimage(H_cur, H_next))))
        print("--- %s seconds ---" % (time.time() - start_time))