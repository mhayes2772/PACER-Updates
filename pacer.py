import requests, datetime, csv, smtplib, sys, re, os, configparser
from email.message import EmailMessage

#Input: Command line args -> 0 for Daily, 1 for Weekly
# def parse_args(args):
#     if len(args) == 1:
#         print("Usage: py pacer.py [daily, weekly]")
#         sys.exit()
#     elif sys.argv[1] == "daily":
#         return 0
#     elif sys.argv[1] == "weekly":
#         return 1
#     else:
#         print("Usage: py pacer.py [daily, weekly]")
#         sys.exit()

#Input: Reads config file values into dictionary
def read_config():
    config = configparser.ConfigParser()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    config.read(path)

    config_values = {
        'script_email': config.get('General', 'script_email'),
        'email_pswd': config.get('General', 'email_pswd'),
        'auth_url': config.get('General', 'auth_url'),
        'pclapiurl': config.get('General', 'pclapiurl'),
        'court_id': config.get('General', 'court_id'),
        'email_recipient': config.get('User', 'email_recipient'),
        'pclusr': config.get('User', 'pclusr'),
        'pclpswd': config.get('User', 'pclpswd'),
    }
    return config_values

#Input: History path -> Reads history csv into an array
def read_history(path):
    content = []
    with open(path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            content.append(row)
    return content

#Input: CSV path, cases and history -> Writes new cases into history
def add_to_history(path, cases, history):
    with open(path, "a", newline='') as f:
        writer = csv.writer(f)
        for case in cases:
            if case not in history:
                writer.writerow(case)

#Input: History path -> Writes sorted history to path with cases older than two weeks removed
def clean_history(path):
    sortedHistory = []
    with open(path, "r", newline='') as infile:
        reader = csv.reader(infile)
        two_weeks = (datetime.datetime.now() - datetime.timedelta(days=14))

        sortedHistory = sorted(reader, key=lambda case:case[2], reverse=True)
        for case in sortedHistory[:]:
            date = datetime.datetime.strptime(case[2], "%Y-%m-%d")
            if date < two_weeks:
                sortedHistory.remove(case)
    
    with open(path, "w", newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(sortedHistory)

#Input: Array with searched cases and history -> Returns a dict of new cases and # of new cases
def find_new_cases(cases, history):
    total = 0
    new_cases = {"U.S. Criminal and Civil Cases":[], "Other Cases": []}

    pattern = re.compile(
        r'\b(?:USA|U\.?S\.?A\.?|United\s+States(?:\s+of\s+America)?)\b\s*v\.?\s*\b', 
        re.IGNORECASE
    )

    for case in cases:
        if case not in history:
            if pattern.search(case[1]):
                new_cases["U.S. Criminal and Civil Cases"].append(case)
            else:
                new_cases["Other Cases"].append(case)
            total += 1
    return new_cases, total

#Input: PACER Username & Password -> Returns an API authentication token
def authenticate(username, password, url):
    my_headers = {"Content-Type":"application/json", "Accept":"application/json"}
    my_body = {"loginId":username, "password":password}
    
    x = requests.post(f"https://{url}/services/cso-auth", 
        json = my_body, headers = my_headers)

    if int(x.json()['loginResult']):
        print("Login failed")
        print(x.json()['errorDescription'])
        sys.exit()

    return x.json()['nextGenCSO']

#Input: PACER API authentication token -> Invalidates the token 
def logout(token, url):
    my_headers = {"Content-Type":"application/json", "Accept":"application/json"}
    my_body = {"nextGenCSO":token}
    x = requests.post(f"https://{url}/services/cso-logout", json = my_body, headers = my_headers)

    if int(x.json()['loginResult']):
        print("An error occured on logout")
        print(x.json()['errorDescription'])
        sys.exit()

#Input: Mode (Daily or Weekly) -> dates to be used for the search
def get_dates(mode):
    toDate = datetime.datetime.now()
    #Special Search (Testing)
    if not mode:
        #Daily Search
        if toDate.strftime("%a") == "Mon":
            fromDate = (datetime.datetime.now() - datetime.timedelta(days = 4))
        else:
            fromDate = (datetime.datetime.now() - datetime.timedelta(days = 2))
    else:
        #Weekly search
        fromDate = (datetime.datetime.now() - datetime.timedelta(days = 7))

    return fromDate.strftime("%Y-%m-%d"), toDate.strftime("%Y-%m-%d")

#Input: EmailMessage Object -> Sends email
def send_email(email, sender, pswd):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(sender, pswd)

    s.send_message(email)

#Input: List of cases from search, list of cases from history -> Creates email message with new cases
def create_email(new_cases, total, cost, sender, reciever, mode):
    date = datetime.datetime.now().strftime("%m/%d/%Y")
    time = datetime.datetime.now().strftime("%I:%M %p")
    message_lines = [f"Hello,\nSince the last search, there are {total} new cases in PACER"]

    for key in new_cases:
        message_lines.append(f"\n   {key}")
        message_lines.append("  ------------------------------------------")
        for case in new_cases[key]:
            message_lines.append(f"  {case[1]}")
            message_lines.append(f"  {case[2]}")
            message_lines.append(f"  Case Type: {case[4]}")
            message_lines.append(f"  {case[0]}")
            message_lines.append(f"  {case[3]}\n")

    message_lines.append(f"Search conducted at {time} on {date}.")
    message_lines.append("This search cost ${cost:.2f}.".format(cost = round(cost, 2)))
    final_email = "\n".join(message_lines)

    message = EmailMessage()

    #Weekly
    if(mode):
        week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%m/%d/%Y")
        message["Subject"] = f"PACER Updates Week Of {week_ago}"
    #Daily
    else:
        message["Subject"] = f"PACER Updates {date}"
        
    message["From"] = sender
    message["To"] = reciever
    message.set_content(final_email, subtype='plain')

    return message

#Input: fromDate, toDate, API authentication token -> Returns all cases found in a list of lists    
def search(fromDate, toDate, token, url, court_id):
    cases = []
    page, total_pages, cost = 0, 1, 0
    my_headers = {"Content-Type":"application/json", "Accept":"application/json", "X-NEXT-GEN-CSO":token}
    my_body = {"dateFiledFrom":fromDate, "dateFiledTo":toDate, "courtId":[court_id]}
    sorting = "sort=jurisdictionType,ASC&sort=dateFiled,DESC"

    while page < total_pages:
        x = requests.post(f"https://{url}/pcl-public-api/rest/cases/find?page={page}&{sorting}", 
            json = my_body, headers = my_headers)
        if not x.ok:
            print(f"API Request Error: {x.status_code}")
            sys.exit()

        cost += float(x.json()['receipt']['searchFee'])
        #TODO: Error handle the request
        total_pages = x.json()['pageInfo']['totalPages']
        for case in x.json()['content']:
            #Only add case if not terminated
            filed_date = datetime.datetime.strptime(case['dateFiled'], "%Y-%m-%d")
            if case.get('dateTermed'):
                term_date = datetime.datetime.strptime(case['dateTermed'], "%Y-%m-%d")
                if term_date >= filed_date:
                    continue
            cases.append([case['caseNumberFull'], case['caseTitle'], case['dateFiled'], case['caseLink'], case['jurisdictionType']])
        page += 1

    return cases, cost

if __name__=="__main__":
    mode = 1 if sys.argv[1] == "weekly" else 0
    
    #LAMBDA - Change to read from environment variables
    config = read_config()
    history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.csv")

    #Get authentication token from PACER
    token = authenticate(config['pclusr'], config['pclpswd'], config['auth_url'])

    #PACER immediate search
    fromDate, toDate = get_dates(mode)
    cases, cost = search(fromDate, toDate, token, config['pclapiurl'], config['court_id'])

    #Read history file into array for use
    history = read_history(history_path)

    #Find new cases by comparing current search and history
    new_cases, total = find_new_cases(cases, history)

    #Create and send the email
    email = create_email(new_cases, total, cost, config['script_email'], config['email_recipient'], mode)
    send_email(email, config['script_email'], config['email_pswd'])

    #Write any new cases into the history file and clean file
    add_to_history(history_path, cases, history)
    clean_history(history_path)

    #Invalidate the authentication token
    logout(token, config['auth_url'])
