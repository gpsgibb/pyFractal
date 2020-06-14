//Calculates the Mandelbrot set 

//output: out (the image array)
//inputs: xmin, ymin  (x and y start coordinates)
//inputs dx, dy  (pixel size in x and y)
//inputs:  nx, ny (number of points in x and y)

//Calculates using floating point x and y values (accurate down to 1E-6 ish)
__kernel void mandelbrot_float(__global int *out, __private float xmin, __private float dx, __private float ymin, __private float dy, __private int nx, __private int ny){
    //coords of thhis kernel instance
    int idx = get_global_id(1);
    int idy = get_global_id(0);
    
    //get the x0 and y0 values
    float x0 = xmin + idx*dx + (dx/2);
    float y0 = ymin + idy*dy + (dy/2);

    float x = 0.;
    float y = 0.;

    int n=0;

    // z_(n+1) = z_(n)^2 + (x0 + iy0)

    float z2 = x*x + y*y;

    while(z2 < 4 && n<256){
        //use this temporarily to hold the original x value
        z2 = x;
        
        //update x and y
        // (x+iy)^2 + x0 + iy0 = (x^2 - y^2 + x0) + (2*y*x + y0)i
        x = x*x - y*y + x0;
        y = 2*z2*y + y0;

        z2 = x*x + y*y;
        n+=1;
    }

    out[idx + nx*idy] = n;

}

//calculates using double precision x and y values, accurate down to 1E-14 ish
__kernel void mandelbrot_double(__global int *out, __private double xmin, __private double dx, __private double ymin, __private double dy, __private int nx, __private int ny){
    //coords of thhis kernel instance
    int idx = get_global_id(1);
    int idy = get_global_id(0);
    
    //get the x0 and y0 values
    double x0 = xmin + idx*dx + (dx/2);
    double y0 = ymin + idy*dy + (dy/2);

    double x = 0.;
    double y = 0.;

    int n=0;

    // z_(n+1) = z_(n)^2 + (x0 + iy0)

    double z2 = x*x + y*y;

    while(z2 < 4 && n<256){
        //use this temporarily to hold the original x value
        z2 = x;
        
        //update x and y
        // (x+iy)^2 + x0 + iy0 = (x^2 - y^2 + x0) + (2*y*x + y0)i
        x = x*x - y*y + x0;
        y = 2*z2*y + y0;

        z2 = x*x + y*y;
        n+=1;
    }

    out[idx + nx*idy] = n;

}




//calculates the real-valued mandelbrot set (returns a real not an int)
__kernel void real_mandelbrot_float(__global float *out, __private float xmin, __private float dx, __private float ymin, __private float dy, __private int nx, __private int ny){
    //coords of thhis kernel instance
    int idx = get_global_id(1);
    int idy = get_global_id(0);
    
    //get the x0 and y0 values
    float x0 = xmin + idx*dx + (dx/2);
    float y0 = ymin + idy*dy + (dy/2);

    float x = 0.;
    float y = 0.;

    const float ln2 = log((float)2.);

    int n=0;

    // z_(n+1) = z_(n)^2 + (x0 + iy0)

    float z2 = x*x + y*y;

    while(z2 < 100 && n<256){
        //use this temporarily to hold the original x value
        z2 = x;
        
        //update x and y
        // (x+iy)^2 + x0 + iy0 = (x^2 - y^2 + x0) + (2*y*x + y0)i
        x = x*x - y*y + x0;
        y = 2*z2*y + y0;

        z2 = x*x + y*y;
        n+=1;
    }


    if (n==256){
        out[idx + nx*idy] = 256.;
    } else {
        out[idx + nx*idy] = (float) n + 2. - log(log(z2))/ln2;
    }
    

}


//calculates the real-valued mandelbrot set (returns a real not an int) using double precision 
__kernel void real_mandelbrot_double(__global float *out, __private double xmin, __private double dx, __private double ymin, __private double dy, __private int nx, __private int ny){
    //coords of thhis kernel instance
    int idx = get_global_id(1);
    int idy = get_global_id(0);
    
    //get the x0 and y0 values
    double x0 = xmin + idx*dx + (dx/2);
    double y0 = ymin + idy*dy + (dy/2);

    double x = 0.;
    double y = 0.;

    const float ln2 = log((float)2.);

    int n=0;

    // z_(n+1) = z_(n)^2 + (x0 + iy0)

    double z2 = x*x + y*y;

    while(z2 < 100 && n<256){
        //use this temporarily to hold the original x value
        z2 = x;
        
        //update x and y
        // (x+iy)^2 + x0 + iy0 = (x^2 - y^2 + x0) + (2*y*x + y0)i
        x = x*x - y*y + x0;
        y = 2*z2*y + y0;

        z2 = x*x + y*y;
        n+=1;
    }


    if (n==256){
        out[idx + nx*idy] = 256.;
    } else {
        out[idx + nx*idy] = (float) n + 2. - log(log((float)z2))/ln2;
    }
    

}