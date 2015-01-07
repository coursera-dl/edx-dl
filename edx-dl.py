#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python 2/3 compatibility imports
from __future__ import print_function
from __future__ import unicode_literals

try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    from urllib.request import urlopen
    from urllib.request import build_opener
    from urllib.request import install_opener
    from urllib.request import HTTPCookieProcessor
    from urllib.request import Request
    from urllib.request import URLError
    import configparser
except ImportError:
    from urllib2 import urlopen
    from urllib2 import build_opener
    from urllib2 import install_opener
    from urllib2 import HTTPCookieProcessor
    from urllib2 import Request
    from urllib2 import URLError
    import ConfigParser

# we alias the raw_input function for python 3 compatibility
try:
    input = raw_input
except:
    pass

try:
    ConfigParser = configparser
except:
    pass

import argparse
import getpass
import json
import os
import os.path
import re
import sys
import imp

from subprocess import Popen, PIPE
from datetime import timedelta, datetime

from bs4 import BeautifulSoup

OPENEDX_SITES = {
    'edx': {
        'url': 'https://courses.edx.org'
    }, 
    'stanford': {
        'url': 'https://class.stanford.edu'
    },
    'usyd-sit': {
        'url': 'http://online.it.usyd.edu.au'
    },
}

COURSEWARE_NAV={ 'en':'Course Navigation','zh-cn':'课程导航','fr':'Menu du cours','es-419':'Navegación del curso','hi':'पाठ्यक्रम नेविगेशन','pt-br':'Navegação do curso' }
BASE_URL = OPENEDX_SITES['edx']['url']
EDX_HOMEPAGE = BASE_URL + '/login_ajax'
LOGIN_API = BASE_URL + '/login_ajax'
DASHBOARD = BASE_URL + '/dashboard'

YOUTUBE_VIDEO_ID_LENGTH = 11

## If nothing else is chosen, we chose the default user agent:

DEFAULT_USER_AGENTS = {"chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.63 Safari/537.31",
                       "firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0",
                       "edx": 'edX-downloader/0.01'}

USER_AGENT = DEFAULT_USER_AGENTS["edx"]

# To replace the print function, the following function must be placed before any other call for print
def print(*objects, **kwargs):
    """
    Overload the print function to adapt for the encoding bug in Windows Console.
    It will try to convert text to the console encoding before print to prevent crashes.
    """
    try:
        stream = kwargs.get('file', None)
        if stream is None:
            stream = sys.stdout
        enc = stream.encoding
        if enc is None:
            enc = sys.getdefaultencoding()
    except AttributeError:
        return __builtins__.print(*objects, **kwargs)
    texts = []
    for object in objects:
        try:
            original_text = str(object)
        except UnicodeEncodeError:
            original_text = unicode(object)
        texts.append(original_text.encode(enc, errors='replace').decode(enc))
    return __builtins__.print(*texts, **kwargs)

def change_openedx_site(site_name):
    global BASE_URL
    global EDX_HOMEPAGE
    global LOGIN_API
    global DASHBOARD

    if site_name not in OPENEDX_SITES.keys():
        print("OpenEdX platform should be one of: %s" % ', '.join(OPENEDX_SITES.keys()))
        sys.exit(2)

    BASE_URL = OPENEDX_SITES[site_name]['url']
    EDX_HOMEPAGE = BASE_URL + '/login_ajax'
    LOGIN_API = BASE_URL + '/login_ajax'
    DASHBOARD = BASE_URL + '/dashboard'

def get_initial_token():
    """
    Create initial connection to get authentication token for future requests.

    Returns a string to be used in subsequent connections with the
    X-CSRFToken header or the empty string if we didn't find any token in
    the cookies.
    """
    cj = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    install_opener(opener)
    opener.open(EDX_HOMEPAGE)

    for cookie in cj:
        if cookie.name == 'csrftoken':
            return cookie.value

    return ''


def get_page_contents(url, headers):
    """
    Get the contents of the page at the URL given by url. While making the
    request, we use the headers given in the dictionary in headers.
    """
    result = urlopen(Request(url, None, headers))
    try:
        charset = result.headers.get_content_charset(failobj="utf-8")  # for python3
    except:
        charset = result.info().getparam('charset') or 'utf-8'
    return result.read().decode(charset)


