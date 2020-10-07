import sys
import os
import time
import json

from PyQt5 import QtCore, QtWidgets

import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.image as MPLimage

from .mandelbrot import Mandelbrot
from . import checkcl
from . import pngs



#list of colourmaps to use (These are the names of matplotlib colourmaps)
cmaps =[
    "viridis",
    "plasma",
    "magma",
    "cubehelix",
    "jet",
    "gray"
]

#names of scaling types
scaling = [
    "Linear",
    "Logarithmic",
    "Sqrt",
    "Cbrt"
]


#loads the OpenCl and precision settings from .pyfractalrc
def load_settings():
    if os.path.exists(".pyfractalrc"):
        print("Loading settings from .pyfractalrc...")
        try:
            f=open(".pyfractalrc","r")
            contents=f.readlines()
            f.close()

            platformline = contents[0]
            deviceline = contents[1]
            precisionline = contents[2]
            
            #read in platform
            platforms = platformline.split()
            if platforms[0] != "platform":
                print("Platform line incorrect")
                return None
            platform = int(platforms[1])
            print("Platform = %d"%platform)
            
            #read in device
            devices = deviceline.split()
            if devices[0] != "device":
                print("Devices line wrong")
                return None
            device = int(devices[1])
            print("Device = %d"%device)
            
            #read in precision
            precisions = precisionline.split()
            if precisions[0] != "precision":
                print("Problem with the precision line")
                return None
            precision = int(precisions[1])
            print("Precision = %d"%precision)

            return platform, device, precision
        except Exception as e:
            print(e)
            return None
    else:
        print("No config file")
        return None
        

#saves the OpenCL and precision settings to .pyfractalrc
def save_settings(platform,device,precision):
    f = open('.pyfractalrc',"w")
    f.write("platform %d\n"%platform)
    f.write("device %d\n"%device)
    f.write("precision %d\n"%precision)
    f.close()

    

#allows the user to select the OpenCL platform and device graphically
class configurePopup(QtWidgets.QDialog):
    def __init__(self,parent):
        QtWidgets.QDialog.__init__(self)

        self.setWindowTitle("pyFractal setup")

        self.parent = parent

        self.platforms = checkcl.GetPlatformsAndDevices()
        
        #names of the platforms
        pnames = []
        for platform in self.platforms:
                pnames.append("Platform: "+platform["name"])
        #add a OpenCL not available platform
        pnames.append("None (do not use OpenCL)")
        
        #set the platform, device and precision to the parent window's current settings
        self.platform = parent.platform
        self.device = parent.device
        self.precision = parent.precision
        
        layout = QtWidgets.QVBoxLayout()

        l1 = QtWidgets.QLabel()
        l1.setText("Please select the OpenCl platform, device, and which precision you wish to use.\n")
        l2 = QtWidgets.QLabel()
        l2.setText("This dialogue only appears the first time you open pyFractal. If you wish to change the \n"
                   "settings at a later date, this option can be found in the Settings section of the main\n"
                   "menu.")

        layout.addWidget(l1)
        layout.addWidget(l2)

        self.platformChooser = QtWidgets.QComboBox()
        self.platformChooser.setPlaceholderText("--select platform--")
        self.platformChooser.currentIndexChanged.connect(self.selectPlatform)
        self.platformChooser.addItems(pnames)
        layout.addWidget(self.platformChooser)

        self.deviceChooser = QtWidgets.QComboBox()
        self.deviceChooser.currentIndexChanged.connect(self.selectDevice)
        self.deviceChooser.setEnabled(False)
        layout.addWidget(self.deviceChooser)

        self.precisionChooser = QtWidgets.QComboBox()
        self.precisionChooser.currentIndexChanged.connect(self.selectPrecision)
        self.precisionChooser.setEnabled(False)
        layout.addWidget(self.precisionChooser)


        self.okButton = QtWidgets.QPushButton("Ok")
        self.okButton.clicked.connect(self.confirm)
        self.okButton.setEnabled(False)
        layout.addWidget(self.okButton)

        self.setLayout(layout)
        
        #if configurePopup is called from the menu we preset the existing settings.
        if self.platform is not None:
            self.platformChooser.setCurrentIndex(self.platform)
            self.deviceChooser.setCurrentIndex(self.device)
            self.precisionChooser.setCurrentIndex(self.precision)
            
    #called when the user selects a platform from platformChooser
    def selectPlatform(self,n):
        
        #If the fallback is selected
        if n == len(self.platforms):
            self.platform = -1
            self.device = -1
            self.precision = 1

            self.deviceChooser.clear()
            self.deviceChooser.setPlaceholderText("--no device available--")
            self.deviceChooser.setEnabled(False)
           
            self.precisionChooser.clear()
            self.precisionChooser.setPlaceholderText("--not applicable--")
            self.precisionChooser.setEnabled(False)
            self.okButton.setEnabled(True)
        #otherwise
        else:
            self.platform = n
            
            #get list of devices
            devices = self.platforms[n]["devices"]
            devicelist = []
            for d in devices:
                devicelist.append("Device: "+d["name"])
            
            if len(devices) > 0:
                self.deviceChooser.clear()
                self.deviceChooser.setPlaceholderText("--select device--")
                self.deviceChooser.addItems(devicelist)
                self.deviceChooser.setEnabled(True)
            else:
                #if there are no devices in this platform, disable deviceChooser
                self.deviceChooser.setPlaceholderText("--no devices available--")
                self.deviceChooser.setEnabled(False)
            
            #clear and disable precisionChooser
            self.precisionChooser.clear()
            self.precisionChooser.setPlaceholderText("")
            self.precisionChooser.setEnabled(False)

            self.okButton.setEnabled(False)
            
        
    #called when the user selects a device from deviceChooser
    def selectDevice(self,n):

        self.device = n

        if n < 0: 
            return

        self.precisionChooser.clear()
        self.okButton.setEnabled(False)
        dp = self.platforms[self.platform]["devices"][n]["double_precision"]
        self.precisionChooser.setPlaceholderText("--select precision--")
        if dp:
            self.precisionChooser.addItems(["Precision: Single","Precision: Double", "Precision: Auto"])
        else:
            self.precisionChooser.addItems(["Precision: Single (device does not support double precision)"])
        self.precisionChooser.setEnabled(True)

    #called when the user selects a precision from precisionChooser   
    def selectPrecision(self,n):
        
        if self.platform == -1:
            self.precision = 1
        else:
            self.precision = n
        self.okButton.setEnabled(True)

    #called when the "ok" button is pressed. Updates the settings for the parent window, writes settings to file and closes the dialogue
    def confirm(self):
        print(self.platform, self.device, self.precision)
        self.parent.platform = self.platform
        self.parent.device = self.device
        self.parent.precision = self.precision

        save_settings(self.platform,self.device,self.precision)
        self.close()



