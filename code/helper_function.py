import numpy as np

# helper functions
# make triad within range C2-C6 (4 octaves)
def bound_triad(notes):
    for i in range(3):
        note = notes[i]
        if note < 36:
            notes[i] += 12
        elif note > 84:
            notes[i] -= 12
    return notes 
            
# make triad into open chords
def open_triad(notes):
    return np.array([notes[0]%12+36,notes[1]%12+48,notes[2]%12+60]) 
            

# calculate if two lines intersect
def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

# Return true if line segments AB and CD intersect
def intersect(A,B,C,D):
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

# another way
def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

def intersect2(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y
    
# transformation
def make_trans(mode,triad,key,trans='p',print=False):
    '''mode: 1 if major, 0 if minor
       triad: a list of three notes forming a triad
       key: current key '''
    trans_type = trans.lower()
    assert trans_type in ['p','r','l']
    assert len(triad) == 3

    # parallel transformation
    if trans_type == 'p':
        if mode == 1:
            triad[1] -= 1
            mode = 0
        else:
            triad[1] += 1
            mode = 1

    # relative transformation
    elif trans_type == 'r':
        if mode == 1:
            key -= 3
            mode = 0
            # move fifth up a tone
            triad[2] += 2
        else:
            key += 3
            mode = 1
            # move root down a tone
            triad[0] -= 2


    # leading-tone exchange
    else:
        if mode == 1:
            key += 4
            mode = 0
            # move root down a semitone
            triad[0] -= 1
        else:
            key -= 4
            mode = 1
            # move fifth up a semitone
            triad[2] += 1


    # make sure pitch is in the valid range 
    key = key % 12 + 60
    # rearrange triad
    temp = (triad - key)%12
    triad = np.array([x for _, x in sorted(zip(temp, triad))])

    # check if calculation is correct, removed for optimization
    # if mode == 1:
    #     calc_triad = key + np.array([0,4,7])
    # else:
    #     calc_triad = key + np.array([0,3,7])
    # if print:
    #     print('sorted triad:',triad)
    #     print('pitch triad:',calc_triad)
    # assert np.array_equal(triad % 12, calc_triad % 12)

    return mode, open_triad(triad), key