def download_cdn_videos(filenames,sub_urls,video_urls, target_dir):
    """ This function downloads the videos from video_urls """
    """ using a simple file downloader """
    for i, v in enumerate(video_urls):
        filename_prefix = str(i+1).zfill(2) + '-'
        #original_filename = v.rsplit('/', 1)[1]
        video_filename = filename_prefix + filenames[i] + '.mp4'
        sub_filename = filename_prefix + filenames[i] + '.srt'
        video_path = os.path.join(target_dir, video_filename)
        sub_path = os.path.join(target_dir, sub_filename)
        #print('[debug] GET %s' % v)
        print('[download] Destination: %s' % video_path)
        if len(v) != YOUTUBE_VIDEO_ID_LENGTH:
           req = Request(v)                                                                      
           try:
              video = urlopen(v)
              fileSize = int(video.headers['content-length'])
              finish = False
              existSize = 0
              if os.path.exists(video_path):
                  output = open(video_path,"ab")
                  existSize = os.path.getsize(video_path)
                  #If the file exists, then only download the remainder
                  if existSize < fileSize:
                      #print("[debug] bytes range is: %s-%s" % (existSize,fileSize))
                      req.headers["Range"]= "bytes=%s-%s" % (existSize,fileSize)
                      video = urlopen(req)
                  else:
                      finish = True
              else:
                  output = open(video_path,"wb")
              if finish == False:
                  file_size_dl = existSize
                  block_sz = 262144
                  while True:
                      buffer = video.read(block_sz)
                      if not buffer:
                          break
                                                                                                   
                      file_size_dl += len(buffer)
                      output.write(buffer)
                      status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / fileSize)
                      status = status + chr(8)*(len(status)+1)
                      sys.stdout.write(status)
                      sys.stdout.flush()
                  
              output.close()

           except URLError as e:
                print("[warning]error: %r when downloading %s" % (e.reason,v) )

        else:
           download_youtube_video(v,video_path)
    
        if sub_urls[i] != "":
            #print('[debug] GET %s' % BASE_URL+sub_urls[i])
            if not os.path.exists(sub_path):
                subs_string = edx_get_subtitle(sub_urls[i], headers)
                if subs_string:
                    print('[info] Writing edX subtitles: %s' % sub_path)
                    open(os.path.join(os.getcwd(), sub_path),
                         'wb+').write(subs_string.encode('utf-8'))

            #srtfile = urlopen(BASE_URL+sub_urls[i])
            #output = open(srt_path,'wb')
            #output.write(srtfile.read())
            #output.close()



def directory_name(initial_name):
    import re
    #allowed_chars = string.digits+string.ascii_letters+" _.&-"
    result_name = re.sub('[\\/:"*?<>|]+','',html_decode(initial_name).replace(': ','-')).strip()
    #for ch in initial_name:
        #if allowed_chars.find(ch) != -1:
            #result_name += ch
    return result_name if result_name != "" else "course_folder"


def edx_json2srt(o):
    i = 1
    output = ''
    for (s, e, t) in zip(o['start'], o['end'], o['text']):
        if t == "":
            continue
        output += str(i) + '\n'
        s = datetime(1, 1, 1) + timedelta(seconds=s/1000.)
        e = datetime(1, 1, 1) + timedelta(seconds=e/1000.)
        output += "%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d" % \
            (s.hour, s.minute, s.second, s.microsecond/1000,
             e.hour, e.minute, e.second, e.microsecond/1000) + '\n'
        output += t + "\n\n"
        i += 1
    return output


def edx_get_subtitle(url, headers):
    """ returns a string with the subtitles content from the url """
    """ or None if no subtitles are available """
    try:
        jsonString = get_page_contents(url, headers)
        jsonObject = json.loads(jsonString)
        return edx_json2srt(jsonObject)
    except URLError as e:
        print('[warning] edX subtitles (error:%s)' % e.reason)
        return None
    except ValueError as e:
        print('[warning] edX subtitles (error:%s)' % e.message)
        return None


