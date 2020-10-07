import pyopencl as cl
import numpy as np
import time
import sys
import numba
import matplotlib.pyplot as plt
import os

nx = 1000
ny = 1000


class Mandelbrot():
    def __init__(self,platform=0,device=2):
        #If the platform is < 0 we request to use the fallback
        if platform < 0:
            self.fallback = True
            print("Using Numba Python fallback")
        #setup OpenCL
        else: 
            self.fallback = False
            #get platform
            platforms = cl.get_platforms()
            try:
                p = platforms[platform]
            except IndexError:
                print("Error: platform %d does not exist"%platform)
            print("Using platform %s"%p.get_info(cl.platform_info.NAME))

            self.platform = p
            
            #get device
            devices = p.get_devices()
            try:
                d = devices[device]
            except IndexError:
                print("Error: device %d does not exist"%device)
            print("Using device %s"%d.get_info(cl.device_info.NAME))

            self.device=d
            
            #set up context 
            self.context = cl.Context(devices=[self.device])
        
            #set up command queue
            self.queue = cl.CommandQueue(self.context,properties=cl.command_queue_properties.PROFILING_ENABLE)
            
            curpath = os.path.dirname(os.path.abspath(__file__))

            #read program source
            f=open(os.path.join(curpath,"mandelbrot.cl"),"r")
            src=f.read()
            f.close()
            
            #create program
            self.program = cl.Program(self.context,src)
            self.program.build()
        



    def calculate(self,xmin=-2,xmax=1,ymin=-1.5,ymax=1.5,double=False,nx=1000,ny=1000):

        dx = (xmax-xmin)/nx
        dy = (ymax-ymin)/ny
        
        #use the python fallback
        if self.fallback:
            print('Calculating discrete mandelbrot set (Numba fallback)')
            tstart = time.time()
            img = int_mandelbrot(xmin,dx, ymin,dy,nx,ny)
            tstop = time.time()
            print("Time taken = %fms"%((tstop-tstart)*1000))
            return img

        #create data buffers
        img = np.zeros(nx*ny,np.int32)
        imgBuf = cl.Buffer(self.context,cl.mem_flags.WRITE_ONLY,img.nbytes)

        
        #run kernel on GPU
        if double == False:
            print("Calculating discrete mandelbrot set using single precision numbers")
            event=self.program.mandelbrot_float(self.queue,(nx,ny),None,imgBuf,np.float32(xmin),np.float32(dx),np.float32(ymin),np.float32(dy),np.int32(nx),np.int32(ny))
        else:
            print("Calculating discrete mandelbrot set using double precision numbers")
            event=self.program.mandelbrot_double(self.queue,(nx,ny),None,imgBuf,np.float64(xmin),np.float64(dx),np.float64(ymin),np.float64(dy),np.int32(nx),np.int32(ny))
        
        
        #wait for it to complete
        event.wait()

        copyevt=cl.enqueue_copy(self.queue,img,imgBuf)

        img = img.reshape((nx,ny))
        try:
            tstart=event.get_profiling_info(cl.profiling_info.START)
            tstop = event.get_profiling_info(cl.profiling_info.END)
            print("Kernel execution time = %f ms"%((tstop-tstart)/1E6))

            tstart=copyevt.get_profiling_info(cl.profiling_info.START)
            tstop = copyevt.get_profiling_info(cl.profiling_info.END)
            print("Copy time = %f ms"%((tstop-tstart)/1E6))
        except cl._cl.RuntimeError as e:
            print(e)
        
        return img

    def calculate_real(self,xmin=-2,xmax=1,ymin=-1.5,ymax=1.5,double=False,nx=1000,ny=1000):
        
        dx = (xmax-xmin)/nx
        dy = (ymax-ymin)/ny
        
        #use the python fallback
        if self.fallback:
            print('Calculating continuous mandelbrot set (Numba fallback)')
            tstart = time.time()
            img = real_mandelbrot(xmin,dx, ymin,dy,nx,ny)
            tstop = time.time()
            print("Time taken = %fms"%((tstop-tstart)*1000))
            return img

        rimg = np.zeros(nx*ny,dtype=np.float32)
        rimgBuf = cl.Buffer(self.context,cl.mem_flags.WRITE_ONLY,rimg.nbytes)

        
        #run kernel on GPU
        if double == False:
            print("Calculating continuous mandelbrot set using single precision numbers")
            event=self.program.real_mandelbrot_float(self.queue,(nx,ny),None,rimgBuf,np.float32(xmin),np.float32(dx),np.float32(ymin),np.float32(dy),np.int32(nx),np.int32(ny))
        else:
            print("Calculating continuous mandelbrot set using double precision numbers")
            event=self.program.real_mandelbrot_double(self.queue,(nx,ny),None,rimgBuf,np.float64(xmin),np.float64(dx),np.float64(ymin),np.float64(dy),np.int32(nx),np.int32(ny))
        
        
        #wait for it to complete
        event.wait()

        copyevt=cl.enqueue_copy(self.queue,rimg,rimgBuf)

        rimg = rimg.reshape((nx,ny))

        try:
            tstart=event.get_profiling_info(cl.profiling_info.START)
            tstop = event.get_profiling_info(cl.profiling_info.END)
            print("Kernel execution time = %f ms"%((tstop-tstart)/1E6))

            tstart=copyevt.get_profiling_info(cl.profiling_info.START)
            tstop = copyevt.get_profiling_info(cl.profiling_info.END)
            print("Copy time = %f ms"%((tstop-tstart)/1E6))
        except cl._cl.RuntimeError as e:
            print(e)

        # print(rimg.max(), rimg.min())
        
        return rimg

@numba.jit(nopython=True)
def int_mandelbrot(xmin, dx, ymin, dy, nx, ny):
    out = np.zeros((ny,nx),dtype=np.int32)

    for j in range(ny):
        y0 = ymin + (j+0.5)*dy
        for i in range(nx):
            n=0

            x=0.
            y=0.

            x0 = xmin + (i+0.5)*dx
            

            while(n < 256):
                n+=1

                z2 = x

                x = x*x - y*y + x0
                y = 2.*z2*y + y0

                z2 = x*x + y*y

                if z2 > 4:
                    break
            
            out[j,i] = n
    return out


@numba.jit(nopython=True)
def real_mandelbrot(xmin, dx, ymin, dy, nx, ny):
    out = np.zeros((ny,nx),dtype=np.float32)

    ln2 = np.log(2.)

    for j in range(ny):
        y0 = ymin + (j+0.5)*dy
        for i in range(nx):
            n=0

            x=0.
            y=0.

            x0 = xmin + (i+0.5)*dx
            

            while(n < 256):
                n+=1

                z2 = x

                x = x*x - y*y + x0
                y = 2.*z2*y + y0

                z2 = x*x + y*y

                if z2 > 100:
                    break
            
            if n == 256:
                out[j,i] = float(n)
            else:
                out[j,i] = n + 2. - np.log(np.log(z2))/ln2;
    return out








if __name__ == "__main__":
    # m=Mandelbrot()

    # img = m.calculate()

    nx = 1000
    ny = 1000


    tstart = time.time()
    img = real_mandelbrot(-2.,4./nx, -2, 4./ny,nx,ny)
    tstop = time.time()
    print("Time = %f"%(tstop-tstart))
    tstart = time.time()
    img = real_mandelbrot(-2.,4./nx, -2, 4./ny,nx,ny)
    tstop = time.time()
    print("Time = %f"%(tstop-tstart))

    plt.imshow(img,origin="lower")
    plt.show()