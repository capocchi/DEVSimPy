"""Test script for CheckerGUI functionality.

Usage:
    python test_checkergui.py --autoclose
    python test_checkergui.py --autoclose 10  # Sleep time before closing frame is 10s
"""

from ApplicationController import TestApp

# import after ApplicationController that init sys.path ot avoid this import
from CheckerGUI import CheckerGUI 

# Some input data to test case
musicdata = {
    1 : ("Bad English", "The Price Of Love", "Rock"),
    2 : ("DNA featuring Suzanne Vega", "Tom's Diner", "Rock"),
    3 : ("George Michael", "Praying For Time", "Rock"),
    4 : ("Gloria Estefan", "Here We Are", "Rock"),
    5 : ("Linda Ronstadt", "Don't Know Much", "Rock"),
    6 : ("Michael Bolton", "How Am I Supposed To Live Without You", "Blues"),
    7 : ("Paul Young", "Oh Girl", "Rock"),
    8 : ("Paula Abdul", "Opposites Attract", "Rock"),
    9 : ("Richard Marx", "Should've Known Better", "Rock"),
    10: ("Rod Stewart", "Forever Young", "Rock"),
    11: ("Roxette", "Dangerous", "Rock"),
    12: ("Sheena Easton", "The Lover In Me", "Rock"),
    13: ("Sinead O'Connor", "Nothing Compares 2 U", "Rock"),
    14: ("Stevie B.", "Because I Love You", "Rock"),
    15: ("Taylor Dayne", "Love Will Lead You Back", "Rock"),
    16: ("The Bangles", "Eternal Flame", "Rock"),
    17: ("Wilson Phillips", "Release Me", "Rock"),
    18: ("Billy Joel", "Blonde Over Blue", "Rock"),
    19: ("Billy Joel", "Famous Last Words", "Rock"),
    20: ("Billy Joel", "Lullabye (Goodnight, My Angel)", "Rock"),
    21: ("Billy Joel", "The River Of Dreams", "Rock"),
    22: ("Billy Joel", "Two Thousand Years", "Rock"),
    23: ("Janet Jackson", "Alright", "Rock"),
    24: ("Janet Jackson", "Black Cat", "Rock"),
    25: ("Janet Jackson", "Come Back To Me", "Rock"),
    26: ("Janet Jackson", "Escapade", "Rock"),
    27: ("Janet Jackson", "Love Will Never Do (Without You)", "Rock"),
    28: ("Janet Jackson", "Miss You Much", "Rock"),
    29: ("Janet Jackson", "Rhythm Nation", "Rock"),
    30: ("Janet Jackson", "State Of The World", "Rock"),
    31: ("Janet Jackson", "The Knowledge", "Rock"),
    32: ("Spyro Gyra", "End of Romanticism", "Jazz"),
    33: ("Spyro Gyra", "Heliopolis", "Jazz"),
    34: ("Spyro Gyra", "Jubilee", "Jazz"),
    35: ("Spyro Gyra", "Little Linda", "Jazz"),
    36: ("Spyro Gyra", "Morning Dance", "Jazz"),
    37: ("Spyro Gyra", "Song for Lorraine", "Jazz"),
    38: ("Yes", "Owner Of A Lonely Heart", "Rock"),
    39: ("Yes", "Rhythm Of Love", "Rock"),
    40: ("Cusco", "Dream Catcher", "New Age"),
    41: ("Cusco", "Geronimos Laughter", "New Age"),
    42: ("Cusco", "Ghost Dance", "New Age"),
    43: ("Blue Man Group", "Drumbone", "New Age"),
    44: ("Blue Man Group", "Endless Column", "New Age"),
    45: ("Blue Man Group", "Klein Mandelbrot", "New Age"),
    46: ("Kenny G", "Silhouette", "Jazz"),
    47: ("Sade", "Smooth Operator", "Jazz"),
    48: ("David Arkenstone", "Papillon (On The Wings Of The Butterfly)", "New Age"),
    49: ("David Arkenstone", "Stepping Stars", "New Age"),
    50: ("David Arkenstone", "Carnation Lily Lily Rose", "New Age"),
    51: ("David Lanz", "Behind The Waterfall", "New Age"),
    52: ("David Lanz", "Cristofori's Dream", "New Age"),
    53: ("David Lanz", "Heartsounds", "New Age"),
    54: ("David Lanz", "Leaves on the Seine", "New Age"),
    }
    
# Run the test
app = TestApp(0)
frame = CheckerGUI(None, "Test", musicdata)
app.RunTest(frame)