# PACER-Updates
## Description
A python script that uses PACER Case Locator API access to search for new cases in a specific district, then email interested parties. Designed to save time and energy for reporters.
## Setup (Local)
1. Clone the repo: `git clone https://github.com/mhayes2772/PACER-Updates.git
2. Rename `config_template.ini` to `config.ini`
3. Add necessary info to `config.ini`
	- `script_email`: gmail address
	- `email_pswd`: gmail application password
		- You will need to setup an application password for the gmail account
	- `court_id`: The id corresponding to the specific court
		- Download the [Pacer Case Locator API User Guide](https://pacer.uscourts.gov/help/pacer/pacer-case-locator-pcl-api-user-guide)
		- Find the list of court id's on page 60
	- `court_tz`: The time zone of the court
		- US/Pacific
		- US/Central
		- US/Eastern
	- `email_recipient`: The email address that will receive the update email
		- Can be a comma separated list of addresses
	- `pclusr`: Username of the PACER Case Locator account
	- `pclpswd`: Password of the PACER Case Locator account
4. Run the script: `py pacer.py daily` or `py pacer.py weekly`
	- Daily will search for new cases in the current and last business day
	- Weekly will search for cases in the last 5 business
5. Use OS scheduler application such as Windows Task Scheduler or LaunchControl to run the script at a set time each day/week/etc.

## Setup (AWS Lambda)
1. Create a lambda function
2. Upload `pacer_package.zip`
    - If you modify `pacer.py`, you will need to recreate `pacer_package.zip`
3. Create an S3 Bucket to hold `history.csv`
4. Add environmental variables for:
	- `script_email`: Gmail address
	- `email_pswd`: gmail application password
		- You will need to setup an application password for the gmail account
	- `court_id`: The id corresponding to the specific court
		- Download the [Pacer Case Locator API User Guide](https://pacer.uscourts.gov/help/pacer/pacer-case-locator-pcl-api-user-guide)
		- Find the list of court id's on page 60
	- `court_tz`: The time zone of the court
		- US/Pacific
		- US/Central
		- US/Eastern
	- `email_recipient`: The email address that will receive the update email
		- Can be a comma separated list of addresses
	- `pclusr`: Username of the PACER Case Locator account
	- `pclpswd`: Password of the PACER Case Locator account
	- `history_bucket`: Name of the S3 bucket `history.csv` is in
5. Create trigger with EventBridge (CloudWatch Events)