#The matplotlib canvas where the fractal is displayed
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=10, height=10, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi,frameon=True)
        super(MplCanvas, self).__init__(fig)
        
        #request no margins for the subplot
        fig.subplots_adjust(left=0.0,right=1.0,bottom=0.0,top=1.0)
        self.axes = fig.add_subplot(111)


        
#Class for the main window
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("pyFractal")


        menubar = self.menuBar()
        menubar.setNativeMenuBar(True)

        fileMenu = menubar.addMenu(" File")
        #Loads the pyFractal relevant metadata from a PNG made by this program
        fileMenu.addAction("Load Image",self.loadPNG)
        settingsMenu = menubar.addMenu(" Settings")
        #allows the user to change the OpenCL settings
        settingsMenu.addAction("Change OpenCL Settings",self.changeOpenCLSettings)
        

        
        self.cmap = "viridis" #set initial cmap to viridis
        self.cmap_inverted = False #set initial cmap inversion to False
        self.scaling = scaling[0] #select the first scaling option (linear)
        self.real = False #set real-valued mandelbrot calculation to false (e.g. use discrete)
        

        #try to load the settings from the config file .pyfractalrc
        config = load_settings()
        if config is not None:
            self.platform, self.device, self.precision = config
        #if this was unsuccessful, open a dialogue for the user to choose the configuration
        else:
            self.platform = None
            self.device = None
            self.precision = None
            
            #Have a popup window to allow the user to select the platform, device and which precision to use
            popup=configurePopup(self)
            popup.exec_()
        
        #if all this failed (typically because the user closes the popup without choosing) close the window
        if self.platform is None:
            print("Closing")
            self.close()
            sys.exit()
        
        #object that calculates the mandelbrot set
        self.Mandelbrot = Mandelbrot(platform = self.platform, device=self.device)
        
        mainwidget = QtWidgets.QWidget()
        mainlayout = QtWidgets.QHBoxLayout()

        panelLayout = QtWidgets.QVBoxLayout()
        panelWidget = QtWidgets.QWidget()

        #the reset button
        Resetbutton = QtWidgets.QPushButton("Reset",self)
        Resetbutton.clicked.connect(self.reset)
        panelLayout.addWidget(Resetbutton)

        #cmap options
        cmapWidget = QtWidgets.QGroupBox("Colourmap Options")
        cmapLayout = QtWidgets.QVBoxLayout()

        self.invert_cmap_button = QtWidgets.QCheckBox("Invert colourmap")
        self.invert_cmap_button.stateChanged.connect(lambda: self.invert_cmap(self.invert_cmap_button))
        cmapLayout.addWidget(self.invert_cmap_button)

        self.cmaps=[]
        for cmap in cmaps:
            radio = QtWidgets.QRadioButton(cmap)
            radio.toggled.connect(self.toggle_cmap)
            cmapLayout.addWidget(radio)
            self.cmaps.append(radio)
        self.cmaps[0].setChecked(True)

        cmapWidget.setLayout(cmapLayout)
        panelLayout.addWidget(cmapWidget)


        #colour scaling options
        scalingWidget = QtWidgets.QGroupBox("Colour Scaling Options")
        scalingLayout = QtWidgets.QVBoxLayout()

        self.scales=[]
        for scale in scaling:
            radio = QtWidgets.QRadioButton(scale)
            radio.toggled.connect(self.toggle_scaling)
            scalingLayout.addWidget(radio)
            self.scales.append(radio)
        self.scales[0].setChecked(True)

        scalingWidget.setLayout(scalingLayout)
        panelLayout.addWidget(scalingWidget)
       


        #discrete or continuous settings
        realWidget = QtWidgets.QGroupBox("Rendering Options")
        realLayout = QtWidgets.QVBoxLayout()

        self.discreteToggle = QtWidgets.QRadioButton("Discrete")
        realLayout.addWidget(self.discreteToggle)
        self.discreteToggle.toggled.connect(lambda: self.toggle_real(self.discreteToggle))

        self.continuousToggle = QtWidgets.QRadioButton("Continuous")
        realLayout.addWidget(self.continuousToggle)
        self.continuousToggle.toggled.connect(lambda:self.toggle_real(self.continuousToggle))
        self.discreteToggle.setChecked(True)

        realWidget.setLayout(realLayout)
        panelLayout.addWidget(realWidget)


        #save button
        saveButton = QtWidgets.QPushButton("Save Image")
        saveButton.clicked.connect(self.save)
        panelLayout.addWidget(saveButton)

        
        #space filling widget
        panelLayout.addStretch()


        panelWidget.setLayout(panelLayout)


        #The canvas for matplotlib
        self.canvas = MplCanvas(self ,width=10, height=10, dpi=100)
        
        #bind mouse clicks and mouse movement events to some hander functions
        self.canvas.mpl_connect("button_press_event",self.onclick)
        self.canvas.mpl_connect("button_release_event",self.offclick)
        self.canvas.mpl_connect("motion_notify_event",self.mousemove)

        self.clicked = False
        self.clickstart=None

        
        #set the layout of the main window, requesting no margins or spacing
        mainlayout.setContentsMargins(0,0,0,0)
        mainlayout.setSpacing(0)
       
        mainlayout.addWidget(panelWidget)
        mainlayout.addWidget(self.canvas)
        
        mainwidget.setLayout(mainlayout)
        
        self.setCentralWidget(mainwidget)
        

        #this resets the plot and displays it
        self.reset()
        
        #shows the window
        self.show()


        
    #Changes the rendering from/to discrete (integer valued mandelbrot set) to/from continuous (real-valued)
    #This is called when the appropriate radio buttons are toggled
    def toggle_real(self,button):
        if button.text() == "Continuous":
            if button.isChecked():
                if not self.real:
                    self.real=True
                    print("Continuous")
                    self.plot()
                
        elif button.text() == "Discrete":
            if button.isChecked():
                if self.real:
                    self.real=False
                    print("Discrete")
                    self.plot()
        
    #Changes the colourmap being used
    # This is called when the approproate radioboxes are toggled
    def toggle_cmap(self):
        for r in self.cmaps:
            if r.isChecked():
                if self.cmap != r.text():
                    self.cmap = r.text()
                    self.plot(recalculate=False)
    
    #Inverts the colourmap
    #is called when the checkbos is checked/unchecked
    def invert_cmap(self,button):
        if button.isChecked():
            self.cmap_inverted=True
        else:
            self.cmap_inverted=False
        
        self.plot(recalculate=False)
    
    #Changes the colour scaling
    #This is called when the appropriate radio boxes are toggled
    def toggle_scaling(self):
        for r in self.scales:
            if r.isChecked():
                if r.text() != self.scaling:
                    self.scaling = r.text()
                    self.plot(recalculate=False)
    
    #Saves a high-res version of the current display to an image file
    #is called when the save button is pressed
    def save(self):
        file = pngs.GetNextFile()
        fname, filters = QtWidgets.QFileDialog.getSaveFileName(caption="File to save",directory=file)
        print(fname)

        if fname != "":
            self.writeImage(fname)

    #Displays the mandelbrot image. If recalculate is True, re-calculates the Mandelbrot set, else it uses the cached one
    #This is called by various functions
    def plot(self, recalculate=True):
        #calculate the image if requested
        if recalculate:
            #determine if we want to use double precision or  single precision
            if self.precision == 0:
                double = False
            elif self.precision == 1:
                double = True
            elif self.precision == 2:
                #switch to DP when pixel size is 1E-7 
                if (self.xmax-self.xmin)/1000 < 1E-7:
                    double = True
                else:
                    double = False
            else:
                raise ValueError("self.precision is not a valid value: %d"%self.precision)
            if self.real == False:
                self.img = self.Mandelbrot.calculate(self.xmin,self.xmax,self.ymin,self.ymax, double=double)
            else:
                self.img = self.Mandelbrot.calculate_real(self.xmin,self.xmax,self.ymin,self.ymax, double=double)
        
        #scale the image
        if self.scaling == "Linear":
            img=self.img
        elif self.scaling == "Logarithmic":
            # img = self.img +1
            img = np.log(self.img)
        elif self.scaling == "Sqrt":
            img = np.sqrt(self.img)
        elif self.scaling == "Cbrt":
            img = np.cbrt(self.img)
        
        #clear the canvas
        self.canvas.axes.cla()
        self.canvas.axes.set_axis_off()

        #display the image
        cmap = self.cmap
        if self.cmap_inverted:
            cmap += "_r"
        self.canvas.axes.imshow(img,
                                origin="lower",
                                extent = [self.xmin,self.xmax,self.ymin,self.ymax],
                                cmap = cmap,
                                interpolation=None)
        self.canvas.axes.set_xlim(self.xmin,self.xmax)
        self.canvas.axes.set_ylim(self.ymin,self.ymax)
        
        self.canvas.draw()
        self.repaint()

    
    #Generates a high resolution mandelbrot set from the current display and writes it to image file
    def writeImage(self, filename,nx=4000,ny=4000):
        #determine if we want to use double precision or  single precision
        if self.precision == 0:
            double = False
        elif self.precision == 1:
            double = True
        elif self.precision == 2:
            #switch to DP when pixel size is 1E-7 
            if (self.xmax-self.xmin)/1000 < 1E-7:
                double = True
            else:
                double = False
        else:
            raise ValueError("self.precision is not a valid value: %d"%self.precision)

        #generate the image
        if self.real == False:
            img = self.Mandelbrot.calculate(self.xmin,self.xmax,self.ymin,self.ymax, double=double,nx=nx,ny=ny)
        else:
            img = self.Mandelbrot.calculate_real(self.xmin,self.xmax,self.ymin,self.ymax, double=double,nx=nx,ny=ny)

        #scale the image
        if self.scaling == "Linear":
            pass
        elif self.scaling == "Logarithmic":
            img = np.log(img)
        elif self.scaling == "Sqrt":
            img = np.sqrt(img)
        elif self.scaling == "Cbrt":
            img = np.cbrt(img)
        
        cmap = self.cmap
        if self.cmap_inverted:
            cmap += "_r"
        
        #Add the display settings to the file so the image can be re-opened by pyFractal
        metadata={
            "xmin": self.xmin,
            "xmax": self.xmax,
            "ymin": self.ymin,
            "ymax": self.ymax,
            "scaling": self.scaling,
            "cmap": self.cmap,
            "cmap_inverted": self.cmap_inverted,
            "continuous": self.real
        }

        print("Writing '%s'..."%filename,end="",flush=True)
        MPLimage.imsave(filename,
                        img,
                        origin="lower",
                        cmap = cmap,
                        metadata = {"Software": "pyFractal",
                                    "pyFractal": json.dumps(metadata)})
        print(" Done!")
                       
    #resets the view
    def reset(self):

        self.xmin = -2.5
        self.xmax = 1.5
        self.ymin=-2
        self.ymax=2

        self.plot()
    
    #When a mouse button is clicked, registers this event in self.clicked and its time in self.clickstart 
    def onclick(self,event):
        self.clicked=True
        self.clickstart = time.time()
    
    #When a mouse button is released, determines how long the button was pressed for. If for a short time, zoom in
    # else we replot the image (its coordinates have likely changed due to self.mousemove)
    def offclick(self,event):
        self.clicked=False
        tstop = time.time()
        if (tstop-self.clickstart) < 0.2:
            self.zoom(event)
        else:
            self.plot()
    
    #if the mouse is currently clicked (e.g. mouse button is being held down), request the image on the screen be moved unless the click is brief 
    def mousemove(self,event):
        if self.clicked == False:
            self.oldx = event.xdata
            self.oldy = event.ydata
            return
        else:
            if time.time()-self.clickstart < 0.2:
                return

        x = event.xdata
        y = event.ydata
        dx = self.oldx-x
        dy = self.oldy-y
        self.xmin += dx
        self.xmax += dx
        self.ymin += dy
        self.ymax += dy

        self.canvas.axes.set_xlim(self.xmin,self.xmax)
        self.canvas.axes.set_ylim(self.ymin,self.ymax)
        
        self.canvas.draw()
        self.repaint()


    #zooms in on point clicked, so that this point remains under the mouse upon zoom completion
    def zoom(self,event):
        
        x, y = event.xdata, event.ydata
        print(x,y)

        xrange = self.xmax-self.xmin
        yrange = self.ymax-self.ymin

        lambdax = (x-self.xmin)/xrange
        lambday = (y-self.ymin)/yrange
        
        if event.button == 1:
            xrange /=2
            yrange /=2
            print("Zoom in")
        elif event.button ==3:
            xrange *=2
            yrange *=2
            print("Zoom out")
        
        self.xmin = x-lambdax*xrange
        self.xmax = self.xmin+xrange

        self.ymin = y-lambday*yrange
        self.ymax = self.ymin + yrange
        
        #old code where it centred on where the user clicks
        # self.xmin = x-xrange/2
        # self.xmax = x+xrange/2

        # self.ymin = y-yrange/2
        # self.ymax = y+yrange/2

        print(xrange,yrange)

        self.plot()


    def changeOpenCLSettings(self):
        #Have a popup window to allow the user to select the platform, device and which precision to use
        oldPlatform = self.platform
        oldDevice = self.device

        popup=configurePopup(self)
        popup.exec_()

        if self.platform != oldPlatform or self.device != oldDevice:
            self.Mandelbrot = Mandelbrot(platform=self.platform,device=self.device)
            self.plot()

    #opens a PNG file written by pyFractal and changes the view to match this image
    def loadPNG(self):
        #get the file to read
        fname, filters = QtWidgets.QFileDialog.getOpenFileName(caption="Open a pyFractal PNG",directory="./",filter = "PNG (*.png)")

        if fname == "":
            return
        
        #extract the metadata from the image
        metadata = pngs.GetImageMetadata(fname)
        
        #if the pyFractal header is in the data, read it in and set the window's settings to those found in the file
        if "pyFractal" in metadata.keys():
            settings = json.loads(metadata["pyFractal"])

            self.xmin = settings["xmin"]
            self.xmax = settings["xmax"]
            self.ymin = settings["ymin"]
            self.ymax = settings["ymax"]

            self.cmap = settings["cmap"]
            for cmap in self.cmaps:
                if cmap.text() == self.cmap:
                    cmap.setChecked(True)

            self.cmap_inverted = settings["cmap_inverted"]
            self.invert_cmap_button.setChecked(self.cmap_inverted)

            self.scaling = settings["scaling"]
            for scale in self.scales:
                if scale.text() == self.scaling:
                    scale.setChecked(True)

            self.real = settings["continuous"]
            if self.real:
                self.continuousToggle.setChecked(True)
            else:
                self.discreteToggle.setChecked(True)

            self.plot()

        else:
            QtWidgets.QMessageBox.warning(self,"","No metadata was found in %s"%fname)

            
def run():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    code = app.exec_()
    sys.exit(code)



