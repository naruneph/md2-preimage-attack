import sys

BLOCK_SIZE = 16
S = [1, 3, 0, 2]

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
            t = newX[j] ^ S[t] 
            newX[j]  = t 
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


def strToIntList(str):
    tmp = str.split()
    lst = []
    for item in tmp:
        lst.append(int(item))
    return lst




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

        
    
    





    

    