def parse_args():
    """
    Parse the arguments/options passed to the program on the command line.
    """
    parser = argparse.ArgumentParser(prog='edx-dl',
                                     description='Get videos from the OpenEdX platform',
                                     epilog='For further use information,'
                                     'see the file README.md',)
    # positional
    parser.add_argument('course_id',
                        nargs='*',
                        action='store',
                        default=None,
                        help='target course id '
                        '(e.g., https://courses.edx.org/courses/BerkeleyX/CS191x/2013_Spring/info/)'
                        )

    # optional
    parser.add_argument('-u',
                        '--username',
                        action='store',
                        help='your edX username (email)')
    parser.add_argument('-p',
                        '--password',
                        action='store',
                        help='your edX password')
    parser.add_argument('-f',
                        '--format',
                        dest='format',
                        action='store',
                        default=None,
                        help='format of videos to download')
    parser.add_argument('-s',
                        '--with-subtitles',
                        dest='subtitles',
                        action='store_true',
                        default=False,
                        help='download subtitles with the videos')
    parser.add_argument('-o',
                        '--output-dir',
                        action='store',
                        dest='output_dir',
                        help='store the files to the specified directory',
                        default='Downloaded')
    parser.add_argument('-x',
                        '--platform',
                        action='store',
                        dest='platform',
                        help='OpenEdX platform, currently either "edx", "stanford" or "usyd-sit"',
                        default='edx')
    parser.add_argument('-nc',
                        '--no-cdn',
                        action='store_false',
                        dest='use_cdn',
                        help='use youtube-dl instead of cdn to get the videos',
                        default=True)

    args = parser.parse_args()
    return args

def html_decode(s):
    """
    Returns the ASCII decoded version of the given HTML string. This does
    NOT remove normal HTML tags like <p>.
    """
    htmlCodes = [["'", '&#39;'],['"', '&quot;'],['>', '&gt;'],['<', '&lt;'],['&', '&amp;'],['"','&#34;']]
    for code in htmlCodes:
        s = s.replace(code[1], code[0])
    return s

