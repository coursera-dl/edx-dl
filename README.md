

# DESCRIPTION
Simple tool to download video lectures from edx.com . 
It requires the Python interpreter (v 2.x or 3.x), youtube-dl, BeautifulSoup4 and it's platform independent. 
It should work fine in your Unix box, in Windows or in Mac OS X . 

# DEPENDENCIES

### youtube-dl
We use youtube-dl to download video lectures from youtube "We don't wanna reinvent the wheel :)".
Make sure you have youtube-dl installed in your system .
You can find youtube-dl here : https://github.com/rg3/youtube-dl

### BeautifulSoup
Scrapping the web can be very silly task, but BeautifulSoup makes it so easy :),
it isn't included in the python standard library .
Make sure you have BeautifulSoup installed .
You can install it with pip install beautifulsoup4 or easy_install beautifulsoup4.
For more info : http://www.crummy.com/software/BeautifulSoup/#Download

# Files

### edx-dl.py
Python2 implementation for edx-downloader


### edx-downloader.py
The original file written by shk3 in/for python3
then updated by emadshaaban92 using 2to3 . 


# USAGE

### For Python2.x 
use edx-dl.py , simply excute it with 2 agrument "email,password"
###### Example 
    python edx-dl.py user@user.com 123456
    
Your downloaded videos will be placed in a new Directory called "Downloaded"

The script is very interactive , if you have a issue please tell us .


### For Python3.x 
Instructions are the same as Python2.x except you should use edx-downloader.py instead of edx-dl.py
###### Example 
    python3 edx-downloader.py user@user.com 123456

