"""
ApplicationController class manages the lifecycle and shutdown behavior of the application.
Attributes:
    DEFAULT_SHUTDOWN_DELAY (int): Default delay for shutdown in milliseconds.
    DEFAULT_STARTUP_DELAY (int): Default delay for startup in milliseconds.
Methods:
    __init__(app):
        Initializes the ApplicationController with the given application instance.
    parse_arguments():
        Parses command line arguments with help documentation.
    configure_startup_shutdown(args):
        Configures application startup and shutdown based on command line arguments.
    _schedule_startup():
        Schedules application startup.
    _perform_startup():
        Performs actual application startup.
    _schedule_shutdown(delay_ms):
        Schedules application shutdown.
    _perform_shutdown():
        Performs actual application shutdown.

TestApp class is a testing application for the ApplicationController.
Methods:
    OnInit():
        Initializes the frame and updates built-in variables.
    RunTest(frame=None):
        Runs the test by showing the frame and configuring the controller for automatic launch and stop.
    OnClose(event):
        Closes the application and exits the main loop.
Use:
if __name__ == '__main__':

	from ApplicationController import TestApp

	app = TestApp(0)
	frame = MyFrameToTest(None, "Test")
	app.RunTest(frame)
"""
import wx
import argparse
import sys, os

# Add parent dir to sys.path in order to avoid import from test files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'devsimpy')))

from config import UpdateBuiltins

# Update the builtins variables
UpdateBuiltins()

class ApplicationController:
    """Controls application lifecycle and shutdown behavior"""
    
    DEFAULT_SHUTDOWN_DELAY = 2000  # milliseconds
    DEFAULT_STARTUP_DELAY = 100    # milliseconds
    
    def __init__(self, app):
        self.app = app
        self._shutdown_timer = None
        self._startup_timer = None
        
    def parse_arguments(self):
        """Parse command line arguments with help documentation"""
        parser = argparse.ArgumentParser(
            description='DEVSimPy XML Module - Diagram Constants Manager',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python XMLModule.py                      # Normal startup
  python XMLModule.py --autostart            # Start automatically without clausing
  python XMLModule.py --autoclose            # Start automatically and close after 2 seconds (defautl sleep time)
  python XMLModule.py --autoclose 5          # Start autoatically and close after 5 seconds
  python XMLModule.py --autostart --autoclose 3 # Start automatically and close after 3 seconds
  python XMLModule.py --autoclose --nogui # Start automatically the test with nogui activated
  
Additional Information:
  - The autostart option shows the window immediately
  - The autoclose option takes seconds as parameter
  - The nogui option set the show option of the frame at False
  - Both options can be combined
""")
        
        parser.add_argument('--autostart', action='store_true',
                          help='Start the application window automatically')
        
        parser.add_argument('--autoclose', 
                      nargs='?',  # Makes the argument value optional
                      type=int,
                      const=2,    # Default value when --autoclose is used without value
                      default=None,  # Default value when --autoclose is not used
                      metavar='SECONDS',
                      help='Automatically close the application after specified seconds (default: 2)')
    
        parser.add_argument('--nogui', action='store_true',
                          help='Run the application without showing the GUI')
    
        parser.add_argument('--version', action='version', 
                          version='%(prog)s 1.0',
                          help='Show program version')
        
        return parser.parse_args()

    def configure_startup_shutdown(self, args):
        """Configures application startup and shutdown based on command line arguments"""
        try:
            # If args is a list (sys.argv), parse it first
            if isinstance(args, list):
                args = self.parse_arguments()
                
            if args.autostart:
                self._schedule_startup()

            if args.autoclose is not None:
                delay = args.autoclose * 1000  # Convert to milliseconds
                self._schedule_shutdown(delay)
        except Exception as e:
            print(f"Error configuring startup/shutdown: {str(e)}")
            raise
    
    def _schedule_startup(self):
        """Schedules application startup"""
        self._startup_timer = wx.CallLater(
            self.DEFAULT_STARTUP_DELAY,
            self._perform_startup
        )
    
    def _perform_startup(self):
        """Performs actual application startup"""
        if hasattr(self.app, 'frame'):
            self.app.frame.Show()
            
    def _schedule_shutdown(self, delay_ms):
        """Schedules application shutdown"""
        self._shutdown_timer = wx.CallLater(
            delay_ms,
            self._perform_shutdown
        )
    
    def _perform_shutdown(self):
        """Performs actual application shutdown"""
        if hasattr(self.app, 'OnClose'):
            self.app.OnClose(None)
        elif hasattr(self.app, 'frame'):
            self.app.frame.Close(True)
        elif hasattr(self.app, 'ExitMainLoop'):
            self.app.ExitMainLoop()
        else:
            self.app.Exit()

class TestApp(wx.App):
    """ Testing application
    """

    def OnInit(self):
        """ Init the frame.
        """

        return True
        
    def RunTest(self, frame=None, show=True):
        """ Run the test.
        """

        # if frame is not provided, get the first top level window
        if not frame:
            frame = wx.GetTopLevelWindows()[0]

        # Remove the show modal mode in order to close automatically
        # style = frame.GetWindowStyleFlag()
        # if style & wx.DIALOG_MODAL:
        #     frame.SetWindowStyleFlag(style & ~wx.DIALOG_MODAL)

        controller = ApplicationController(self)

        args = controller.parse_arguments()
        show = not args.nogui

        # Show the frame
        frame.Show(show)

        # Activate the controller to launc and stop the frame automatically
        controller.configure_startup_shutdown(args)
        
        # Start the main loop
        self.MainLoop()

    def OnClose(self, event):
        """ Close the application.
        """
        self.ExitMainLoop()  # Quitte proprement la boucle