def main():
    try:
        imp.reload(sys)  
        sys.setdefaultencoding('utf8')
    except:
        pass
    PYTHONIOENCODING="utf-8"
    config = ConfigParser.ConfigParser()
    global args 
    args = parse_args()
    for loc in os.curdir, os.path.expanduser("~")+"/.edx-dl" :
        try: 
            with open(os.path.join(loc,"config")) as source:
                config.readfp( source )
                args.platform = config.get('basic','platform')
                args.username = config.get('basic','username')
                args.password = config.get('basic','password')
        except IOError:
            pass
    # if no args means we are calling the interactive version
    is_interactive = len(sys.argv) == 1 and (args.username == "" or args.username==None)
    if is_interactive:
        args.platform = input('Platform: ')
        args.username = input('Username: ')
        args.password = getpass.getpass()  

    change_openedx_site(args.platform)

    if not args.username or not args.password:
        print("You must supply username AND password to log-in")
        sys.exit(2)

    # Prepare Headers
    global headers 
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        'Referer': EDX_HOMEPAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': get_initial_token(),
    }

    # Login
    post_data = urlencode({'email': args.username, 'password': args.password,
                           'remember': False}).encode('utf-8')
    request = Request(LOGIN_API, post_data, headers)
    response = urlopen(request)
    resp = json.loads(response.read().decode('utf-8'))
    if not resp.get('success', False):
        print(resp.get('value', "Wrong Email or Password."))
        exit(2)

    # Get user info/courses
    dash = get_page_contents(DASHBOARD, headers)
    soup = BeautifulSoup(dash)
    data = soup.find_all('ul')[1]
    USERNAME = data.find_all('span')[1].string
    COURSES = soup.find_all('article', 'course')
    courses = []
    for COURSE in COURSES:
        c_name = COURSE.h3.text.strip()
        c_link = BASE_URL + COURSE.a['href']
        if c_link.endswith('info') or c_link.endswith('info/'):
            state = 'Started'
        else:
            state = 'Not yet'
        courses.append((c_name, c_link, state))
    numOfCourses = len(courses)

    # Welcome and Choose Course

    print('Welcome %s' % USERNAME)
    print('You can access %d courses' % numOfCourses)

    c = 0
    for course in courses:
        c += 1
        print('%d - %s -> %s' % (c, course[0], course[2]))

    c_number = int(input('Enter Course Number: '))
    while c_number > numOfCourses or courses[c_number - 1][2] != 'Started':
        print('Enter a valid Number for a Started Course ! between 1 and ',
              numOfCourses)
        c_number = int(input('Enter Course Number: '))
    selected_course = courses[c_number - 1]
    COURSEWARE = selected_course[1].replace('info', 'courseware')

    ## Getting Available Weeks
    courseware = get_page_contents(COURSEWARE, headers)
    soup = BeautifulSoup(courseware)
    COURSEWARE_SEL= ('nav',{'aria-label':COURSEWARE_NAV[soup.html.get('lang')]})
    data = soup.find(*COURSEWARE_SEL)
    WEEKS = data.find_all('div')
    weeks = [(w.h3.a.string, [BASE_URL + a['href'] for a in
             w.ul.find_all('a')]) for w in WEEKS]
    
    numOfWeeks = len(weeks)
    #Getting names of sections of each weak 
    fileweeks = [(w.h3.a.string, [a.getText().replace('\n', '').replace('  ','')  for a in
             w.ul.select('li > a')]) for w in WEEKS]

    # Choose Week or choose all
    print('%s has %d weeks so far' % (selected_course[0], numOfWeeks))
    w = 0
    for week in weeks:
        w += 1
        print('%d - Download %s videos' % (w, week[0].strip()))
    print('%d - Download them all' % (numOfWeeks + 1))
    

    w_number = int(input('Enter Your Choice: '))
    while w_number > numOfWeeks + 1:
        print('Enter a valid Number between 1 and %d' % (numOfWeeks + 1))
        w_number = int(input('Enter Your Choice: '))

    if w_number == numOfWeeks + 1:
        startw = 0
        endw = numOfWeeks-1
    else:
        startw = w_number - 1
        endw = startw

    target_dir = os.path.join(args.output_dir,
                              directory_name(selected_course[0]))
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if is_interactive:
        args.use_cdn = input('Use youtube-dl to download videos (y/n)? ').lower() == 'n'

    if is_interactive:
        args.subtitles = input('Download subtitles (y/n)? ').lower() == 'y'
    
    re_videomules  = re.compile(r'xmodule_VideoModule.*?h2(?:>|&gt;)(.*?)(?:&lt;|<)\/h2.*?data-streams=(?:&#34;|").*?(?:1.0[0]*:|.*?)(.*?)(?:&#34;|").*?data-sources=&#39;\[(.*?)\]&#39;.*?data-transcript-translation-url=(?:&#34;|")(.*?)(?:&#34;|").*?wrapper-downloads(.*?)(?:&lt;|<)\/ul',re.DOTALL)
    # notice that not all the webpages have this field (opposite of data-streams)
    re_video_urls = re.compile(r'href=(?:&#34;|")([^"&]*mp4)')
    
     
    extra_youtube = re.compile(r'//w{0,3}\.youtube.com/embed/([^ \?&]*)[\?& ]')
    wfilenames = []
    wvideo_urls = []
    wsub_urls = []
    wfolders = []
    NoOfVideo = 0
    for iw in range(startw,endw+1):
        video_urls = []
        sub_urls = []
        i = 0
        filenames = []
        for link in weeks[iw][1]:                                                                   
            print("Processing '%s'..." % link)
            page = get_page_contents(link, headers)
    
            #find video section by xmodule_VideoModule                                                                      
            video_modules= re_videomules.findall(page)                                                                      
            for video_m in video_modules:  
                
                tmpname=re.sub('[\\/:"*?<>|]+','',html_decode(video_m[0]).replace(': ','-')).strip() #remove illegal characters in filenames(according to Windows)
                if len(video_modules) > 1 or tmpname != "Video":
                    filenames.append(tmpname)
                else : #If only one video in this section && the video's name is Video, use section name as filename instead
                    tmpname=re.sub('[\\/:"*?<>|]+','',html_decode(fileweeks[iw][1][i]).replace(': ','-')).strip()
                    filenames.append(tmpname)
                if video_m[1]=="":
                   video_sources=video_m[2].split(",")
                   video_urls.append(html_decode(video_sources[0]).replace('"',''))
                   sub_urls.append("")
                else:   
                    sub_urls.append(BASE_URL + video_m[3] + "en" + "?videoId=" + video_m[1]) 
                    if args.use_cdn:    
                        page_video_urls = re_video_urls.findall(video_m[4])                                                     
                        if len(page_video_urls) != 0:                                                                           
                            video_urls.extend(page_video_urls)                                                                  
                        else:                                                                                                   
                            video_urls.append(video_m[1])
                        #print(page_video_urls)                                                                                 
                    else:                                                                                                       
                        video_urls.append(video_m[1])                                                                           
                        #print(video_m[1])                                                                                      
                                                                                                                            
            #print("[debug] Found %s cdn videos" % len(page_video_urls))                                                    
            i = i + 1                                                                                                       
               
            # Try to download some extra videos which is referred by iframe
            extra_ids = extra_youtube.findall(page)
            video_urls += [link[:YOUTUBE_VIDEO_ID_LENGTH] for link in
                         extra_ids]
            sub_urls += ['' for e_id in extra_ids]

        if len(video_urls) > 0:
            wfilenames.append(filenames)
            wvideo_urls.append(video_urls)
            wsub_urls.append(sub_urls)
            wfolders.append(weeks[iw][0])
            NoOfVideo += len(video_urls)

    if NoOfVideo > 0:                                                             
        print("[info] Output directory: " + args.output_dir)
        if is_interactive and (not args.use_cdn):
            # Get Available Video formats
            os.system('youtube-dl -F %s' % video_urls[-1])
            print('Choose a valid format or a set of valid format codes e.g. 22/17/...')
            args.format = input('Choose Format code: ')
        for i, videos in enumerate(wvideo_urls):
            #create direcotry                                                                       
            wtarget_dir = os.path.join(target_dir,                                                  
                          directory_name(wfolders[i].replace(': ','-')).strip())                    
            if not os.path.exists(wtarget_dir):                                                     
                os.makedirs(wtarget_dir)                                                            
            if args.use_cdn:                                                                        
                download_cdn_videos(wfilenames[i],wsub_urls[i],videos, wtarget_dir)             
            else:                                                                                   
                download_youtube_videos(wfilenames[i],wsub_urls[i],videos, wtarget_dir)                       
    else:
        print('WARNING: No downloadable video found.')
        sys.exit(0)
    #video_urls = ['http://youtube.com/watch?v=' + v_id
                  #for v_id in video_urls]

