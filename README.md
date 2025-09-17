# PACER Updates Tool

A Python based tool that uses [PACER Case Locator API](https://pacer.uscourts.gov/help/pacer/pacer-case-locator-pcl-api-user-guide) to automatically search for new federal cases in a specificized district and email interested parties. Designed to save time and effort for reporters, researchers and legal professionals. Can either be run locally or in AWS Lambda.
## Example
___

![[example_email.png]]
## Requirements
___
- Python 3.9+
- PACER Case Locator account credentials
- Gmail account with [App Passwords Enabled](https://support.google.com/mail/answer/185833?hl=en)
- (Optional) AWS account with permissions to create Lambda, S3, and EventBridge resources 
## Setup (Local)
___
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
___
1. Create an S3 Bucket to hold `history.csv`
2. Create an IAM Role for your pacer function
3. Attach the AWSLambdaBasicExecution policy
	- This policy allows the function to write to CloudWatch for logging purposes
4. Create and attach a policy giving the function read/write access to the S3 Bucket created in step 1
	- Will need `s3:PutObject` and `s3:GetObject`
5. Create a Lambda function
6. Select Python for Runtime
7. For execution role, select "Use an existing role" and select the role you created
8. Upload `pacer_package.zip` by selecting upload from .zip file
    - If you modify `pacer.py`, you will need to recreate `pacer_package.zip`
9. Add environmental variables for:
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
10. Create trigger with EventBridge (CloudWatch Events)
	- Use cron expression for scheduling
	- `cron(0 13 ? * MON-FRI *)` would execute Mon-Fri at 13:00 UTC
11. Modify the EventBridge rule to input a JSON Constant:
	- `{"mode":"daily"}` or `{"mode":"weekly"`
	- You will need to go to EventBridge in AWS to edit the rule
## License
___
MIT License. See [LICENSE](./LICENSE) for details.