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


####Getting user info 
req = urllib2.Request(DASHBOARD,None,headers)
resp = urllib2.urlopen(req)
#print resp.info()
dash = resp.read()
#print dash
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
#print COURSEWARE

## Getting Current Lectures
req = urllib2.Request(COURSEWARE,None,headers)
resp = urllib2.urlopen(req)
courseware = resp.read()
soup = BeautifulSoup(courseware)
data = soup.section.section.div.div.nav
WEEKS = data.find_all('div')
weeks = [(w.h3.a.string,["https://www.edx.org"+a['href'] for a in w.ul.find_all('a')]) for w in WEEKS]
#print WEEKS[2].h3.a.string
#print WEEKS[2].ul.find_all('a')
#print weeks[0]
numOfWeeks = len(weeks)
w = 0
print selected_course[0] ," has ", numOfWeeks, " Weeks so far"
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

#exit(2)


########
"""
links = []
links.append("https://www.edx.org/courses/BerkeleyX/CS188.1x/2012_Fall/courseware/Week_3/Lecture_4_CSPs")
links.append("https://www.edx.org/courses/BerkeleyX/CS188.1x/2012_Fall/courseware/Week_3/Lecture_4_CSPs_continued/")
links.append("https://www.edx.org/courses/BerkeleyX/CS188.1x/2012_Fall/courseware/Week_3/Lecture_5_CSPs_II/")
links.append("https://www.edx.org/courses/BerkeleyX/CS188.1x/2012_Fall/courseware/Week_3/Lecture_5_CSPs_II_continued/")
"""
video_id = []
for link in links :
    req = urllib2.Request(link,None,headers)

    resp = urllib2.urlopen(req)

    page =  resp.read()
    splitter = re.compile('data-streams=(?:&#34;|\")1.0:')
    id_container = splitter.split(page)[1:]
    #print link
    video_id += [link[:11] for link in id_container]
    #print video_id


video_link = ["http://youtube.com/watch?v="+ v_id for v_id in video_id]
#print video_link
### Downloading 

os.system('youtube-dl -F '+video_link[-1])
format = int(raw_input("Choose Format code : "))
c = 0
for v in video_link:
    c += 1
    os.system('youtube-dl -o "Downloaded/'+str(c)+'- %(stitle)s.%(ext)s" -f '+str(format)+" "  + v)

