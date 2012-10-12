#!/usr/bin/env python
import os, pprint, sys, math, urllib,urllib2, cookielib, shutil, json,re
from bs4 import BeautifulSoup
from datetime import timedelta, datetime

EDX_HOMEPAGE = 'https://www.edx.org'
LOGIN_API = 'https://www.edx.org/login'
DASHBOARD = 'https://www.edx.org/dashboard'
save_path = 'temp'
user_email = sys.argv[1]
user_pswd = sys.argv[2]

#Get Token
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)
response = opener.open(EDX_HOMEPAGE)
set_cookie = {}
for cookie in cj:
    set_cookie[cookie.name] = cookie.value


#Prepare Headers
headers = {'User-Agent': 'edX-downloader/0.01',
           'Accept': 'application/json, text/javascript, */*; q=0.01',
           'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
           'Referer': EDX_HOMEPAGE,
           'X-Requested-With': 'XMLHttpRequest',
           'X-CSRFToken': set_cookie.get('csrftoken', '') }

#Login
post_data = urllib.urlencode({
            'email' : user_email,
            'password' : user_pswd,
            'remember' : False
            }).encode('utf-8')
request = urllib2.Request(LOGIN_API, post_data,headers)
response = urllib2.urlopen(request)
resp = json.loads(response.read().decode(encoding = 'utf-8'))
if not resp.get('success', False):
    print 'Wrong Email or Password.'
    exit(2)

#Get user info/courses 
req = urllib2.Request(DASHBOARD,None,headers)
resp = urllib2.urlopen(req)
dash = resp.read()
soup = BeautifulSoup(dash)
data = soup.find_all('ul')[1]
USERNAME =  data.find_all('span')[1].string
USEREMAIL = data.find_all('span')[3].string
COURSES = soup.find_all('article')
courses = []
for COURSE in COURSES :
    c_name = COURSE.h3.string
    c_link = "https://www.edx.org"+COURSE.a['href']
    if c_link.endswith("info") or c_link.endswith("info/") :
        state = "Started"
    else :
        state = "Not yet"
    courses.append((c_name,c_link,state))
numOfCourses = len(courses)

#Welcome and Choose Course
print "Welcome " , USERNAME 
print "You can access ",numOfCourses," Courses on edX"

c = 0
for course in courses :
    c += 1
    print c, "- ",course[0]," -> ",course[2]
    
c_number = int(raw_input("Enter Course Number : "))
while c_number > numOfCourses or courses[c_number-1][2] != "Started" :
    print "Enter a valid Number for a Started Course ! between 1 and ",numOfCourses 
    c_number = int(raw_input("Enter Course Number : "))
selected_course = courses[c_number-1]
COURSEWARE = selected_course[1].replace("info","courseware")

## Getting Available Weeks
req = urllib2.Request(COURSEWARE,None,headers)
resp = urllib2.urlopen(req)
courseware = resp.read()
soup = BeautifulSoup(courseware)
data = soup.section.section.div.div.nav
WEEKS = data.find_all('div')
weeks = [(w.h3.a.string,["https://www.edx.org"+a['href'] for a in w.ul.find_all('a')]) for w in WEEKS]
numOfWeeks = len(weeks)

#Choose Week or choose all
print selected_course[0] ," has ", numOfWeeks, " Weeks so far"
w = 0
for week in weeks :
    w+=1
    print w, "- Dowload ", week[0], " videos"
print numOfWeeks+1, "- Download them all"

w_number = int(raw_input("Enter Your Choice : "))
while w_number > numOfWeeks + 1  :
    print "Enter a valid Number between 1 and ",numOfWeeks+1 
    w_number = int(raw_input("Enter Your Choice : "))

if w_number == numOfWeeks+1 :
    links = [link for week in weeks for link in week[1]]
else :
    links = weeks[w_number-1][1]

video_id = []
for link in links :
    req = urllib2.Request(link,None,headers)
    resp = urllib2.urlopen(req)
    page =  resp.read()
    splitter = re.compile('data-streams=(?:&#34;|\")1.0:')
    id_container = splitter.split(page)[1:]
    video_id += [link[:11] for link in id_container]
    
video_link = ["http://youtube.com/watch?v="+ v_id for v_id in video_id]

#Get Available Formats
os.system('youtube-dl -F '+video_link[-1])
format = int(raw_input("Choose Format code : "))

#Download Videos
c = 0
for v in video_link:
    c += 1
    os.system('youtube-dl -o "Downloaded/'+str(c)+'- %(stitle)s.%(ext)s" -f '+str(format)+" "  + v)

#Say Good Bye :)
print "Videos have been downloaded, thanks for using our tool, Good Bye :)"
