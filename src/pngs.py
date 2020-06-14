import glob

#Returns the name of the next available imagename. OF the form "img*.png", where * is a number
def GetNextFile():
    allimages = glob.glob("img*.png")

    nums=[]
    for imgfile in allimages:
        s=""
        for char in imgfile:
            if char.isdigit():
                s+=char
        if len(s) > 0:
            i = int(s)
            nums.append(i)

    nums.sort()

    if len(nums) == 0:
        numstring = ""
    else:
        numstring = str(nums[-1]+1)

    fname = "img%s.png"%numstring

    return fname

#returns the metadata from the tEXt chunks, as a dictionary of keys and values
def GetImageMetadata(filename):
    f=open(filename,"rb")

    num=f.read(8)
    if num != bytearray.fromhex("89504e470d0a1a0a"):
        return None
    
    metadata={}
    while True:
        chunk = getNextChunk(f)
        if chunk["name"] == "tEXt":
            # print("tEXt")
            key, value = parse_tEXt(chunk)
            metadata[key] = value
        if chunk["name"]=="IEND" or chunk["name"]=="":
            # print("IEND REACHED")
            break
    f.close()

    return metadata


#parses the tEXt chunk, returning they key and the value contained within
def parse_tEXt(chunk):
    data = chunk["data"]
    i=0
    #we look for the null byte, which is the seperator between the key and value
    for b in data:
        if b == 0:
            break
        i+=1
    

    key = data[:i].decode("ascii")
    value = data[i+1:].decode("ascii")

    return key, value

    
#reads in a chunk, returning its name, byte count and data in a dictionary
def getNextChunk(f):
    nbytes = f.read(4)
    n = int.from_bytes(nbytes,"big")
    name = f.read(4).decode("ascii")
    data = f.read(n)
    crc = f.read(4)
    d={
        "name": name,
        "count": n,
        "data": data
    }
    return(d)



if __name__ == "__main__":
    print(GetNextFile())
    print(GetImageMetadata("img11.png"))