def download_youtube_video(video_id, file_path):
    cmd = ["youtube-dl",                                                                                                       
           "-o", file_path]   
    if args.format:                                                                                                            
        cmd.append("-f")                                                                                                       
        # defaults to mp4 in case the requested format isn't available                                                         
        cmd.append(args.format + '/mp4')                                                                                       
    if args.subtitles:                                                                                                         
        cmd.append('--write-sub')                                                                                              
    cmd.append(str(video_id))                                                                                                         
    try:                                                                                                                       
        popen_youtube = Popen(cmd, stdout=PIPE, stderr=PIPE)                                                                   
    except OSError:                                                                                                            
        print("[warning] youtube-dl not installed, video:%s couldn't be downloaed" %video_id)                                         
        return                                                                                                               
    youtube_stdout = b''                                                                                                       
    while True:  # Save output to youtube_stdout while this being echoed                                                       
        tmp = popen_youtube.stdout.read(1)                                                                                     
        youtube_stdout += tmp                                                                                                  
        print(tmp, end="")                                                                                                     
        sys.stdout.flush()                                                                                                     
        # do it until the process finish and there isn't output                                                                
        if tmp == b"" and popen_youtube.poll() is not None:                                                                    
            break                                                                                                              
                                                                                                                               
def download_youtube_videos (filenames,sub_urls,video_urls, target_dir):
    # Download Videos
    c = 0
    for v, s in zip(video_urls, sub_urls):
        c += 1
        filename_prefix = str(c).zfill(2)
        video_filename = filename_prefix + "-" + filenames[c-1] + '.mp4'
        video_path = os.path.join(target_dir, video_filename)
        download_youtube_video(v,video_path) 

        if args.subtitles:
            sub_filename = filename_prefix + filenames[c-1] + '.srt'
            sub_path = os.path.join(target_dir, sub_filename)

            if not os.path.exists(sub_path):
                subs_string = edx_get_subtitle(s, headers)
                if subs_string:
                    print('[info] Writing edX subtitles: %s' % sub_path)
                    open(os.path.join(os.getcwd(), sub_path),
                         'wb+').write(subs_string.encode('utf-8'))


def get_filename(target_dir, filename_prefix):
    """ returns the basename for the corresponding filename_prefix """
    # this whole function is not the nicest thing, but isolating it makes
    # things clearer , a good refactoring would be to get
    # the info from the video_url or the current output, to avoid the
    # iteration from the current dir
    filenames = os.listdir(target_dir)
    subs_filename = filename_prefix
    for name in filenames:  # Find the filename of the downloaded video
        if name.startswith(filename_prefix):
            (basename, ext) = os.path.splitext(name)
            return basename

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCTRL-C detected, shutting down....")
        sys.exit(0)
