import pyopencl as cl

#Returns the list of platforms and associated devices. If none are available, returns an empty list
def GetPlatformsAndDevices():

    try:
        platforms = cl.get_platforms()
    except:
        return []

    p = []
    for platform in platforms:
        d = {}
        name = platform.get_info(cl.platform_info.NAME)
        d["name"] = name
        
        try:
            devices = platform.get_devices()
        except:
            return []

        dlist=[]
        for device in devices:
            name = device.get_info(cl.device_info.NAME)

            dp = device.get_info(cl.device_info.PREFERRED_VECTOR_WIDTH_DOUBLE)
            if dp > 0:
                dp = True
            else:
                dp = False

            dlist.append({"name": name, "double_precision": dp})
        d["devices"] = dlist

        p.append(d)
    
    return p

if __name__ == "__main__":
    print(GetPlatformsAndDevices())